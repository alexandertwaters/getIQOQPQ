# api/generate.py - Vercel Python serverless: generate IQ/OQ/PQ package
import os
import sys
import json
import tempfile
from pathlib import Path
from urllib.parse import urlparse, parse_qs

# Ensure project root is on path
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from http.server import BaseHTTPRequestHandler


def _parse_request(handler):
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    body = None
    if handler.command in ("POST", "PUT"):
        try:
            length = int(handler.headers.get("Content-Length", 0))
            if length:
                raw = handler.rfile.read(length).decode("utf-8")
                body = json.loads(raw) if raw.strip() else {}
        except (ValueError, json.JSONDecodeError):
            pass
    return {"method": handler.command, "query": {k: v[0] if len(v) == 1 else v for k, v in query.items()}, "body": body or {}}


def _send_json(handler, status, data):
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ARTIFACT_BUCKET = os.environ.get("ARTIFACT_BUCKET", "artifacts")


def _get_supabase():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _upload_file(supabase, bucket, path_in_bucket, local_path, content_type="application/json"):
    with open(local_path, "rb") as f:
        data = f.read()
    supabase.storage.from_(bucket).upload(path_in_bucket, data, {"content-type": content_type})


def _handle_post(payload):
    try:
        from engine.engine_core import run_vector
        from engine.render_engine import render_markdown
    except Exception as e:
        import traceback
        raise RuntimeError(f"Import failed: {e}\n{traceback.format_exc()}") from e

    required = [
        "equipmentId", "cohort", "type", "siteContext",
        "controlArchitecture", "hazards", "rulesetId", "hazcatVersion",
    ]
    for k in required:
        if k not in payload:
            return 400, {"error": f"Missing required field {k}"}

    vector = {
        "cohort": payload["cohort"],
        "type": payload["type"],
        "model": payload.get("equipmentId", ""),
        "siteContext": payload["siteContext"],
        "controlArchitecture": payload["controlArchitecture"],
        "rulesetId": payload["rulesetId"],
        "hazcatVersion": payload["hazcatVersion"],
        "hazards": payload["hazards"],
    }

    pkg = run_vector(vector)
    fingerprint = pkg["fingerprint"]
    safe_name = fingerprint.replace(":", "_")

    tmpdir = tempfile.mkdtemp()
    pkg_path = Path(tmpdir) / f"{safe_name}.json"
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2)

    template_md = _PROJECT_ROOT / "templates" / "human_readable_template_markdown_v1.md"
    langmap = _PROJECT_ROOT / "rules" / "hazard_to_language_map_v1.json"
    rendered_dir = Path(tmpdir) / "rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    render_markdown(str(pkg_path), str(template_md), str(langmap), str(rendered_dir))

    base_path = safe_name
    supabase = _get_supabase()
    if supabase and ARTIFACT_BUCKET:
        _upload_file(
            supabase, ARTIFACT_BUCKET,
            f"{base_path}/{safe_name}.json", str(pkg_path),
            content_type="application/json"
        )
        for f in rendered_dir.iterdir():
            ctype = (
                "text/markdown" if f.suffix == ".md"
                else "text/csv" if f.suffix == ".csv"
                else "application/octet-stream"
            )
            _upload_file(supabase, ARTIFACT_BUCKET, f"{base_path}/{f.name}", str(f), content_type=ctype)

        try:
            supabase.table("packages").upsert({
                "fingerprint": fingerprint,
                "package_json": pkg,
                "artifact_path": f"{base_path}/",
                "ruleset_id": pkg.get("rulesetId"),
                "hazcat_version": pkg.get("hazcatVersion"),
                "qualification_band": pkg.get("qualificationBand"),
            }, on_conflict="fingerprint").execute()
        except Exception as e:
            print("DB upsert error", str(e))

    return 200, {
        "fingerprint": fingerprint,
        "artifactPath": f"{base_path}/",
        "artifactBucket": ARTIFACT_BUCKET,
    }


class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        req = _parse_request(self)
        if req["method"] != "POST":
            _send_json(self, 405, {"error": "Method not allowed"})
            return
        try:
            status, data = _handle_post(req["body"] or {})
            _send_json(self, status, data)
        except Exception as e:
            import traceback
            _send_json(self, 500, {"error": str(e), "traceback": traceback.format_exc()})
