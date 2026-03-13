# api/v1/requirements_library.py - GET /api/v1/requirements-library?kind=urs|frs|trs&equipmentTypeId=...
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


_KIND_TO_FILE = {
    "urs": ("data/urs_library_v1.json", "requirements"),
    "frs": ("data/frs_library_v1.json", "functions"),
    "trs": ("data/trs_library_v1.json", "tests"),
}


def _load_doc(path):
    p = Path(path)
    if not p.exists():
        return {}
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(kind=None, equipment_type_id=None):
    k = (kind or "").strip().lower()
    if k not in _KIND_TO_FILE:
        return 400, {"error": "kind must be one of: urs, frs, trs"}
    file_path, key = _KIND_TO_FILE[k]
    doc = _load_doc(file_path)
    rows = doc.get(key, [])
    if equipment_type_id:
        rows = [r for r in rows if r.get("equipmentTypeId") == equipment_type_id]
    return 200, {"version": doc.get("version", ""), key: rows}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        kind = req["query"].get("kind")
        eid = req["query"].get("equipmentTypeId")
        status, data = _handle_get(kind, eid)
        send_json(self, status, data)
