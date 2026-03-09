# api/artifact.py
# Vercel Python serverless function to return signed URLs for artifact files stored in Supabase
import os
import json
from supabase import create_client
from urllib.parse import unquote

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
ARTIFACT_BUCKET = os.environ.get("ARTIFACT_BUCKET")

supabase = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE_KEY)

def handler(request):
    # Expect path param fingerprint or query param fingerprint
    fingerprint = request.args.get("fingerprint") if hasattr(request, "args") else None
    if not fingerprint:
        # Try JSON body
        try:
            body = request.json()
            fingerprint = body.get("fingerprint")
        except Exception:
            fingerprint = None
    if not fingerprint:
        return {"statusCode":400, "body": json.dumps({"error":"fingerprint required"})}

    safe_folder = fingerprint.replace(":", "_")
    prefix = f"{safe_folder}/"

    # List objects under prefix
    res = supabase.storage.from_(ARTIFACT_BUCKET).list(prefix)
    if res.get("error"):
        return {"statusCode":500, "body": json.dumps({"error": res["error"]})}

    files = res.get("data", [])
    signed_urls = {}
    for entry in files:
        path = entry.get("name")
        # generate signed URL valid for 1 hour
        signed = supabase.storage.from_(ARTIFACT_BUCKET).create_signed_url(path, 3600)
        if signed.get("error"):
            signed_urls[path] = {"error": signed["error"]}
        else:
            signed_urls[path] = signed.get("signedURL")

    return {"statusCode":200, "body": json.dumps({"files": signed_urls})}