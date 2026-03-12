# engine/render_engine.py
import json
import os
import sys
from pathlib import Path
from jinja2 import Template


def _load_equipment_controls_catalog(base_path=None):
    base = Path(base_path or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = base / "data" / "equipment_controls_catalog.json"
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("equipmentTypes", [])


def _format_equipment_controls_human(pkg):
    """Build human-readable equipment controls lines: 'Control label: Response'."""
    ec = pkg.get("equipmentControls") or {}
    if not ec:
        return []
    et_id = pkg.get("equipment", {}).get("equipmentTypeId")
    if not et_id:
        return [f"{k}: {v}" for k, v in sorted(ec.items())]

    catalog = _load_equipment_controls_catalog()
    ctrl_map = {}
    for et in catalog:
        if et.get("equipmentTypeId") != et_id:
            continue
        for cat in et.get("controlCategories", []):
            for ctrl in cat.get("controls", []):
                cid = ctrl.get("controlId")
                if cid:
                    ctrl_map[cid] = {"label": ctrl.get("label", cid), "valueType": ctrl.get("valueType", "boolean"), "options": ctrl.get("options", [])}

    lines = []
    for cid, val in sorted(ec.items()):
        if val == "" or val is False:
            continue
        info = ctrl_map.get(cid, {})
        label = info.get("label", cid)
        if info.get("valueType") == "boolean":
            resp = "Yes" if val else "No"
        elif info.get("valueType") == "choice" and info.get("options"):
            opt = next((o for o in info["options"] if (o.get("value") or o.get("label")) == val), None)
            resp = (opt.get("label") or opt.get("value") or val) if opt else val
        else:
            resp = str(val)
        lines.append(f"{label}: {resp}")
    return lines


def load_template(path):
    with open(path, 'r', encoding='utf8') as f:
        return f.read()


def _build_iq_test_scripts_table(checklist_items):
    """Build representative IQ test script rows (Category | Objective | Setup | Steps | Data to record | Acceptance) from checklist items."""
    if not checklist_items:
        return []
    by_cat = {}
    for it in checklist_items:
        cat = it.get("category", "Other")
        if cat not in by_cat:
            by_cat[cat] = []
        by_cat[cat].append(it)
    rows = []
    for cat, items in sorted(by_cat.items()):
        first = items[0]
        desc = first.get("description", "")
        expected = first.get("expected", "")
        objective = f"Verify {desc}" if desc else "Verify installation per specification."
        setup = "Equipment installed; drawings and supplier documentation available; tools and calibrated instruments per procedure."
        steps = "1. Review specification and drawings. 2. Verify item per expected criteria. 3. Record results and evidence."
        if len(items) > 1:
            steps = "1. Review specification and drawings. 2. Verify each item in this category per expected criteria. 3. Record results and evidence."
        data = "Checklist result (Pass/Fail), measured values if applicable, evidence file reference."
        acceptance = expected if expected else "Conforms to supplier specification and site requirements."
        rows.append({
            "category": cat,
            "objective": objective,
            "setup": setup,
            "steps": steps,
            "dataToRecord": data,
            "acceptanceCriteria": acceptance,
        })
    return rows


def build_langmap(langmap_doc):
    m = {}
    default = None
    for entry in langmap_doc.get("mappings", []):
        match = entry.get("match", {})
        human = entry.get("human", {})
        test_id = match.get("testId")
        if test_id:
            m[test_id.lower()] = human
        if test_id == "default":
            default = human
    if default:
        m["default"] = default
    return m

def _substitute_test_id(obj, tid):
    """Replace {{testId}} in strings/lists with actual test id."""
    tid_str = tid if isinstance(tid, str) else str(tid)
    if isinstance(obj, str):
        return obj.replace("{{testId}}", tid_str)
    if isinstance(obj, list):
        return [_substitute_test_id(x, tid_str) for x in obj]
    if isinstance(obj, dict):
        return {k: _substitute_test_id(v, tid_str) for k, v in obj.items()}
    return obj


def expand_tests_for_hazard(hazard, langmap):
    def expand_list(lst):
        out = []
        for tid in lst:
            raw_tid = tid if isinstance(tid, str) else str(tid)
            key = raw_tid.lower()
            entry = langmap.get(key)
            if not entry:
                entry = langmap.get("default", {
                    "title": "{{testId}}",
                    "objective": "Execute the supplier recommended verification for {{testId}}.",
                    "setup": "Follow supplier documentation and applicable standards.",
                    "steps": ["Execute supplier recommended procedure for {{testId}}."],
                    "dataToRecord": "Supplier report and measured values.",
                    "acceptanceCriteria": "Meet supplier acceptance criteria or applicable standard."
                })
            substituted = _substitute_test_id(dict(entry), raw_tid)
            out.append(substituted)
        return out

    return {
        "IQ_tests": expand_list(hazard.get("IQ_list", [])),
        "OQ_tests": expand_list(hazard.get("OQ_list", [])),
        "PQ_tests": expand_list(hazard.get("PQ_list", []))
    }

def render_markdown(pkg_path, template_md_path, langmap_path, outdir):
    with open(pkg_path, 'r', encoding='utf8') as f:
        pkg = json.load(f)
    with open(langmap_path, 'r', encoding='utf8') as f:
        langmap_doc = json.load(f)
    langmap = build_langmap(langmap_doc)
    template_md = load_template(template_md_path)

    ctx = {}
    ctx["equipment"] = pkg.get("equipment", {})
    sc = pkg.get("siteContext", {})
    ctx["siteContext"] = {
        "cleanroomClass": sc.get("cleanroomClass", ""),
        "utilities_comma": ", ".join(sorted(sc.get("utilities", []))),
        "productContact_label": "Yes" if sc.get("productContact", False) else "No",
        "productionThroughput": sc.get("productionThroughput", "")
    }
    ctx["qualificationBand"] = pkg.get("qualificationBand", "")
    ctx["ResidualRiskIndex"] = f"{pkg.get('ResidualRiskIndex', 0.0):.3f}"
    ctx["recommendation"] = pkg.get("recommendation", "")
    ctx["equipmentControlsFormatted"] = _format_equipment_controls_human(pkg)
    ctx["recommendation"] = pkg.get("recommendation", "")

    hazards_ctx = []
    for h in pkg.get("hazards", []):
        expanded = expand_tests_for_hazard(h, langmap)
        hazards_ctx.append({
            "hazardId": h.get("hazardId", ""),
            "title": h.get("title", ""),
            "definition": h.get("definition", ""),
            "standards_comma": ", ".join(h.get("standards", [])) if h.get("standards") else "",
            "ruleId": h.get("ruleId", ""),
            "severityOptions": h.get("severityOptions", []),
            "probabilityOptions": h.get("probabilityOptions", []),
            "exposureOptions": h.get("exposureOptions", []),
            "detectabilityOptions": h.get("detectabilityOptions", []),
            "controlEffectivenessOptions": h.get("controlEffectivenessOptions", []),
            "Severity_label": h.get("Severity_label", ""),
            "Severity_value": f"{h.get('Severity', 0.0):.2f}" if h.get("Severity") is not None else "—",
            "ProbabilityOfOccurrence_value": f"{h.get('ProbabilityOfOccurrence', 0.0):.2f}" if h.get("ProbabilityOfOccurrence") is not None else "—",
            "ProbabilityOfOccurrence_label": h.get("ProbabilityOfOccurrence_label", ""),
            "Exposure_value": f"{h.get('Exposure', 0.0):.2f}" if h.get("Exposure") is not None else "—",
            "Exposure_label": h.get("Exposure_label", ""),
            "Detectability_value": f"{h.get('Detectability', 0.0):.2f}" if h.get("Detectability") is not None else "—",
            "Detectability_label": h.get("Detectability_label", ""),
            "ControlEffectiveness_value": f"{h.get('ControlEffectiveness', 0.0):.2f}" if h.get("ControlEffectiveness") is not None else "—",
            "ControlEffectiveness_label": h.get("ControlEffectiveness_label", ""),
            "RawRisk": f"{h.get('RawRisk', 0.0):.2f}",
            "AdjustedRisk": f"{h.get('AdjustedRisk', 0.0):.2f}",
            "ResidualRisk": f"{h.get('ResidualRisk', 0.0):.2f}",
            "EscalatedResidualRiskForMapping": f"{h.get('EscalatedResidualRiskForMapping', 0.0):.2f}" if h.get("EscalatedResidualRiskForMapping") is not None else None,
            "IQ_list": [t.get("title", "") for t in expanded["IQ_tests"]],
            "OQ_list": [t.get("title", "") for t in expanded["OQ_tests"]],
            "PQ_list": [t.get("title", "") for t in expanded["PQ_tests"]],
            "IQ_tests": expanded["IQ_tests"],
            "OQ_tests": expanded["OQ_tests"],
            "PQ_tests": expanded["PQ_tests"],
            "hazardContext": h.get("hazardContext", {}),
            "qualificationDepthEscalation": h.get("qualificationDepthEscalation", False),
            "escalationReason": h.get("escalationReason", ""),
        })
    ctx["hazards"] = hazards_ctx
    iq = pkg.get("IQ", {})
    ctx["IQ"] = {
        "checklist": iq.get("checklist", []),
        "checklistItems": iq.get("checklistItems", []),
        "evidenceNamingConvention": iq.get("evidenceNamingConvention", ""),
        "evidenceNamingHelp": iq.get("evidenceNamingHelp", ""),
        "testScripts": _build_iq_test_scripts_table(iq.get("checklistItems", [])) or ([{"category": "Installation", "objective": "Verify equipment installed per specification.", "setup": "Drawings and supplier documentation available.", "steps": "1. Review spec and drawings. 2. Verify each item. 3. Record results.", "dataToRecord": "Pass/Fail, evidence reference.", "acceptanceCriteria": "Conforms to supplier and site requirements."}] if iq.get("checklist") else []),
    }
    # Deduplicate OQ tests by title so same test appears once
    oq_seen = {}
    oq_tests = []
    for h in sorted(hazards_ctx, key=lambda x: x["hazardId"]):
        for t in h["OQ_tests"]:
            title = t.get("title", "") or ""
            if title and title not in oq_seen:
                oq_seen[title] = t
                oq_tests.append(t)
    ctx["OQ"] = {"tests": oq_tests}
    ctx["PQ"] = pkg.get("PQ", {})
    ctx["VMP"] = pkg.get("VMP", {})
    ctx["URS"] = pkg.get("URS", {})
    ctx["DQ"] = pkg.get("DQ", {})
    ctx["computerizedValidation"] = pkg.get("computerizedValidation", {})
    ctx["Requalification"] = pkg.get("Requalification", {})
    ctx["csvGuidance"] = pkg.get("csvGuidance", [])
    ctx["evidenceList"] = pkg.get("evidenceList", [])
    ctx["traceabilityMatrix"] = pkg.get("traceabilityMatrix", [])
    ctx["executedRuleIds_comma"] = ", ".join([r for r in pkg.get("traceability", {}).get("hazardRules", []) if r])

    template = Template(template_md)
    md = template.render(**ctx)

    os.makedirs(outdir, exist_ok=True)
    fp = pkg.get("fingerprint", "package")
    safe_fp = fp.replace(":", "_")
    out_md = os.path.join(outdir, f"{safe_fp}.md")
    with open(out_md, 'w', encoding='utf8') as of:
        of.write(md)

    def _csv_escape(val):
        s = str(val).replace("\n", " ").replace("\r", " ")
        if "," in s or '"' in s or "\n" in s:
            return '"' + s.replace('"', '""') + '"'
        return s

    # IQ checklist CSV (structured items when present)
    iq_items = pkg.get("IQ", {}).get("checklistItems", [])
    if iq_items:
        iq_csv_path = os.path.join(outdir, f"{safe_fp}.IQ_checklist.csv")
        with open(iq_csv_path, 'w', encoding='utf8', newline='') as iqf:
            iqf.write("ItemID,Category,Description,Expected,Measured,EvidenceFileName,Result,Owner,SignoffDate\n")
            for it in iq_items:
                row = [
                    it.get("itemId", ""),
                    it.get("category", ""),
                    it.get("description", ""),
                    it.get("expected", ""),
                    "",
                    it.get("evidenceFileName", ""),
                    "",
                    "",
                    "",
                ]
                iqf.write(",".join(_csv_escape(x) for x in row) + "\n")
        print("IQ checklist CSV written to", iq_csv_path)

    # PQ worksheet CSV (BI placement template for sterilizers)
    pq = pkg.get("PQ", {})
    eq_id = pkg.get("equipment", {}).get("equipmentTypeId", "")
    if eq_id in ("STER_PV_AUT", "STER_GRAV_AUT") and pq.get("biologicalIndicatorPlacement"):
        pq_csv_path = os.path.join(outdir, f"{safe_fp}.PQ_worksheet.csv")
        with open(pq_csv_path, 'w', encoding='utf8', newline='') as pqf:
            pqf.write("Cycle,BI_ID,Location,Placement_Description,Incubation_Result,Incubation_Date,Reviewed\n")
            for cyc in range(1, 4):
                for bi in range(1, 13):
                    pqf.write(f"{cyc},{bi},,,,,\n")
            pqf.write("\nBI Incubation Log:\n")
            pqf.write("BI_ID,Cycle_Date,Incubation_Start,Incubation_End,Result,Reviewer\n")
        print("PQ worksheet CSV written to", pq_csv_path)

    csv_path = os.path.join(outdir, f"{safe_fp}.perHazard.csv")
    with open(csv_path, 'w', encoding='utf8', newline='') as cf:
        headers = [
            "hazardId", "title", "definition",
            "Severity_label", "Severity_numeric",
            "Probability_label", "Probability_numeric", "Exposure_label", "Exposure_numeric",
            "Detectability_label", "Detectability_numeric", "ControlEffectiveness_label", "ControlEffectiveness_numeric",
            "RawRisk", "AdjustedRisk", "ResidualRisk", "EscalatedResidualRiskForMapping",
            "ruleId", "standards"
        ]
        cf.write(",".join(headers) + "\n")
        for h in sorted(pkg.get("hazards", []), key=lambda x: x["hazardId"]):
            stds = h.get("standards", [])
            row = [
                h.get("hazardId", ""),
                h.get("title", ""),
                h.get("definition", ""),
                h.get("Severity_label", ""),
                f"{h.get('Severity',0.0):.12f}",
                h.get("ProbabilityOfOccurrence_label", ""),
                f"{h.get('ProbabilityOfOccurrence',0.0):.12f}",
                h.get("Exposure_label", ""),
                f"{h.get('Exposure',0.0):.12f}",
                h.get("Detectability_label", ""),
                f"{h.get('Detectability',0.0):.12f}",
                h.get("ControlEffectiveness_label", ""),
                f"{h.get('ControlEffectiveness',0.0):.12f}",
                f"{h.get('RawRisk',0.0):.12f}",
                f"{h.get('AdjustedRisk',0.0):.12f}",
                f"{h.get('ResidualRisk',0.0):.12f}",
                f"{h.get('EscalatedResidualRiskForMapping',0.0):.12f}",
                h.get("ruleId", ""),
                "; ".join(stds) if stds else "",
            ]
            cf.write(",".join(_csv_escape(x) for x in row) + "\n")

    print("Rendered markdown to", out_md)
    print("Per-hazard CSV written to", csv_path)

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python engine/render_engine.py <package.json> <template.md> <langmap.json> <outdir>")
        sys.exit(2)
    pkg_path = sys.argv[1]
    template_path = sys.argv[2]
    langmap_path = sys.argv[3]
    outdir = sys.argv[4]
    render_markdown(pkg_path, template_path, langmap_path, outdir)
