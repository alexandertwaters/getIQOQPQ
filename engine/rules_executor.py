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
    """Build traceability matrix with human-readable hazard title and test title (no codes)."""
    rows = []
    for h in pkg.get("hazards", []):
        hazard_title = h.get("title", "") or h.get("hazardId", "")
        for tid in h.get("URS_list", []) or []:
            rows.append({"hazardTitle": hazard_title, "testType": "URS", "testTitle": tid})
        for tid in h.get("DQ_list", []) or []:
            rows.append({"hazardTitle": hazard_title, "testType": "DQ", "testTitle": tid})
        for tid in h.get("IQ_list", []) or []:
            rows.append({"hazardTitle": hazard_title, "testType": "IQ", "testTitle": tid})
        for tid in h.get("OQ_list", []) or []:
            rows.append({"hazardTitle": hazard_title, "testType": "OQ", "testTitle": tid})
        for tid in h.get("PQ_list", []) or []:
            rows.append({"hazardTitle": hazard_title, "testType": "PQ", "testTitle": tid})
    return rows


def _build_evidence_list(pkg, hmi_used_for_release):
    """Build evidence list; include HMI/CSV evidence when applicable."""
    base = [
        "IQ checklist signed and dated",
        "OQ test scripts with results and acceptance",
        "PQ cycle logs and BI incubation results",
        "Training records for protocol executors and reviewers",
        "Supplier documentation and installation evidence",
    ]
    if hmi_used_for_release:
        base.extend([
            "HMI/CSV qualification report (export, audit trail, backup/restore)",
            "Evidence naming: SITE_EQUIPID_TESTID_YYYYMMDD_HHMM.ext",
        ])
    return base


def _build_requalification_plan(pkg):
    """Build requalification schedule tied to risk band and selected triggers."""
    lifecycle = pkg.get("lifecycle") or {}
    rq = lifecycle.get("requalificationPlan") or {}
    selected = rq.get("baseFrequency", "annual")
    band = pkg.get("qualificationBand", "Targeted")
    if selected == "risk_based":
        frequency = "Annual" if band in ("Targeted", "Full") else "Every 2 years"
    elif selected == "biennial" and band in ("Targeted", "Full"):
        frequency = "Annual (elevated by risk band)"
    elif selected == "biennial":
        frequency = "Every 2 years"
    else:
        frequency = "Annual"
    triggers = rq.get("triggers") or ["move", "major_repair", "process_change", "oot"]
    trigger_labels = {
        "move": "Relocation or move",
        "major_repair": "Major repair or maintenance affecting function",
        "process_change": "Process parameter or load pattern change",
        "oot": "Out-of-tolerance/deviation event",
        "software_change": "Software/configuration change",
    }
    return {
        "frequency": frequency,
        "triggers": [trigger_labels.get(t, t) for t in triggers],
        "rationale": rq.get("rationale", "") or "Risk-based requalification per VMP and process criticality.",
    }


