# engine/fingerprint.py
import json
import hashlib
from collections import OrderedDict

NUMERIC_PRECISION = 12

def format_num(v):
    return f"{v:.{NUMERIC_PRECISION}f}"

def canonicalize_package_for_fingerprint(pkg):
    canonical = OrderedDict()
    canonical["equipment.cohort"] = pkg["equipment"]["cohort"]
    canonical["equipment.type"] = pkg["equipment"]["type"]
    sc = pkg["siteContext"]
    canonical["siteContext.cleanroomClass"] = sc["cleanroomClass"]
    canonical["siteContext.utilities"] = sorted(sc["utilities"])
    canonical["siteContext.productContact"] = bool(sc["productContact"])
    canonical["siteContext.productionThroughput"] = sc["productionThroughput"]
    canonical["controlArchitecture"] = pkg["controlArchitecture"]

    hazards = sorted(pkg["hazards"], key=lambda h: h["hazardId"])
    canonical_hazards = []
    for h in hazards:
        ch = OrderedDict()
        ch["hazardId"] = h["hazardId"]
        ch["title"] = h.get("title", "")
        ch["contextualTags"] = sorted(h.get("contextualTags", []))
        ch["Severity"] = format_num(h["Severity"])
        ch["ProbabilityOfOccurrence"] = format_num(h["ProbabilityOfOccurrence"])
        ch["Exposure"] = format_num(h["Exposure"])
        ch["Detectability"] = format_num(h["Detectability"])
        ch["ControlEffectiveness"] = format_num(h["ControlEffectiveness"])
        ch["RawRisk"] = format_num(h["RawRisk"])
        ch["AdjustedRisk"] = format_num(h["AdjustedRisk"])
        ch["ResidualRisk"] = format_num(h["ResidualRisk"])
        if "EscalatedResidualRiskForMapping" in h:
            ch["EscalatedResidualRiskForMapping"] = format_num(h["EscalatedResidualRiskForMapping"])
        ch["ruleId"] = h.get("ruleId", "")
        canonical_hazards.append(ch)
    canonical["hazards"] = canonical_hazards

    canonical["ResidualRiskIndex"] = format_num(pkg["ResidualRiskIndex"])
    canonical["qualificationBand"] = pkg["qualificationBand"]
    canonical["rulesetId"] = pkg["rulesetId"]
    canonical["hazcatVersion"] = pkg["hazcatVersion"]
    canonical["packageTemplateVersion"] = pkg.get("packageTemplateVersion", "v1.0")

    serialized = json.dumps(canonical, separators=(',', ':'), ensure_ascii=False)
    digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    return f"sha256:{digest}"
