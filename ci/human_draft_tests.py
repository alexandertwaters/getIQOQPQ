# ci/human_draft_tests.py
import os
import sys
import json
import argparse
from pathlib import Path

def find_markdown_for_fingerprint(artifacts_dir, fingerprint):
    fp_dir = Path(artifacts_dir) / fingerprint.replace(":", "_")
    if not fp_dir.exists():
        return None
    md_files = list(fp_dir.glob("*.md"))
    return md_files[0] if md_files else None

def check_markdown_contains_required_sections(md_path):
    text = md_path.read_text(encoding='utf8')
    required = ["Qualification band", "Residual Risk Index", "Installation Qualification", "Operational Qualification", "Performance Qualification", "Traceability appendix"]
    missing = [r for r in required if r not in text]
    return missing

def check_perhazard_csv(fp_dir):
    csvs = list(Path(fp_dir).glob("*.perHazard.csv"))
    return bool(csvs)

def run(artifacts_dir, vectors_path):
    vectors = json.load(open(vectors_path, 'r', encoding='utf8'))["vectors"]
    failures = []
    for v in vectors:
        vid = v["id"]
        found = False
        for root, dirs, files in os.walk(artifacts_dir):
            for fn in files:
                if fn.endswith(".json"):
                    try:
                        doc = json.load(open(os.path.join(root, fn), 'r', encoding='utf8'))
                    except Exception:
                        continue
                    if doc.get("fingerprint"):
                        fp = doc.get("fingerprint")
                        md = find_markdown_for_fingerprint(artifacts_dir, fp)
                        if md:
                            missing_sections = check_markdown_contains_required_sections(md)
                            if missing_sections:
                                failures.append({"id": vid, "fingerprint": fp, "missing_sections": missing_sections})
                            else:
                                fp_dir = Path(artifacts_dir) / fp.replace(":", "_")
                                if not check_perhazard_csv(fp_dir):
                                    failures.append({"id": vid, "fingerprint": fp, "error": "missing perHazard CSV"})
                            found = True
                            break
            if found:
                break
        if not found:
            failures.append({"id": vid, "error": "no rendered artifact found"})
    if failures:
        print("Human draft tests failed:")
        for f in failures:
            print(json.dumps(f, ensure_ascii=False))
        sys.exit(2)
    print("Human draft tests passed for all vectors.")
    sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--artifacts", required=True)
    parser.add_argument("--vectors", required=True)
    args = parser.parse_args()
    run(args.artifacts, args.vectors)
