# api/v1/equipment_controls.py - GET /api/v1/equipment-controls?equipmentTypeId=...
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


def _load_catalog():
    path = Path("data/equipment_controls_catalog.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(equipment_type_id=None):
    catalog = _load_catalog()
    equipment_types = catalog.get("equipmentTypes", [])

    if equipment_type_id:
        for et in equipment_types:
            if et.get("equipmentTypeId") == equipment_type_id:
                return 200, {
                    "equipmentTypeId": et.get("equipmentTypeId"),
                    "equipmentType": et.get("equipmentType", ""),
                    "cohort": et.get("cohort", ""),
                    "controlCategories": et.get("controlCategories", []),
                }
        return 404, {"error": f"equipmentTypeId not found: {equipment_type_id}"}

    return 200, {
        "equipmentTypes": [
            {"equipmentTypeId": et.get("equipmentTypeId"), "equipmentType": et.get("equipmentType"), "cohort": et.get("cohort")}
            for et in equipment_types
        ],
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        eid = req["query"].get("equipmentTypeId")
        status, data = _handle_get(eid)
        send_json(self, status, data)
