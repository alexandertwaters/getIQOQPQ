# ci/human_draft_tests.py
import os
import sys
import json
import argparse
from pathlib import Path

def find_markdown_for_fingerprint(artifacts_dir, fingerprint):
    """Find rendered MD: artifacts_dir/{fp}.md (fp may have : or _) or artifacts_dir/{fp}/*.md."""
    base = Path(artifacts_dir)
    safe_fp = fingerprint.replace(":", "_")
    for fn in [f"{safe_fp}.md", f"{fingerprint}.md"]:
        if (base / fn).exists():
            return base / fn
    fp_dir = base / safe_fp
    if fp_dir.exists():
        md_files = list(fp_dir.glob("*.md"))
        return md_files[0] if md_files else None
    return None

def check_markdown_contains_required_sections(md_path):
    text = md_path.read_text(encoding='utf8')
    required = [
        "Qualification band",
        "Residual Risk Index",
        "Validation Master Plan (VMP)",
        "User Requirements Specification (URS)",
        "Design Qualification (DQ)",
        "Installation Qualification (IQ)",
        "Operational Qualification (OQ)",
        "Performance Qualification (PQ)",
        "Requalification plan",
        "Traceability matrix",
    ]
    missing = [r for r in required if r not in text]
    return missing

def check_markdown_contains_help_or_example(md_path):
    text = md_path.read_text(encoding='utf8')
    return "Objective" in text and "Acceptance" in text

def check_perhazard_csv(artifacts_dir, fingerprint):
    base = Path(artifacts_dir)
    safe_fp = fingerprint.replace(":", "_")
    csvs = list(base.glob(f"{safe_fp}.perHazard.csv"))
    if not csvs:
        csvs = list((base / safe_fp).glob("*.perHazard.csv"))
    return bool(csvs)

def check_package_metadata(pkg):
    """Validate hazards contain definition, ruleId, standards (keys present)."""
    hazards = pkg.get("hazards", [])
    if not hazards:
        return None
    for h in hazards:
        if "definition" not in h or "ruleId" not in h or "standards" not in h:
            return f"hazard {h.get('hazardId')} missing definition/ruleId/standards"
    return None

def run(artifacts_dir, vectors_path):
    vectors = json.load(open(vectors_path, 'r', encoding='utf8'))["vectors"]
    artifacts_path = Path(artifacts_dir).resolve()
    dryrun_root = artifacts_path.parent if artifacts_path.name == "rendered" else artifacts_path
    rendered_dir = str(artifacts_path) if artifacts_path.name == "rendered" else str(artifacts_path / "rendered")

    run_summary_path = dryrun_root / "run_summary.json"
    if not run_summary_path.exists():
        print("Human draft tests failed: run_summary.json not found")
        sys.exit(2)
    summary = json.load(open(run_summary_path, 'r', encoding='utf8'))
    vid_to_fp = {s["id"]: s["fingerprint"] for s in summary}

    failures = []
    for v in vectors:
        vid = v["id"]
        fp = vid_to_fp.get(vid)
        if not fp:
            failures.append({"id": vid, "error": "no fingerprint in run_summary"})
            continue
        safe_fp = fp.replace(":", "_")
        pkg_path = dryrun_root / safe_fp / f"{safe_fp}.json"
        if not pkg_path.exists():
            failures.append({"id": vid, "error": "no package json found"})
            continue
        doc = json.load(open(pkg_path, 'r', encoding='utf8'))
        md = find_markdown_for_fingerprint(rendered_dir, fp)
        if not md:
            failures.append({"id": vid, "fingerprint": fp, "error": "no rendered markdown found"})
            continue
        missing_sections = check_markdown_contains_required_sections(md)
        if missing_sections:
            failures.append({"id": vid, "fingerprint": fp, "missing_sections": missing_sections})
        elif not check_markdown_contains_help_or_example(md):
            failures.append({"id": vid, "fingerprint": fp, "error": "markdown missing script objective/acceptance structure"})
        elif not check_perhazard_csv(rendered_dir, fp):
            failures.append({"id": vid, "fingerprint": fp, "error": "missing perHazard CSV"})
        else:
            meta_err = check_package_metadata(doc)
            if meta_err:
                failures.append({"id": vid, "fingerprint": fp, "error": f"metadata: {meta_err}"})
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
