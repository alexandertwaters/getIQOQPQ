# engine/schema_validator.py
import json
import os
import sys

def validate_no_free_text(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            key_lower = k.lower()
            if key_lower in ("notes", "note", "free_text", "free-text", "free", "comments"):
                raise ValueError(f"Free text field detected at {path}.{k}")
            validate_no_free_text(v, path=f"{path}.{k}")
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            validate_no_free_text(item, path=f"{path}[{i}]")

def validate_hazcat(data, path):
    if "hazcatVersion" not in data:
        raise ValueError(f"Schema validation failed: missing 'hazcatVersion' in {path}")
    if "equipmentTypes" not in data or not isinstance(data["equipmentTypes"], list):
        raise ValueError(f"Schema validation failed: 'equipmentTypes' must be a non-empty array in {path}")
    validate_no_free_text(data)
    print(f"Hazcat schema validation passed for {path}")

def validate_ruleset(data, path):
    if "rulesetId" not in data:
        raise ValueError(f"Schema validation failed: missing 'rulesetId' in {path}")
    if "rules" not in data or not isinstance(data["rules"], list):
        raise ValueError(f"Schema validation failed: 'rules' must be an array in {path}")
    validate_no_free_text(data)
    print(f"Ruleset schema validation passed for {path}")

def validate_wizard_mapping(data, path):
    if "mappingVersion" not in data and "cohorts" not in data:
        raise ValueError(f"Schema validation failed: missing 'mappingVersion' or 'cohorts' in {path}")
    if "cohorts" not in data or not isinstance(data["cohorts"], list):
        raise ValueError(f"Schema validation failed: 'cohorts' must be an array in {path}")
    validate_no_free_text(data)
    print(f"Wizard mapping schema validation passed for {path}")

def validate_ui_wiring(data, path):
    if "uiSchemaVersion" not in data:
        raise ValueError(f"Schema validation failed: missing 'uiSchemaVersion' in {path}")
    for key in ("entryScreen", "reviewScreen"):
        if key not in data or not isinstance(data[key], dict):
            raise ValueError(f"Schema validation failed: '{key}' must be an object in {path}")
    if "entryScreen" in data and "fields" not in data["entryScreen"]:
        raise ValueError(f"Schema validation failed: entryScreen must have 'fields' in {path}")
    validate_no_free_text(data)
    print(f"UI wiring schema validation passed for {path}")

def basic_validate_input_schema(path):
    with open(path, 'r', encoding='utf8') as f:
        data = json.load(f)
    required_top = ["equipmentId", "cohort", "type", "siteContext", "controlArchitecture", "hazards", "rulesetId", "hazcatVersion"]
    for k in required_top:
        if k not in data:
            raise ValueError(f"Schema validation failed: missing required top-level field '{k}' in {path}")
    sc = data["siteContext"]
    for rk in ("cleanroomClass", "utilities", "productContact", "productionThroughput"):
        if rk not in sc:
            raise ValueError(f"Schema validation failed: missing siteContext field '{rk}' in {path}")
    if not isinstance(data["hazards"], list) or len(data["hazards"]) == 0:
        raise ValueError("Schema validation failed: 'hazards' must be a non-empty array")
    validate_no_free_text(data)
    print(f"Input schema validation passed for {path}")

def validate_canonical(path):
    basename = os.path.basename(path).lower()
    with open(path, 'r', encoding='utf8') as f:
        data = json.load(f)
    if "hazcat" in basename:
        validate_hazcat(data, path)
    elif "ruleset" in basename:
        validate_ruleset(data, path)
    elif "wizard_mapping" in basename:
        validate_wizard_mapping(data, path)
    elif "ui_wiring_schema" in basename:
        validate_ui_wiring(data, path)
    else:
        basic_validate_input_schema(path)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engine/schema_validator.py <input_json> [input_json...]")
        sys.exit(2)
    failed = False
    for path in sys.argv[1:]:
        try:
            validate_canonical(path)
        except Exception as e:
            print("Schema validation error:", str(e))
            failed = True
    if failed:
        sys.exit(3)
