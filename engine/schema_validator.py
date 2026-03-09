# engine/schema_validator.py
import json
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
    print(f"Basic schema validation passed for {path}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python engine/schema_validator.py <input_json>")
        sys.exit(2)
    try:
        basic_validate_input_schema(sys.argv[1])
    except Exception as e:
        print("Schema validation error:", str(e))
        sys.exit(3)
