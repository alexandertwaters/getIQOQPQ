# engine/calculator.py
NUM_MAP = {
    "Severity": {"Catastrophic":1.0,"Major":0.8,"Moderate":0.5,"Minor":0.2,"Negligible":0.0},
    "ProbabilityOfOccurrence": {"Frequent":0.8,"Occasional":0.5,"Remote":0.2,"Extremely remote":0.05},
    "Exposure": {"Continuous":1.0,"Frequent":0.6,"Intermittent":0.3,"Rare":0.05},
    "Detectability": {"High detectability":0.9,"Moderate detectability":0.6,"Low detectability":0.3,"None":0.0},
    "ControlEffectiveness": {"Very effective":0.2,"Effective":0.4,"Partially effective":0.7,"Ineffective":1.0}
}

def compute_hazard_numeric_from_labels(hazard_labels):
    s_label = hazard_labels["Severity_label"]
    p_label = hazard_labels["ProbabilityOfOccurrence_label"]
    e_label = hazard_labels["Exposure_label"]
    d_label = hazard_labels["Detectability_label"]
    c_label = hazard_labels["ControlEffectiveness_label"]

    s = NUM_MAP["Severity"][s_label]
    p = NUM_MAP["ProbabilityOfOccurrence"][p_label]
    e = NUM_MAP["Exposure"][e_label]
    d = NUM_MAP["Detectability"][d_label]
    c = NUM_MAP["ControlEffectiveness"][c_label]

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