def _load_json_file(path):
    if not os.path.isabs(path):
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        path = os.path.join(base, path)
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def apply_vmodel_mapping(pkg):
    """Resolve URS->FRS->TRS and derive IQ/OQ/PQ sections for pure V-model mode."""
    equipment_type_id = (pkg.get("equipment") or {}).get("equipmentTypeId", "")
    sel = (pkg.get("lifecycle") or {}).get("vmodel") or {}
    urs_ids = list(dict.fromkeys(sel.get("ursIds") or []))
    frs_ids = list(dict.fromkeys(sel.get("frsIds") or []))
    trs_ids = list(dict.fromkeys(sel.get("trsIds") or []))

    urs_doc = _load_json_file("data/urs_library_v1.json")
    frs_doc = _load_json_file("data/frs_library_v1.json")
    trs_doc = _load_json_file("data/trs_library_v1.json")
    map_doc = _load_json_file("data/requirements_traceability_map_v1.json")

    urs_rows = [r for r in urs_doc.get("requirements", []) if r.get("equipmentTypeId") == equipment_type_id]
    frs_rows = [r for r in frs_doc.get("functions", []) if r.get("equipmentTypeId") == equipment_type_id]
    trs_rows = [r for r in trs_doc.get("tests", []) if r.get("equipmentTypeId") == equipment_type_id]
    urs_map = {r.get("ursId"): r for r in urs_rows}
    frs_map = {r.get("frsId"): r for r in frs_rows}
    trs_map = {r.get("trsId"): r for r in trs_rows}

    if not urs_ids:
        urs_ids = [r.get("ursId") for r in urs_rows if r.get("criticality") == "critical"]
    if not frs_ids:
        frs_ids = [
            f.get("frsId")
            for f in frs_rows
            if any(u in urs_ids for u in (f.get("derivedFromURS") or []))
        ]
    if not trs_ids:
        trs_ids = [
            t.get("trsId")
            for t in trs_rows
            if any(f in frs_ids for f in (t.get("verifiesFRS") or []))
        ]

    selected_urs = [urs_map[u] for u in urs_ids if u in urs_map]
    selected_frs = [frs_map[f] for f in frs_ids if f in frs_map]
    selected_trs = [trs_map[t] for t in trs_ids if t in trs_map]

    # If caller supplied stale/unknown TRS IDs (e.g., legacy IDs from older UI),
    # recover by deriving TRS from selected FRS so IQ/OQ/PQ protocols are populated.
    if not selected_trs and selected_frs:
        derived_trs_ids = [
            t.get("trsId")
            for t in trs_rows
            if any(f.get("frsId") in (t.get("verifiesFRS") or []) for f in selected_frs)
        ]
        trs_ids = list(dict.fromkeys(derived_trs_ids))
        selected_trs = [trs_map[t] for t in trs_ids if t in trs_map]

    def _trs_phase(phase):
        return [t for t in selected_trs if (t.get("verificationPhase") or "").upper() == phase]

    iq_trs = _trs_phase("IQ")
    oq_trs = _trs_phase("OQ")
    pq_trs = _trs_phase("PQ")

    lifecycle = pkg.get("lifecycle") or {}
    vmp_in = lifecycle.get("vmp") or {}
    urs_in = lifecycle.get("urs") or {}
    pkg["VMP"] = {
        "scope": vmp_in.get("scope", ""),
        "objective": vmp_in.get("objective", ""),
        "roles": vmp_in.get("roles", ""),
        "qualificationStrategy": vmp_in.get("qualificationStrategy", ""),
        "timeline": vmp_in.get("timeline", ""),
        "deliverables": vmp_in.get("deliverables", ""),
        "trainingPlan": vmp_in.get("trainingPlan", ""),
        "supplierEvidencePlan": vmp_in.get("supplierEvidencePlan", ""),
    }

    frs_to_oq = {}
    frs_to_pq = {}
    for t in oq_trs:
        for fid in (t.get("verifiesFRS") or []):
            frs_to_oq.setdefault(fid, []).append(t)
    for t in pq_trs:
        for fid in (t.get("verifiesFRS") or []):
            frs_to_pq.setdefault(fid, []).append(t)

    def _is_ctq_from_urs_ids(ids):
        for uid in ids:
            u = urs_map.get(uid) or {}
            if (u.get("criticality") or "").lower() == "critical":
                return True
        return False

    urs_rows = []
    for u in selected_urs:
        uid = u.get("ursId", "")
        related_frs = [f for f in selected_frs if uid in (f.get("derivedFromURS") or [])]
        related_pq = []
        for f in related_frs:
            related_pq.extend(frs_to_pq.get(f.get("frsId", ""), []))
        related_pq = list({t.get("trsId", ""): t for t in related_pq if t.get("trsId")}.values())
        urs_rows.append({
            "itemId": uid,
            "requirement": u.get("statement") or u.get("title", ""),
            "rationale": u.get("rationale") or "Supports intended use, patient safety, and regulatory compliance.",
            "acceptanceCriteria": u.get("acceptanceCriteria") or ("; ".join([t.get("acceptanceCriteria", "") for t in related_pq if t.get("acceptanceCriteria")]) or "Defined in mapped PQ protocol."),
            "testMethod": "; ".join([f"{t.get('trsId', '')}: {t.get('title', '')}" for t in related_pq]) or "Mapped PQ protocol execution.",
            "ctq": "Yes" if (u.get("criticality") or "").lower() == "critical" else "No",
            "responsible": u.get("responsible") or "Validation / QA",
        })

    frs_rows = []
    for f in selected_frs:
        fid = f.get("frsId", "")
        oq_for_frs = frs_to_oq.get(fid, [])
        ctq = "Yes" if _is_ctq_from_urs_ids(f.get("derivedFromURS") or []) else "No"
        frs_rows.append({
            "itemId": fid,
            "requirement": f.get("functionalRequirement") or f.get("title", ""),
            "rationale": f.get("rationale") or "Defines required equipment behavior to satisfy URS.",
            "acceptanceCriteria": f.get("acceptanceCriteria") or ("; ".join([t.get("acceptanceCriteria", "") for t in oq_for_frs if t.get("acceptanceCriteria")]) or "Defined in mapped OQ protocol."),
            "testMethod": "; ".join([f"{t.get('trsId', '')}: {t.get('title', '')}" for t in oq_for_frs]) or "Mapped OQ protocol execution.",
            "ctq": ctq,
            "responsible": f.get("responsible") or "Validation / Engineering",
        })

    trs_rows = []
    for t in selected_trs:
        phase = (t.get("verificationPhase") or "").upper()
        ctq = "Yes" if _is_ctq_from_urs_ids([uid for f in selected_frs if f.get("frsId") in (t.get("verifiesFRS") or []) for uid in (f.get("derivedFromURS") or [])]) else "No"
        default_resp = "Engineering / Validation" if phase == "IQ" else ("Validation / Automation" if phase == "OQ" else "Validation / QA / Operations")
        trs_rows.append({
            "itemId": t.get("trsId", ""),
            "requirement": t.get("objective") or t.get("title", ""),
            "rationale": t.get("rationale") or "Provides executable verification of technical requirements.",
            "acceptanceCriteria": t.get("acceptanceCriteria", ""),
            "testMethod": f"{phase} protocol execution",
            "ctq": ctq,
            "responsible": t.get("responsible") or default_resp,
        })

    pkg["URS"] = {
        "intendedUse": urs_in.get("intendedUse", ""),
        "criticalProcessParameters": urs_in.get("criticalProcessParameters", ""),
        "environmentNeeds": urs_in.get("environmentNeeds", ""),
        "throughputRationale": urs_in.get("throughputRationale", ""),
        "acceptanceCriteria": urs_in.get("acceptanceCriteria", ""),
        "requirements": selected_urs,
        "tableRows": urs_rows,
    }
    pkg["FRS"] = {"functions": selected_frs, "tableRows": frs_rows}
    pkg["TRS"] = {"tests": selected_trs, "tableRows": trs_rows}
    pkg["IQ"] = {
        "purpose": "Verify installation, utilities, baseline configuration, and documented readiness for operation.",
        "prerequisites": "Approved IQ protocol, calibrated tools, installation complete, and required documentation available.",
        "executionNotes": "Execute in order, attach objective evidence, and manage deviations per QMS.",
        "checklist": [t.get("title", "") for t in iq_trs],
        "testScripts": [
            {
                "testId": t.get("trsId", ""),
                "title": t.get("title", ""),
                "objective": t.get("objective", ""),
                "setup": "Equipment installed and prerequisites complete.",
                "steps": "Execute protocol steps per approved method.",
                "dataToRecord": "Observed values, evidence references, and deviations.",
                "acceptanceCriteria": t.get("acceptanceCriteria", ""),
            }
            for t in iq_trs
        ],
    }
    pkg["OQ"] = {
        "purpose": "Verify functional operation across intended operating ranges, alarms, interlocks, and challenge conditions.",
        "prerequisites": "IQ complete, approved procedures available, and calibrated challenge instruments ready.",
        "executionNotes": "Document each run and challenge condition with objective evidence and pass/fail outcomes.",
        "tests": [
            {
                "testId": t.get("trsId", ""),
                "title": t.get("title", ""),
                "objective": t.get("objective", ""),
                "setup": "Calibrated instruments and approved SOP available.",
                "steps": ["Execute test at defined ranges and challenge conditions."],
                "dataToRecord": "Range values, alarm/interlock outcomes, evidence references.",
                "acceptanceCriteria": t.get("acceptanceCriteria", ""),
            }
            for t in oq_trs
        ]
    }
    prefs = (lifecycle.get("protocolPreferences") or {})
    pkg["PQ"] = {
        "purpose": "Verify repeatable process performance under representative and worst-case production conditions.",
        "prerequisites": "OQ complete, approved loads and acceptance criteria, trained operators, and required materials available.",
        "executionNotes": "Execute planned runs with full data capture and deviation handling per approved protocol.",
        "plan": "Representative production and worst-case challenge execution.",
        "pqCycles": int(prefs.get("pqRunCount") or 3),
        "worstCaseLoadDefinition": "Worst-case load profile from selected TRS coverage.",
        "biologicalIndicatorPlacement": "Define BI locations per approved load map where applicable.",
        "acceptanceCriteria": "; ".join([t.get("acceptanceCriteria", "") for t in pq_trs if t.get("acceptanceCriteria")]) or "Meets approved PQ acceptance criteria.",
        "tests": [
            {
                "testId": t.get("trsId", ""),
                "title": t.get("title", ""),
                "objective": t.get("objective", ""),
                "setup": "Production-representative operators, materials, and approved batch records.",
                "steps": ["Execute representative and worst-case runs."],
                "dataToRecord": "Run records, trend statistics, deviations, and evidence links.",
                "acceptanceCriteria": t.get("acceptanceCriteria", ""),
            }
            for t in pq_trs
        ],
    }
    pkg["computerizedValidation"] = lifecycle.get("computerizedValidation") or {}
    pkg["Requalification"] = _build_requalification_plan(pkg)
    pkg["csvGuidance"] = _build_csv_guidance(bool((pkg.get("computerizedValidation") or {}).get("computerized")))
    pkg["evidenceList"] = _build_evidence_list(pkg, bool((pkg.get("computerizedValidation") or {}).get("computerized")))

    trace_rows = []
    for t in iq_trs:
        trace_rows.append({
            "sourceType": "TRS",
            "sourceId": t.get("trsId", ""),
            "sourceTitle": t.get("title", ""),
            "targetProtocol": "IQ",
            "targetTest": t.get("title", ""),
        })
    for f in selected_frs:
        oq_for_frs = frs_to_oq.get(f.get("frsId", ""), [])
        if not oq_for_frs:
            trace_rows.append({
                "sourceType": "FRS",
                "sourceId": f.get("frsId", ""),
                "sourceTitle": f.get("title", ""),
                "targetProtocol": "OQ",
                "targetTest": "No mapped OQ test",
            })
            continue
        for t in oq_for_frs:
            trace_rows.append({
                "sourceType": "FRS",
                "sourceId": f.get("frsId", ""),
                "sourceTitle": f.get("title", ""),
                "targetProtocol": "OQ",
                "targetTest": f"{t.get('trsId', '')}: {t.get('title', '')}",
            })
    for u in selected_urs:
        related_frs = [f for f in selected_frs if u.get("ursId") in (f.get("derivedFromURS") or [])]
        related_pq = []
        for f in related_frs:
            related_pq.extend(frs_to_pq.get(f.get("frsId", ""), []))
        related_pq = list({t.get("trsId", ""): t for t in related_pq if t.get("trsId")}.values())
        if not related_pq:
            trace_rows.append({
                "sourceType": "URS",
                "sourceId": u.get("ursId", ""),
                "sourceTitle": u.get("title", ""),
                "targetProtocol": "PQ",
                "targetTest": "No mapped PQ test",
            })
            continue
        for t in related_pq:
            trace_rows.append({
                "sourceType": "URS",
                "sourceId": u.get("ursId", ""),
                "sourceTitle": u.get("title", ""),
                "targetProtocol": "PQ",
                "targetTest": f"{t.get('trsId', '')}: {t.get('title', '')}",
            })
    pkg["traceabilityMatrix"] = trace_rows
    pkg["traceability"] = {"hazardRules": []}

    # Deterministic, V-model-specific recommendation and metadata.
    pkg["qualificationBand"] = "VModel"
    pkg["ResidualRiskIndex"] = 0.0
    pkg["recommendation"] = "Generate V-model documents: VMP, URS, FRS, TRS, and IQ/OQ/PQ protocols."


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
        hazard.setdefault("VMP_list", [])
        hazard.setdefault("URS_list", [])
        hazard.setdefault("DQ_list", [])
        hazard.setdefault("Requalification_list", [])
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
                    if "VMP" in then:
                        hazard["VMP_list"] = _merge_list(hazard["VMP_list"], then["VMP"])
                    if "URS" in then:
                        hazard["URS_list"] = _merge_list(hazard["URS_list"], then["URS"])
                    if "DQ" in then:
                        hazard["DQ_list"] = _merge_list(hazard["DQ_list"], then["DQ"])
                    if "Requalification" in then:
                        hazard["Requalification_list"] = _merge_list(hazard["Requalification_list"], then["Requalification"])

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
    vmp_items = []
    urs_items = []
    dq_items = []
    rq_items = []
    for h in pkg["hazards"]:
        iq_checklist.extend(h.get("IQ_list", []))
        pq_items.extend(h.get("PQ_list", []))
        vmp_items.extend(h.get("VMP_list", []))
        urs_items.extend(h.get("URS_list", []))
        dq_items.extend(h.get("DQ_list", []))
        rq_items.extend(h.get("Requalification_list", []))
    iq_checklist = list(dict.fromkeys(iq_checklist))
    pq_items = list(dict.fromkeys(pq_items))
    vmp_items = list(dict.fromkeys(vmp_items))
    urs_items = list(dict.fromkeys(urs_items))
    dq_items = list(dict.fromkeys(dq_items))
    rq_items = list(dict.fromkeys(rq_items))

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
    lifecycle = pkg.get("lifecycle") or {}
    pkg["VMP"] = {
        "scope": (lifecycle.get("vmp") or {}).get("scope", ""),
        "roles": (lifecycle.get("vmp") or {}).get("roles", ""),
        "timeline": (lifecycle.get("vmp") or {}).get("timeline", ""),
        "deliverables": (lifecycle.get("vmp") or {}).get("deliverables", ""),
        "trainingPlan": (lifecycle.get("vmp") or {}).get("trainingPlan", ""),
        "supplierEvidencePlan": (lifecycle.get("vmp") or {}).get("supplierEvidencePlan", ""),
        "generatedItems": vmp_items,
    }
    pkg["URS"] = {
        "intendedUse": (lifecycle.get("urs") or {}).get("intendedUse", ""),
        "criticalProcessParameters": (lifecycle.get("urs") or {}).get("criticalProcessParameters", ""),
        "environmentNeeds": (lifecycle.get("urs") or {}).get("environmentNeeds", ""),
        "throughputRationale": (lifecycle.get("urs") or {}).get("throughputRationale", ""),
        "acceptanceCriteria": (lifecycle.get("urs") or {}).get("acceptanceCriteria", ""),
        "generatedItems": urs_items,
    }
    pkg["DQ"] = {
        "designSummary": (lifecycle.get("dq") or {}).get("designSummary", ""),
        "ursAlignment": (lifecycle.get("dq") or {}).get("ursAlignment", ""),
        "supplierAssessment": (lifecycle.get("dq") or {}).get("supplierAssessment", ""),
        "openItems": (lifecycle.get("dq") or {}).get("openItems", ""),
        "generatedItems": dq_items,
    }
    computerized = (lifecycle.get("computerizedValidation") or {}).get("computerized", False)
    pkg["computerizedValidation"] = {
        "computerized": computerized,
        "softwareClassification": (lifecycle.get("computerizedValidation") or {}).get("softwareClassification", ""),
        "part11Controls": (lifecycle.get("computerizedValidation") or {}).get("part11Controls", ""),
        "dataIntegrityControls": (lifecycle.get("computerizedValidation") or {}).get("dataIntegrityControls", ""),
        "patchConfigHistory": (lifecycle.get("computerizedValidation") or {}).get("patchConfigHistory", ""),
    }
    pkg["Requalification"] = _build_requalification_plan(pkg)
    if rq_items:
        pkg["Requalification"]["generatedItems"] = rq_items

    # CSV guidance and evidence when HMI used for release (21 CFR Part 11)
    pkg["csvGuidance"] = _build_csv_guidance(hmi_used_for_release)
    pkg["evidenceList"] = _build_evidence_list(pkg, hmi_used_for_release)

    # Traceability matrix: Hazard | Control | IQ/OQ/PQ Test ID | Acceptance
    pkg["traceabilityMatrix"] = _build_traceability_matrix(pkg)


