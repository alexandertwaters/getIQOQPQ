# engine/rules_executor.py
def apply_policy_escalations(pkg):
    for h in pkg["hazards"]:
        severity = h.get("Severity", 0.0)
        product_contact = pkg["siteContext"].get("productContact", False)
        rule_id = h.get("ruleId", "").upper()
        if severity == 1.0 and product_contact and rule_id.startswith("R_STER"):
            h["EscalatedResidualRiskForMapping"] = h["ResidualRisk"] * 10.0
        else:
            h["EscalatedResidualRiskForMapping"] = h["ResidualRisk"]

def compute_residual_risk_index_and_band(pkg):
    vals = [h["EscalatedResidualRiskForMapping"] for h in pkg["hazards"]]
    maxv = max(vals) if vals else 0.0
    s = sum(vals)
    rri = maxv + 0.1 * s
    pkg["ResidualRiskIndex"] = rri
    if rri <= 0.15:
        pkg["qualificationBand"] = "Basic"
    elif rri <= 0.40:
        pkg["qualificationBand"] = "Targeted"
    else:
        pkg["qualificationBand"] = "Full"
