# api/generate.py
# Vercel Python serverless function to generate package, store artifacts in Supabase, and return fingerprint.
import os
import json
import tempfile
from pathlib import Path
from supabase import create_client
from datetime import datetime
from engine.engine_core import run_vector
from engine.render_engine import render_markdown

# Environment variables expected
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ARTIFACT_BUCKET = os.environ.get("ARTIFACT_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def upload_file_to_bucket(bucket, path_in_bucket, local_path, content_type="application/json"):
    with open(local_path, "rb") as f:
        data = f.read()
    res = supabase.storage.from_(bucket).upload(path_in_bucket, data, {"content-type": content_type})
    if res.get("error"):
        raise RuntimeError(f"Supabase upload error: {res['error']}")
    return res

def handler(request):
    try:
        payload = request.json()
    except Exception:
        return {"statusCode":400, "body": json.dumps({"error":"Invalid JSON payload"})}

    # Basic validation: required top-level fields
    required = ["equipmentId","cohort","type","siteContext","controlArchitecture","hazards","rulesetId","hazcatVersion"]
    for k in required:
        if k not in payload:
            return {"statusCode":400, "body": json.dumps({"error":f"Missing required field {k}"})}

    # Build vector wrapper expected by run_vector
    vector = {
        "cohort": payload["cohort"],
        "type": payload["type"],
        "model": payload.get("equipmentId",""),
        "siteContext": payload["siteContext"],
        "controlArchitecture": payload["controlArchitecture"],
        "rulesetId": payload["rulesetId"],
        "hazcatVersion": payload["hazcatVersion"],
        "hazards": payload["hazards"]
    }

    # Run engine to compute package
    pkg = run_vector(vector)
    fingerprint = pkg["fingerprint"]
    safe_folder = fingerprint.replace(":", "_")
    tmpdir = tempfile.mkdtemp()
    pkg_path = Path(tmpdir) / f"{fingerprint}.json"
    with open(pkg_path, "w", encoding="utf-8") as f:
        json.dump(pkg, f, indent=2)

    # Render markdown and CSV locally using render_engine
    rendered_dir = Path(tmpdir) / "rendered"
    rendered_dir.mkdir(parents=True, exist_ok=True)
    # Use the provided template and language map paths relative to repo root
    template_md = Path("templates") / "human_readable_template_markdown_v1.md"
    langmap = Path("rules") / "hazard_to_language_map_v1.json"
    render_markdown(str(pkg_path), str(template_md), str(langmap), str(rendered_dir))

    # Upload JSON, MD, CSV to Supabase storage under ARTIFACT_BUCKET/<fingerprint>/
    bucket = ARTIFACT_BUCKET
    base_path = f"{safe_folder}"
    # Upload package JSON
    upload_file_to_bucket(bucket, f"{base_path}/{pkg_path.name}", str(pkg_path), content_type="application/json")
    # Upload rendered files
    for f in rendered_dir.iterdir():
        ctype = "text/markdown" if f.suffix == ".md" else "text/csv" if f.suffix == ".csv" else "application/octet-stream"
        upload_file_to_bucket(bucket, f"{base_path}/{f.name}", str(f), content_type=ctype)

    # Insert metadata row into packages table
    try:
        supabase.table("packages").upsert({
            "fingerprint": fingerprint,
            "package_json": pkg,
            "artifact_path": f"{base_path}/",
            "created_by": "api",
            "created_at": datetime.utcnow().isoformat(),
            "rulesetId": pkg.get("rulesetId"),
            "hazcatVersion": pkg.get("hazcatVersion")
        }).execute()
    except Exception as e:
        # Nonfatal for artifact availability but log
        print("DB upsert error", str(e))

    # Return fingerprint and artifact path
    return {
        "statusCode": 200,
        "body": json.dumps({
            "fingerprint": fingerprint,
            "artifactPath": f"{base_path}/",
            "artifactBucket": bucket
        })
    }
