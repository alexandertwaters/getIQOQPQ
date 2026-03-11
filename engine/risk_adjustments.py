# engine/risk_adjustments.py
"""Apply control and hazard context adjustments to risk parameters per risk_linkage_rules."""

import json
import os


_LINKAGE_CACHE = None

_LINKAGE_PATH = "data/risk_linkage_rules_v1.json"


def _load_linkage():
    global _LINKAGE_CACHE
    if _LINKAGE_CACHE is not None:
        return _LINKAGE_CACHE
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, _LINKAGE_PATH) if not os.path.isabs(_LINKAGE_PATH) else _LINKAGE_PATH
    if not os.path.exists(path):
        _LINKAGE_CACHE = {"controlAdjustments": [], "hazardContextAdjustments": []}
        return _LINKAGE_CACHE
    with open(path, "r", encoding="utf-8") as f:
        _LINKAGE_CACHE = json.load(f)
    return _LINKAGE_CACHE


def _applies_to_hazard(rule, hazard_id, rule_id):
    """Check if rule applies to this hazard."""
    prefix_list = rule.get("appliesToRulePrefixes", [])
    id_list = rule.get("appliesToHazardIds", [])
    if id_list and hazard_id in id_list:
        return True
    if prefix_list and rule_id:
        rid = (rule_id or "").upper()
        for prefix in prefix_list:
            if rid.startswith((prefix or "").upper()):
                return True
    return False


def _control_matches(ctrl_val, when_value):
    """Check if control value matches rule's whenValue."""
    if when_value is True:
        return ctrl_val is True
    if when_value is False:
        return ctrl_val is False
    return ctrl_val == when_value


def _context_matches(hazard_context, context_id, context_value=None, context_value_in=None):
    """Check if hazard context matches rule."""
    val = hazard_context.get(context_id)
    if val is None:
        return False
    if context_value is not None:
        return val == context_value
    if context_value_in is not None:
        if isinstance(val, list):
            return any(v in context_value_in for v in val)
        return val in context_value_in
    return False


def _clamp(val, lo=0.0, hi=1.0):
    return max(lo, min(hi, float(val)))


def apply_linkage_adjustments(numeric, hazard, pkg):
    """
    Apply control and hazard context adjustments to risk numeric values.
    Returns adjusted numeric dict (P, D, C, S may be modified; RawRisk, AdjustedRisk, ResidualRisk recomputed).
    """
    linkage = _load_linkage()
    hazard_id = hazard.get("hazardId", "")
    rule_id = hazard.get("ruleId", "")
    equipment_controls = pkg.get("equipmentControls") or {}
    hazard_context = hazard.get("hazardContext") or {}

    p = numeric.get("ProbabilityOfOccurrence", 0.0)
    d = numeric.get("Detectability", 0.0)
    c = numeric.get("ControlEffectiveness", 0.0)
    s = numeric.get("Severity", 0.0)
    e = numeric.get("Exposure", 0.0)

    qual_depth_escalation = False

    # Control adjustments
    for rule in linkage.get("controlAdjustments", []):
        if not _applies_to_hazard(rule, hazard_id, rule_id):
            continue
        ctrl_id = rule.get("controlId")
        when_val = rule.get("whenValue")
        ctrl_val = equipment_controls.get(ctrl_id)
        if not _control_matches(ctrl_val, when_val):
            continue
        adj = rule.get("adjustment", {})
        p += adj.get("ProbabilityOfOccurrence_delta", 0.0)
        d += adj.get("Detectability_delta", 0.0)
        c += adj.get("ControlEffectiveness_delta", 0.0)
        s += adj.get("Severity_delta", 0.0)

    # Hazard context adjustments
    for rule in linkage.get("hazardContextAdjustments", []):
        if not _applies_to_hazard(rule, hazard_id, rule_id):
            continue
        ctx_id = rule.get("contextId")
        ctx_val = rule.get("contextValue")
        ctx_val_in = rule.get("contextValueIn")
        if not _context_matches(hazard_context, ctx_id, ctx_val, ctx_val_in):
            continue
        adj = rule.get("adjustment", {})
        p += adj.get("ProbabilityOfOccurrence_delta", 0.0)
        d += adj.get("Detectability_delta", 0.0)
        c += adj.get("ControlEffectiveness_delta", 0.0)
        s += adj.get("Severity_delta", 0.0)
        if rule.get("qualificationDepthEscalation"):
            qual_depth_escalation = True

    p = _clamp(p)
    d = _clamp(d)
    c = _clamp(c)
    s = _clamp(s)

    raw = s * p
    adjusted = raw * e * (1 - d)
    residual = adjusted * c

    out = {
        "Severity": s,
        "ProbabilityOfOccurrence": p,
        "Exposure": e,
        "Detectability": d,
        "ControlEffectiveness": c,
        "RawRisk": raw,
        "AdjustedRisk": adjusted,
        "ResidualRisk": residual,
    }
    if qual_depth_escalation:
        out["_qualificationDepthEscalation"] = True
    return out
