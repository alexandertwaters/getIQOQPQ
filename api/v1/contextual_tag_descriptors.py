# api/v1/contextual_tag_descriptors.py - GET /api/v1/contextual-tag-descriptors
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import send_json


def _handle_get():
    path = Path("data/contextual_tag_descriptors.json")
    if not path.exists():
        return 200, {"tags": {}}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return 200, {"tags": data.get("tags", {})}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, data = _handle_get()
        send_json(self, status, data)
