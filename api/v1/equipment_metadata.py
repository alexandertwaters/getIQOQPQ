# api/v1/equipment_metadata.py - GET /api/v1/equipment-metadata or ?equipmentTypeId=...
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import parse_request, send_json


def _load_metadata():
    path = Path("data/equipment_metadata.json")
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _handle_get(equipment_type_id=None):
    meta = _load_metadata()
    utilities_master = meta.get("utilitiesMasterList", {})
    equipment_list = meta.get("equipmentMetadata", [])

    if equipment_type_id:
        for em in equipment_list:
            if em.get("equipmentTypeId") == equipment_type_id:
                return 200, {
                    "utilitiesMasterList": utilities_master,
                    "equipmentMetadata": em,
                }
        return 404, {"error": f"equipmentTypeId not found: {equipment_type_id}"}

    return 200, {
        "utilitiesMasterList": utilities_master,
        "equipmentMetadata": equipment_list,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        req = parse_request(self)
        eid = req["query"].get("equipmentTypeId")
        status, data = _handle_get(eid)
        send_json(self, status, data)
