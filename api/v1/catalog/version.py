# api/v1/catalog/version.py - GET /api/v1/catalog/version
# CWD is project root per Vercel
import json
from pathlib import Path
from http.server import BaseHTTPRequestHandler

from api._shared import send_json


def _handle_get():
    hazcat_path = Path("data/hazcat_v1.1_equipment_types - comprehensive.json")
    ruleset_path = Path("data/ruleset_v1.1_equipment_type_mappings - comprehensive.json")
    hazcat_version = "hazcat_v1.1"
    ruleset_id = "ruleset_v1.1"
    if hazcat_path.exists():
        with open(hazcat_path, "r", encoding="utf-8") as f:
            hazcat_version = json.load(f).get("hazcatVersion", hazcat_version)
    if ruleset_path.exists():
        with open(ruleset_path, "r", encoding="utf-8") as f:
            ruleset_id = json.load(f).get("rulesetId", ruleset_id)
    return 200, {
        "hazcatVersion": hazcat_version,
        "rulesetId": ruleset_id,
    }


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        status, data = _handle_get()
        send_json(self, status, data)
