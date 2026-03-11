# engine/fingerprint.py
"""
Canonical fingerprint of package for reproducible hashing.
Excludes freeform text (title, definition, help/example) to avoid churn from copy edits.
ruleId included: affects IQ/OQ/PQ mapping; changes imply ruleset bump.
standards excluded: catalog metadata; hazcatVersion covers versioning.
"""
import json
import hashlib
from collections import OrderedDict

NUMERIC_PRECISION = 12

# Keys included in per-hazard canonical form. Excludes: title, definition,
# severityOptions, probabilityOptions, exposureOptions, detectabilityOptions,
# controlEffectivenessOptions, quickDefaults, standards (freeform/help text).
CANONICAL_HAZARD_KEYS = [
    "hazardId",
    "contextualTags",      # populated from contextualTags_selected
    "Severity",
    "ProbabilityOfOccurrence",
    "Exposure",
    "Detectability",
    "ControlEffectiveness",
    "RawRisk",
    "AdjustedRisk",
    "ResidualRisk",
    "EscalatedResidualRiskForMapping",
    "ruleId",
]

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
    ec = pkg.get("equipmentControls") or {}
    canonical["equipmentControls"] = json.dumps(sorted(ec.items()), separators=(',', ':')) if ec else ""

    hazards = sorted(pkg["hazards"], key=lambda h: h["hazardId"])
    canonical_hazards = []
    for h in hazards:
        tags = h.get("contextualTags_selected")
        if tags is None:
            tags = h.get("contextualTags", [])
        ch = OrderedDict()
        ch["hazardId"] = h["hazardId"]
        ch["contextualTags"] = sorted(tags)
        hc = h.get("hazardContext") or {}
        hc_items = [(k, tuple(sorted(v)) if isinstance(v, list) else v) for k, v in sorted(hc.items())]
        ch["hazardContext"] = json.dumps(hc_items, separators=(',', ':')) if hc_items else ""
        ch["Severity"] = format_num(h["Severity"])
        ch["ProbabilityOfOccurrence"] = format_num(h["ProbabilityOfOccurrence"])
        ch["Exposure"] = format_num(h["Exposure"])
        ch["Detectability"] = format_num(h["Detectability"])
        ch["ControlEffectiveness"] = format_num(h["ControlEffectiveness"])
        ch["RawRisk"] = format_num(h["RawRisk"])
        ch["AdjustedRisk"] = format_num(h["AdjustedRisk"])
        ch["ResidualRisk"] = format_num(h["ResidualRisk"])
        ch["EscalatedResidualRiskForMapping"] = format_num(
            h.get("EscalatedResidualRiskForMapping", h["ResidualRisk"])
        )
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
