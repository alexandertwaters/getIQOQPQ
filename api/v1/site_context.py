# api/v1/site_context.py - GET /api/v1/site-context
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import send_json


def _handle_get():
    path = Path("data/site_context_metadata.json")
    if not path.exists():
        return 200, {
            "cleanroomClasses": [],
            "productContact": {},
            "productionThroughput": [],
        }
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return 200, {
        "cleanroomClasses": data.get("cleanroomClasses", []),
        "productContact": data.get("productContact", {}),
        "productionThroughput": data.get("productionThroughput", []),
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, data = _handle_get()
        send_json(self, status, data)
