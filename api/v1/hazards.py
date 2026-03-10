# api/v1/hazards.py - GET /api/v1/hazards?equipmentTypeId=...
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


def _load_hazcat():
    path = Path("data/hazcat_v1.1_equipment_types.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(equipment_type_id):
    hazcat = _load_hazcat()
    for et in hazcat.get("equipmentTypes", []):
        if et.get("equipmentTypeId") == equipment_type_id:
            return 200, {"hazards": et.get("hazards", []), "equipmentType": et.get("equipmentType", "")}
    return 404, {"error": f"equipmentTypeId not found: {equipment_type_id}"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        eid = req["query"].get("equipmentTypeId")
        status, data = _handle_get(eid) if eid else (400, {"error": "equipmentTypeId required"})
        send_json(self, status, data)
