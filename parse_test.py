import json
files = [
  "data/unit_test_vectors_v1.json",
  "data/hazcat_v1.1_equipment_types.json",
  "data/ruleset_v1.1_equipment_type_mappings.json"
]
for p in files:
    with open(p, "r", encoding="utf-8") as f:
        json.load(f)
print("OK: key JSON files parsed")