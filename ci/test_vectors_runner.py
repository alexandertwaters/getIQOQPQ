# ci/test_vectors_runner.py
# Compares actual vs expected fingerprints. Fingerprint excludes help/example/definition
# to avoid churn; metadata validation is in human_draft_tests.
import json
import sys
import argparse

def load_json(path):
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)

def run(actual_path, expected_path):
    actual = load_json(actual_path)
    expected_map = load_json(expected_path)
    mismatches = []
    for item in actual:
        vid = item.get("id")
        actual_fp = item.get("fingerprint")
        expected_fp = expected_map.get(vid)
        if expected_fp is None:
            mismatches.append({"id": vid, "error": "missing expected fingerprint"})
            continue
        if actual_fp != expected_fp:
            mismatches.append({"id": vid, "expected": expected_fp, "actual": actual_fp})
    if mismatches:
        print("Fingerprint mismatches or missing expected entries:")
        for m in mismatches:
            print(json.dumps(m, ensure_ascii=False))
        sys.exit(2)
    print("All fingerprints match expected.")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--actual", required=True)
    parser.add_argument("--expected", required=True)
    args = parser.parse_args()
    run(args.actual, args.expected)
