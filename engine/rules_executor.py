# engine/rules_executor.py
import json
import os
import re


def _eval_condition(cond_str, hazard, pkg):
    """Evaluate simple condition string. Supports:
    - hazard.ruleId startsWith 'prefix'
    - qualificationBand in ['A','B',...]
    - and / or
    """
    cond = (cond_str or "").strip()
    if not cond:
        return False
    parts = re.split(r"\s+and\s+", cond, flags=re.IGNORECASE)
    for part in parts:
        part = part.strip()
        # hazard.ruleId startsWith 'R_STER_PV'
        m = re.match(r"hazard\.ruleId\s+startsWith\s+['\"]([^'\"]*)['\"]", part, re.IGNORECASE)
        if m:
            prefix = m.group(1)
            if not (hazard.get("ruleId") or "").upper().startswith(prefix.upper()):
                return False
            continue
        # qualificationBand in ['Targeted','Full']
        m = re.match(r"qualificationBand\s+in\s+\[(.*)\]", part, re.IGNORECASE)
        if m:
            items = re.findall(r"['\"]([^'\"]*)['\"]", m.group(1))
            band = pkg.get("qualificationBand", "")
            if band not in items:
                return False
            continue
    return True


def _load_ruleset(ruleset_path):
    if not os.path.isabs(ruleset_path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        ruleset_path = os.path.join(base, ruleset_path)
    with open(ruleset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_ruleset_path(ruleset_id):
    """Map rulesetId to data file path."""
    id_to_file = {
        "ruleset_v1.1": "data/ruleset_v1.1_equipment_type_mappings - comprehensive.json",
    }
    return id_to_file.get(ruleset_id, f"data/{ruleset_id}_equipment_type_mappings.json")


def _item_to_title(item):
    """Normalize ruleset IQ/OQ/PQ item to string (for dedup and downstream). Accepts str or dict with title."""
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        return item.get("title") or item.get("id") or str(item)
    return str(item)


def _normalize_list(lst):
    """Convert list of strings or dicts to list of unique title strings."""
    seen = set()
    out = []
    for item in lst:
        title = _item_to_title(item)
        if title and title not in seen:
            seen.add(title)
            out.append(title)
    return out


def _merge_list(existing, new_items):
    """Merge new items into existing, normalizing both. Returns list of unique title strings."""
    combined = _normalize_list(existing) + _normalize_list(new_items)
    return list(dict.fromkeys(combined))


def apply_iqoqpq_mapping(pkg, ruleset_path=None):
    """Apply ruleset mapping rules to populate hazard IQ_list, OQ_list, PQ_list and package IQ, OQ, PQ."""
    path = ruleset_path or _resolve_ruleset_path(pkg.get("rulesetId", ""))
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    full_path = path if os.path.isabs(path) else os.path.join(base, path)
    if not os.path.exists(full_path):
        _set_default_iqoqpq(pkg)
        return
    ruleset = _load_ruleset(path)
    mapping_rules = [
        r for r in ruleset.get("rules", [])
        if "logic" in r and any(
            isinstance(logic, dict) and "if" in logic and "then" in logic
            for logic in r["logic"]
        )
    ]
    for hazard in pkg["hazards"]:
        hazard.setdefault("IQ_list", [])
        hazard.setdefault("OQ_list", [])
        hazard.setdefault("PQ_list", [])
        for rule in mapping_rules:
            for logic in rule.get("logic", []):
                if not isinstance(logic, dict) or "if" not in logic or "then" not in logic:
                    continue
                if _eval_condition(logic["if"], hazard, pkg):
                    then = logic["then"]
                    if "IQ" in then:
                        hazard["IQ_list"] = _merge_list(hazard["IQ_list"], then["IQ"])
                    if "OQ" in then:
                        hazard["OQ_list"] = _merge_list(hazard["OQ_list"], then["OQ"])
                    if "PQ" in then:
                        hazard["PQ_list"] = _merge_list(hazard["PQ_list"], then["PQ"])

        # Context escalation: add extra IQ/OQ/PQ when hazard context indicates elevated risk
        # (e.g., tortuous pathway, lumened devices, mixed loads) per FDA QSMR / ISO 14971
        if hazard.get("qualificationDepthEscalation") and pkg.get("qualificationBand") in ("Targeted", "Full"):
            rid = (hazard.get("ruleId") or "").upper()
            if rid.startswith("R_STER_PV") or rid.startswith("R_STER_GRAV"):
                hazard["OQ_list"] = _merge_list(hazard["OQ_list"], [
                    "Thermocouple mapping at lumen/worst-case geometry locations",
                    "BI placement validation at challenging pathway sites",
                ])
                hazard["PQ_list"] = _merge_list(hazard["PQ_list"], [
                    "Extended PQ cycles for worst-case load configurations including lumened/tortuous items",
                    "BI at lumen interior and challenging pathway locations",
                ])

    iq_checklist = []
    pq_items = []
    for h in pkg["hazards"]:
        iq_checklist.extend(h.get("IQ_list", []))
        pq_items.extend(h.get("PQ_list", []))
    iq_checklist = list(dict.fromkeys(iq_checklist))
    pq_items = list(dict.fromkeys(pq_items))

    pkg["IQ"] = {
        "checklist": iq_checklist if iq_checklist else ["Installation verification per supplier drawing"]
    }
    pkg["OQ"] = {"tests": []}
    pkg["PQ"] = {
        "plan": "; ".join(pq_items) if pq_items else "Default PQ plan",
        "pqCycles": 3,
        "worstCaseLoadDefinition": "",
        "biologicalIndicatorPlacement": "",
        "acceptanceCriteria": "",
    }


def _set_default_iqoqpq(pkg):
    pkg["IQ"] = {"checklist": ["Installation verification per supplier drawing"]}
    pkg["OQ"] = {"tests": []}
    pkg["PQ"] = {"plan": "Default PQ plan", "pqCycles": 3, "worstCaseLoadDefinition": "", "biologicalIndicatorPlacement": "", "acceptanceCriteria": ""}
    for h in pkg["hazards"]:
        h.setdefault("IQ_list", [])
        h.setdefault("OQ_list", [])
        h.setdefault("PQ_list", [])


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
