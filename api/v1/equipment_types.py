# api/v1/equipment_types.py - GET /api/v1/equipment-types (list cohorts and equipment types)
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import send_json


def _handle_get():
    wizard_path = Path("data/wizard_mapping_equipment_types.json")
    if not wizard_path.exists():
        return 200, {"cohorts": []}
    with open(wizard_path, "r", encoding="utf-8") as f:
        doc = json.load(f)
    return 200, {"cohorts": doc.get("cohorts", [])}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, data = _handle_get()
        send_json(self, status, data)
