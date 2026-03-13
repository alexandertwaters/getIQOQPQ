# api/v1/trs_library.py - GET /api/v1/trs-library?equipmentTypeId=...
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


def _load_doc():
    path = Path("data/trs_library_v1.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(equipment_type_id=None):
    doc = _load_doc()
    rows = doc.get("tests", [])
    if equipment_type_id:
        rows = [r for r in rows if r.get("equipmentTypeId") == equipment_type_id]
    return 200, {"version": doc.get("version", ""), "tests": rows}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        eid = req["query"].get("equipmentTypeId")
        status, data = _handle_get(eid)
        send_json(self, status, data)
