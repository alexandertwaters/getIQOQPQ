# api/artifact.py - Vercel Python serverless: return signed URLs for artifacts
import os
import json
from http.server import BaseHTTPRequestHandler
from supabase import create_client

from api._shared import parse_request, send_json

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ARTIFACT_BUCKET = os.environ.get("ARTIFACT_BUCKET", "artifacts")


def _get_supabase():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)


def _extract_metadata(pkg):
    """Extract small metadata summary for API clients without downloading full JSON."""
    if not pkg:
        return None
    hazards = pkg.get("hazards", [])
    rule_ids = list(dict.fromkeys(h.get("ruleId", "") for h in hazards if h.get("ruleId")))
    standards = sorted(set(s for h in hazards for s in h.get("standards", [])))
    return {
        "rulesetId": pkg.get("rulesetId"),
        "hazcatVersion": pkg.get("hazcatVersion"),
        "qualificationBand": pkg.get("qualificationBand"),
        "ruleIds": rule_ids,
        "standards": standards,
    }


def _handle_get(fingerprint):
    if not fingerprint:
        return 400, {"error": "fingerprint required"}

    supabase = _get_supabase()
    if not supabase:
        return 503, {"error": "Storage not configured"}

    safe_folder = fingerprint.replace(":", "_")
    prefix = f"{safe_folder}/"

    metadata = None
    try:
        row = supabase.table("packages").select("package_json").eq("fingerprint", fingerprint).execute()
        if row.data and len(row.data) > 0:
            metadata = _extract_metadata(row.data[0].get("package_json"))
    except Exception:
        pass

    try:
        listing = supabase.storage.from_(ARTIFACT_BUCKET).list(prefix)
    except Exception as e:
        return 500, {"error": str(e)}

    files = listing if isinstance(listing, list) else listing.get("data", [])
    signed_urls = {}
    for entry in files:
        name = entry.get("name") if isinstance(entry, dict) else entry
        if not name:
            continue
        file_path = f"{prefix}{name}"
        try:
            result = supabase.storage.from_(ARTIFACT_BUCKET).create_signed_url(file_path, 3600)
            if isinstance(result, dict) and result.get("error"):
                signed_urls[name] = {"error": result["error"]}
            else:
                signed_urls[name] = result.get("signedUrl") or result.get("signedURL") or result
        except Exception as e:
            signed_urls[name] = {"error": str(e)}

    resp = {"files": signed_urls}
    if metadata:
        resp["metadata"] = metadata
    return 200, resp


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        fp = req["query"].get("fingerprint")
        status, data = _handle_get(fp)
        send_json(self, status, data)
