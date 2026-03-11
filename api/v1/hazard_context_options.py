# api/v1/hazard_context_options.py - GET /api/v1/hazard-context-options?equipmentTypeId=... [&hazardId=...]
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


def _load_catalog():
    path = Path("data/hazard_context_options.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(equipment_type_id=None, hazard_id=None):
    catalog = _load_catalog()
    equipment_types = catalog.get("equipmentTypes", [])

    if not equipment_type_id:
        return 400, {"error": "equipmentTypeId required"}

    for et in equipment_types:
        if et.get("equipmentTypeId") != equipment_type_id:
            continue
        hazard_options = et.get("hazardContextOptions", [])
        if hazard_id:
            for ho in hazard_options:
                if ho.get("hazardId") == hazard_id:
                    return 200, {
                        "equipmentTypeId": equipment_type_id,
                        "hazardId": hazard_id,
                        "hazardContextOptions": ho.get("contextOptions", []),
                    }
            return 404, {"error": f"hazardId not found: {hazard_id}"}
        return 200, {
            "equipmentTypeId": equipment_type_id,
            "equipmentType": et.get("equipmentType", ""),
            "hazardContextOptions": hazard_options,
        }
    return 404, {"error": f"equipmentTypeId not found: {equipment_type_id}"}


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        eid = req["query"].get("equipmentTypeId")
        hid = req["query"].get("hazardId")
        status, data = _handle_get(eid, hid)
        send_json(self, status, data)