def _set_default_iqoqpq(pkg):
    pkg["IQ"] = {"checklist": ["Installation verification per supplier drawing"]}
    pkg["OQ"] = {"tests": []}
    pkg["PQ"] = {"plan": "Default PQ plan", "pqCycles": 3, "worstCaseLoadDefinition": "", "biologicalIndicatorPlacement": "", "acceptanceCriteria": ""}
    pkg["VMP"] = {"scope": "", "roles": "", "timeline": "", "deliverables": "", "trainingPlan": "", "supplierEvidencePlan": "", "generatedItems": []}
    pkg["URS"] = {"intendedUse": "", "criticalProcessParameters": "", "environmentNeeds": "", "throughputRationale": "", "acceptanceCriteria": "", "generatedItems": []}
    pkg["DQ"] = {"designSummary": "", "ursAlignment": "", "supplierAssessment": "", "openItems": "", "generatedItems": []}
    pkg["computerizedValidation"] = {"computerized": False, "softwareClassification": "", "part11Controls": "", "dataIntegrityControls": "", "patchConfigHistory": ""}
    pkg["Requalification"] = _build_requalification_plan(pkg)
    for h in pkg["hazards"]:
        h.setdefault("IQ_list", [])
        h.setdefault("OQ_list", [])
        h.setdefault("PQ_list", [])
        h.setdefault("VMP_list", [])
        h.setdefault("URS_list", [])
        h.setdefault("DQ_list", [])
        h.setdefault("Requalification_list", [])


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
