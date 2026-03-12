# engine/engine_core.py
import json
import os
import sys
try:
    from .calculator import compute_hazard_numeric_from_labels
    from .risk_adjustments import apply_linkage_adjustments
    from .rules_executor import apply_policy_escalations, compute_residual_risk_index_and_band, apply_iqoqpq_mapping
    from .fingerprint import canonicalize_package_for_fingerprint
except ImportError:
    from calculator import compute_hazard_numeric_from_labels
    from risk_adjustments import apply_linkage_adjustments
    from rules_executor import apply_policy_escalations, compute_residual_risk_index_and_band, apply_iqoqpq_mapping
    from fingerprint import canonicalize_package_for_fingerprint

_HAZCAT_CACHE = {}

_HAZCAT_VERSION_TO_FILE = {
    "hazcat_v1.1": "data/hazcat_v1.1_equipment_types - comprehensive.json",
}


def _load_hazcat(hazcat_version):
    """Load hazcat by version; resolve path and cache."""
    if hazcat_version in _HAZCAT_CACHE:
        return _HAZCAT_CACHE[hazcat_version]
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    filename = _HAZCAT_VERSION_TO_FILE.get(
        hazcat_version,
        f"{hazcat_version}_equipment_types.json",
    )
    path = os.path.join(base, filename) if not os.path.isabs(filename) else filename
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    _HAZCAT_CACHE[hazcat_version] = data
    return data

def _find_hazard_in_catalog(hazcat, hazard_id):
    """Find hazard metadata by hazardId across all equipment types."""
    for et in hazcat.get("equipmentTypes", []):
        for h in et.get("hazards", []):
            if h.get("hazardId") == hazard_id:
                return h
    return {}

def run_vector(vector):
    pkg = {}
    pkg["equipment"] = {
        "cohort": vector["cohort"],
        "type": vector["type"],
        "model": vector.get("model", ""),
        "equipmentTypeId": vector.get("equipmentTypeId", ""),
    }
    pkg["siteContext"] = vector["siteContext"]
    pkg["controlArchitecture"] = vector["controlArchitecture"]
    pkg["lifecycle"] = {
        "vmp": vector.get("vmp", {}) or {},
        "urs": vector.get("urs", {}) or {},
        "dq": vector.get("dq", {}) or {},
        "computerizedValidation": vector.get("computerizedValidation", {}) or {},
        "requalificationPlan": vector.get("requalificationPlan", {}) or {},
    }
    if vector.get("equipmentControls"):
        pkg["equipmentControls"] = vector["equipmentControls"]
    pkg["rulesetId"] = vector["rulesetId"]
    pkg["hazcatVersion"] = vector["hazcatVersion"]
    pkg["packageTemplateVersion"] = "v1.0"
    pkg["hazards"] = []

    hazcat = _load_hazcat(vector["hazcatVersion"])

    for h in vector["hazards"]:
        catalog = _find_hazard_in_catalog(hazcat, h["hazardId"])
        hazard_labels = {
            "Severity_label": h.get("Severity_label") or h.get("Severity"),
            "ProbabilityOfOccurrence_label": h.get("ProbabilityOfOccurrence_label") or h.get("ProbabilityOfOccurrence"),
            "Exposure_label": h.get("Exposure_label") or h.get("Exposure"),
            "Detectability_label": h.get("Detectability_label") or h.get("Detectability"),
            "ControlEffectiveness_label": h.get("ControlEffectiveness_label") or h.get("ControlEffectiveness")
        }
        numeric = compute_hazard_numeric_from_labels(hazard_labels)
        # Apply control and hazard context adjustments (per ISO 14971 / FDA QSMR)
        hazard_for_linkage = {
            "hazardId": h["hazardId"],
            "ruleId": catalog.get("ruleId") or h.get("ruleId"),
            "hazardContext": h.get("hazardContext") or {},
        }
        numeric = apply_linkage_adjustments(numeric, hazard_for_linkage, pkg)
        qual_depth_escalation = numeric.pop("_qualificationDepthEscalation", False)
        hazard_context = h.get("hazardContext", {})

        hazard_entry = {
            "hazardId": h["hazardId"],
            "title": catalog.get("title") or h.get("title", ""),
            "hazardContext": hazard_context if hazard_context else None,
            "qualificationDepthEscalation": qual_depth_escalation,
            "definition": catalog.get("definition") or h.get("definition", ""),
            "severityOptions": catalog.get("severityOptions", []),
            "probabilityOptions": catalog.get("probabilityOptions", []),
            "exposureOptions": catalog.get("exposureOptions", []),
            "detectabilityOptions": catalog.get("detectabilityOptions", []),
            "controlEffectivenessOptions": catalog.get("controlEffectivenessOptions", []),
            "quickDefaults": catalog.get("quickDefaults", {}),
            "ruleId": catalog.get("ruleId") or h.get("ruleId", ""),
            "standards": catalog.get("standards", []),
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
        }
        pkg["hazards"].append(hazard_entry)

    apply_policy_escalations(pkg)
    compute_residual_risk_index_and_band(pkg)

    fingerprint = canonicalize_package_for_fingerprint(pkg)
    pkg["fingerprint"] = fingerprint

    apply_iqoqpq_mapping(pkg)
    pkg.setdefault("csvGuidance", [])
    pkg.setdefault("evidenceList", [])
    pkg["traceability"] = {"hazardRules": [h.get("ruleId","") for h in pkg["hazards"]]}

    band = pkg.get("qualificationBand", "Basic")
    has_pq = any(h.get("PQ_list") for h in pkg["hazards"])
    if band == "Full" or (band == "Targeted" and has_pq):
        pkg["recommendation"] = "Conduct lifecycle package: URS, DQ, IQ, OQ, and PQ (or targeted PQ as applicable)."
    elif band == "Targeted":
        pkg["recommendation"] = "Conduct IQ, OQ, and targeted PQ."
    elif band == "Basic" and has_pq:
        pkg["recommendation"] = "Conduct IQ, OQ, and PQ as indicated in advisory tests below."
    elif band == "Basic":
        pkg["recommendation"] = "Conduct IQ and OQ."
    else:
        pkg["recommendation"] = "Conduct IQ and OQ."

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
        safe_fp = fp.replace(":", "_")
        outdir = os.path.join(args.output, safe_fp)
        os.makedirs(outdir, exist_ok=True)
        with open(os.path.join(outdir, f"{safe_fp}.json"), 'w', encoding='utf8') as of:
            json.dump(pkg, of, indent=2)
        results.append({"id": v["id"], "fingerprint": fp, "qualificationBand": pkg["qualificationBand"]})

    with open(os.path.join(args.output, "run_summary.json"), 'w', encoding='utf8') as s:
        json.dump(results, s, indent=2)

    print("Dry run complete. Artifacts in", args.output)

if __name__ == "__main__":
    main()
