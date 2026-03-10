# engine/engine_core.py
import json
import os
import sys
try:
    from .calculator import compute_hazard_numeric_from_labels
    from .rules_executor import apply_policy_escalations, compute_residual_risk_index_and_band, apply_iqoqpq_mapping
    from .fingerprint import canonicalize_package_for_fingerprint
except ImportError:
    from calculator import compute_hazard_numeric_from_labels
    from rules_executor import apply_policy_escalations, compute_residual_risk_index_and_band, apply_iqoqpq_mapping
    from fingerprint import canonicalize_package_for_fingerprint

def run_vector(vector):
    pkg = {}
    pkg["equipment"] = {"cohort": vector["cohort"], "type": vector["type"], "model": vector.get("model", "")}
    pkg["siteContext"] = vector["siteContext"]
    pkg["controlArchitecture"] = vector["controlArchitecture"]
    pkg["rulesetId"] = vector["rulesetId"]
    pkg["hazcatVersion"] = vector["hazcatVersion"]
    pkg["packageTemplateVersion"] = "v1.0"
    pkg["hazards"] = []

    for h in vector["hazards"]:
        hazard_labels = {
            "Severity_label": h.get("Severity_label") or h.get("Severity"),
            "ProbabilityOfOccurrence_label": h.get("ProbabilityOfOccurrence_label") or h.get("ProbabilityOfOccurrence"),
            "Exposure_label": h.get("Exposure_label") or h.get("Exposure"),
            "Detectability_label": h.get("Detectability_label") or h.get("Detectability"),
            "ControlEffectiveness_label": h.get("ControlEffectiveness_label") or h.get("ControlEffectiveness")
        }
        numeric = compute_hazard_numeric_from_labels(hazard_labels)
        hazard_entry = {
            "hazardId": h["hazardId"],
            "title": h.get("title", ""),
            "definition": h.get("definition", ""),
            "contextualTags": h.get("contextualTags", []),
            "Severity_label": hazard_labels["Severity_label"],
            "ProbabilityOfOccurrence_label": hazard_labels["ProbabilityOfOccurrence_label"],
            "Exposure_label": hazard_labels["Exposure_label"],
            "Detectability_label": hazard_labels["Detectability_label"],
            "ControlEffectiveness_label": hazard_labels["ControlEffectiveness_label"],
            "Severity": numeric["Severity"],
            "ProbabilityOfOccurrence": numeric["ProbabilityOfOccurrence"],
            "Exposure": numeric["Exposure"],
            "Detectability": numeric["Detectability"],
            "ControlEffectiveness": numeric["ControlEffectiveness"],
            "RawRisk": numeric["RawRisk"],
            "AdjustedRisk": numeric["AdjustedRisk"],
            "ResidualRisk": numeric["ResidualRisk"],
            "ruleId": h.get("ruleId", "")
        }
        pkg["hazards"].append(hazard_entry)

    apply_policy_escalations(pkg)
    compute_residual_risk_index_and_band(pkg)

    fingerprint = canonicalize_package_for_fingerprint(pkg)
    pkg["fingerprint"] = fingerprint

    apply_iqoqpq_mapping(pkg)
    pkg["csvGuidance"] = []
    pkg["evidenceList"] = []
    pkg["traceability"] = {"hazardRules": [h.get("ruleId","") for h in pkg["hazards"]]}
    pkg["recommendation"] = "See qualification band mapping."

    return pkg

def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["dryrun"], required=True)
    parser.add_argument("--vectors", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    with open(args.vectors, 'r', encoding='utf8') as f:
        vectors_doc = json.load(f)

    os.makedirs(args.output, exist_ok=True)
    results = []
    for v in vectors_doc["vectors"]:
        pkg = run_vector(v["input"])
        fp = pkg["fingerprint"]
        outdir = os.path.join(args.output, fp.replace(":", "_"))
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, f"{fp}.json"), 'w', encoding='utf8') as of:
            json.dump(pkg, of, indent=2)
        results.append({"id": v["id"], "fingerprint": fp, "qualificationBand": pkg["qualificationBand"]})

    with open(os.path.join(args.output, "run_summary.json"), 'w', encoding='utf8') as s:
        json.dump(results, s, indent=2)

    print("Dry run complete. Artifacts in", args.output)

if __name__ == "__main__":
    main()
