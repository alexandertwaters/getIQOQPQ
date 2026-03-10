# engine/calculator.py
NUM_MAP = {
    "Severity": {"Catastrophic":1.0,"Major":0.8,"Moderate":0.5,"Minor":0.2,"Negligible":0.0},
    "ProbabilityOfOccurrence": {"Frequent":0.8,"Occasional":0.5,"Remote":0.2,"Extremely remote":0.05},
    "Exposure": {"Continuous":1.0,"Frequent":0.6,"Intermittent":0.3,"Rare":0.05},
    "Detectability": {"High detectability":0.9,"Moderate detectability":0.6,"Low detectability":0.3,"None":0.0},
    "ControlEffectiveness": {"Very effective":0.2,"Effective":0.4,"Partially effective":0.7,"Ineffective":1.0}
}

def _lookup(key, val, map_key):
    """Resolve value: if numeric use as-is, else look up label in NUM_MAP."""
    if isinstance(val, (int, float)) and not isinstance(val, bool):
        return float(val)
    return NUM_MAP[map_key].get(val, 0.0)


def compute_hazard_numeric_from_labels(hazard_labels):
    s_label = hazard_labels.get("Severity_label") or hazard_labels.get("Severity")
    p_label = hazard_labels.get("ProbabilityOfOccurrence_label") or hazard_labels.get("ProbabilityOfOccurrence")
    e_label = hazard_labels.get("Exposure_label") or hazard_labels.get("Exposure")
    d_label = hazard_labels.get("Detectability_label") or hazard_labels.get("Detectability")
    c_label = hazard_labels.get("ControlEffectiveness_label") or hazard_labels.get("ControlEffectiveness")

    s = _lookup("Severity_label", s_label, "Severity")
    p = _lookup("ProbabilityOfOccurrence_label", p_label, "ProbabilityOfOccurrence")
    e = _lookup("Exposure_label", e_label, "Exposure")
    d = _lookup("Detectability_label", d_label, "Detectability")
    c = _lookup("ControlEffectiveness_label", c_label, "ControlEffectiveness")

    raw = s * p
    adjusted = raw * e * (1 - d)
    residual = adjusted * c

    return {
        "Severity": s,
        "ProbabilityOfOccurrence": p,
        "Exposure": e,
        "Detectability": d,
        "ControlEffectiveness": c,
        "RawRisk": raw,
        "AdjustedRisk": adjusted,
        "ResidualRisk": residual
    }
