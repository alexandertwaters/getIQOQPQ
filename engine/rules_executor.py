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


def _load_iq_checklists():
    """Load IQ checklists from data/iq_checklists.json."""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    path = os.path.join(base, "data", "iq_checklists.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_ster_pv_iq_checklist(pkg, hmi_used_for_release):
    """Load STER_PV IQ checklist; filter conditional items (hmiUsedForRelease).
    Returns (descriptions_list, full_items_list, evidence_naming, evidence_help) or (None, None, None, None)."""
    doc = _load_iq_checklists()
    for et in doc.get("equipmentTypes", []):
        if et.get("equipmentTypeId") != "STER_PV_AUT":
            continue
        items = et.get("items", [])
        out_desc = []
        out_items = []
        cat_map = {c["categoryId"]: c.get("label", c["categoryId"]) for c in et.get("categories", [])}
        for item in items:
            cond = item.get("conditional")
            if cond == "hmiUsedForRelease" and not hmi_used_for_release:
                continue
            out_desc.append(item.get("description") or item.get("itemId", ""))
            out_items.append({
                "itemId": item.get("itemId", ""),
                "category": cat_map.get(item.get("categoryId", ""), item.get("categoryId", "")),
                "description": item.get("description", ""),
                "expected": item.get("expected", ""),
                "evidenceFileName": item.get("evidenceFileName", ""),
            })
        return (
            out_desc if out_desc else None,
            out_items if out_items else None,
            et.get("evidenceNamingConvention", ""),
            et.get("evidenceNamingHelp", ""),
        )
    return (None, None, None, None)


def _build_pq_worst_case_load(pkg):
    """Build worst-case load definition from hazard context. Per ISO 17665."""
    parts = []
    for h in pkg.get("hazards", []):
        ctx = h.get("hazardContext") or {}
        load_types = ctx.get("load_type")
        if isinstance(load_types, list) and load_types:
            labels = {
                "pouches": "pouches",
                "trays_wrapped": "wrapped trays",
                "trays_unwrapped": "unwrapped trays",
                "porous": "porous loads",
                "lumened": "lumened devices",
                "tubing_pathway": "challenging pathway items",
                "vials": "vials",
            }
            names = [labels.get(lt, lt) for lt in load_types if labels.get(lt)]
            if names:
                parts.append("load types: " + ", ".join(names))
        load_density = ctx.get("load_density")
        if load_density:
            parts.append(f"load density: {load_density}")
        load_config = ctx.get("load_config")
        if load_config == "mixed_loads":
            parts.append("mixed loads")
    if parts:
        return "; ".join(parts)
    return "Worst-case load per validated load configuration (see load mapping)."


def _build_pq_bi_placement(pkg, equipment_type_id):
    """Build biological indicator placement description. Per ISO 17665, ISO 11138."""
    if equipment_type_id not in ("STER_PV_AUT", "STER_GRAV_AUT"):
        return ""
    return (
        "Place BIs at worst-case locations identified in thermocouple mapping: "
        "inside trays, on tray surfaces, chamber extremities, and cold-spot locations. "
        "Typically 12 BIs per cycle; include positive and negative controls per ISO 11138."
    )


def _build_pq_acceptance_criteria(pkg, equipment_type_id):
    """Build PQ acceptance criteria. Per ISO 17665."""
    if equipment_type_id in ("STER_PV_AUT", "STER_GRAV_AUT"):
        return (
            "All BIs show no growth after incubation per BI manufacturer instructions; "
            "OQ parameters (temperature, pressure, dwell time) met for each PQ cycle."
        )
    return "Acceptance per validated protocol and applicable standards."


def _build_csv_guidance(hmi_used_for_release):
    """Build CSV/HMI verification guidance when HMI used for release (21 CFR Part 11)."""
    if not hmi_used_for_release:
        return []
    return [
        "When HMI cycle data is used for release decisions, 21 CFR Part 11 applies.",
        "Verify: audit trail enabled and tamper-evident; access control; backup and restore tested.",
        "Export integrity: verify CSV/printout matches source data; document checksums if applicable.",
        "Printout vs export: verify printed record matches electronic export for critical parameters.",
    ]


def _build_traceability_matrix(pkg):
    """Build traceability matrix: Hazard | Control | Test ID | Acceptance."""
    rows = []
    for h in pkg.get("hazards", []):
        hazard_id = h.get("hazardId", "")
        title = h.get("title", "")
        rule_id = h.get("ruleId", "")
        for tid in h.get("IQ_list", []) or []:
            rows.append({"hazardId": hazard_id, "hazardTitle": title, "testType": "IQ", "testId": tid, "ruleId": rule_id})
        for tid in h.get("OQ_list", []) or []:
            rows.append({"hazardId": hazard_id, "hazardTitle": title, "testType": "OQ", "testId": tid, "ruleId": rule_id})
        for tid in h.get("PQ_list", []) or []:
            rows.append({"hazardId": hazard_id, "hazardTitle": title, "testType": "PQ", "testId": tid, "ruleId": rule_id})
    return rows


def _build_evidence_list(pkg, hmi_used_for_release):
    """Build evidence list; include HMI/CSV evidence when applicable."""
    base = [
        "IQ checklist signed and dated",
        "OQ test scripts with results and acceptance",
        "PQ cycle logs and BI incubation results",
    ]
    if hmi_used_for_release:
        base.extend([
            "HMI/CSV qualification report (export, audit trail, backup/restore)",
            "Evidence naming: SITE_EQUIPID_TESTID_YYYYMMDD_HHMM.ext",
        ])
    return base


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

    # STER_PV: use equipment-type-specific IQ checklist from iq_checklists.json
    equipment_type_id = (pkg.get("equipment") or {}).get("equipmentTypeId", "")
    hmi_used_for_release = (
        (pkg.get("equipmentControls") or {}).get("CTRL_STER_PV_002b") is True
        or (pkg.get("siteContext") or {}).get("hmiUsedForRelease") is True
    )
    iq_items = []
    evidence_naming = ""
    evidence_naming_help = ""
    if equipment_type_id == "STER_PV_AUT":
        desc_list, full_items, ev_naming, ev_help = _load_ster_pv_iq_checklist(pkg, hmi_used_for_release)
        if desc_list:
            iq_checklist = desc_list
        if full_items:
            iq_items = full_items
        if ev_naming:
            evidence_naming = ev_naming
        if ev_help:
            evidence_naming_help = ev_help

    pkg["IQ"] = {
        "checklist": iq_checklist if iq_checklist else ["Installation verification per supplier drawing"],
        "checklistItems": iq_items if iq_items else [],
        "evidenceNamingConvention": evidence_naming,
        "evidenceNamingHelp": evidence_naming_help,
    }
    pkg["OQ"] = {"tests": []}
    pkg["PQ"] = {
        "plan": "; ".join(pq_items) if pq_items else "Default PQ plan",
        "pqCycles": 3,
        "worstCaseLoadDefinition": _build_pq_worst_case_load(pkg),
        "biologicalIndicatorPlacement": _build_pq_bi_placement(pkg, equipment_type_id),
        "acceptanceCriteria": _build_pq_acceptance_criteria(pkg, equipment_type_id),
    }

    # CSV guidance and evidence when HMI used for release (21 CFR Part 11)
    pkg["csvGuidance"] = _build_csv_guidance(hmi_used_for_release)
    pkg["evidenceList"] = _build_evidence_list(pkg, hmi_used_for_release)

    # Traceability matrix: Hazard | Control | IQ/OQ/PQ Test ID | Acceptance
    pkg["traceabilityMatrix"] = _build_traceability_matrix(pkg)


def _set_default_iqoqpq(pkg):
    pkg["IQ"] = {"checklist": ["Installation verification per supplier drawing"]}
    pkg["OQ"] = {"tests": []}
    pkg["PQ"] = {"plan": "Default PQ plan", "pqCycles": 3, "worstCaseLoadDefinition": "", "biologicalIndicatorPlacement": "", "acceptanceCriteria": ""}
    for h in pkg["hazards"]:
        h.setdefault("IQ_list", [])
        h.setdefault("OQ_list", [])
        h.setdefault("PQ_list", [])


def apply_policy_escalations(pkg):
    """Apply policy-based risk escalations per FDA QSR and ISO 14971.
    - productContact + Catastrophic (Severity 1.0) + STER: x10
    - HMI used for release + H_DATA_001: x2 (21 CFR Part 11 data integrity risk)
    """
    hmi_used_for_release = False
    equipment_controls = pkg.get("equipmentControls") or {}
    site_ctx = pkg.get("siteContext") or {}
    if equipment_controls.get("CTRL_STER_PV_002b") is True:
        hmi_used_for_release = True
    if site_ctx.get("hmiUsedForRelease") is True:
        hmi_used_for_release = True

    for h in pkg["hazards"]:
        severity = h.get("Severity", 0.0)
        product_contact = site_ctx.get("productContact", False)
        rule_id = h.get("ruleId", "").upper()
        hazard_id = h.get("hazardId", "").upper()

        base_risk = h["ResidualRisk"]
        multiplier = 1.0

        escalation_reasons = []
        if severity == 1.0 and product_contact and rule_id.startswith("R_STER"):
            multiplier *= 10.0
            escalation_reasons.append("Product contact + Catastrophic severity (×10)")
        if hazard_id == "H_DATA_001" and hmi_used_for_release:
            multiplier *= 2.0
            escalation_reasons.append("HMI used for release / 21 CFR Part 11 (×2)")

        h["EscalatedResidualRiskForMapping"] = base_risk * multiplier
        if escalation_reasons:
            h["escalationReason"] = "; ".join(escalation_reasons)

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
