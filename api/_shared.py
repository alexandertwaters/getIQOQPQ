# api/_shared.py - Shared helpers for Vercel Python handlers
import json
from urllib.parse import urlparse, parse_qs


def parse_request(handler):
    """Parse BaseHTTPRequestHandler into method, path, query, body."""
    parsed = urlparse(handler.path)
    query = parse_qs(parsed.query)
    body = None
    if handler.command == "POST" or handler.command == "PUT":
        try:
            length = int(handler.headers.get("Content-Length", 0))
            if length:
                raw = handler.rfile.read(length).decode("utf-8")
                body = json.loads(raw) if raw.strip() else {}
        except (ValueError, json.JSONDecodeError):
            pass
    return {
        "method": handler.command,
        "path": parsed.path,
        "query": {k: v[0] if len(v) == 1 else v for k, v in query.items()},
        "body": body or {},
    }


def send_json(handler, status, data):
    """Send JSON response."""
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json")
    handler.end_headers()
    handler.wfile.write(json.dumps(data).encode("utf-8"))
