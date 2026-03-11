# engine/render_engine.py
import json
import os
import sys
from jinja2 import Template

def load_template(path):
    with open(path, 'r', encoding='utf8') as f:
        return f.read()

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

def expand_tests_for_hazard(hazard, langmap):
    def expand_list(lst):
        out = []
        for tid in lst:
            key = tid.lower()
            entry = langmap.get(key)
            if not entry:
                entry = langmap.get("default", {
                    "title": tid,
                    "objective": f"Execute the supplier recommended verification for {tid}.",
                    "setup": "Follow supplier documentation.",
                    "steps": [f"Execute supplier recommended procedure for {tid}."],
                    "dataToRecord": "Supplier report and measured values.",
                    "acceptanceCriteria": "Meet supplier acceptance criteria or applicable standard."
                })
            out.append(entry)
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
    ctx["rulesetId"] = pkg.get("rulesetId", "")
    ctx["hazcatVersion"] = pkg.get("hazcatVersion", "")
    ctx["fingerprint"] = pkg.get("fingerprint", "")
    ctx["qualificationBand"] = pkg.get("qualificationBand", "")
    ctx["ResidualRiskIndex"] = f"{pkg.get('ResidualRiskIndex', 0.0):.3f}"
    ctx["equipmentControls"] = pkg.get("equipmentControls", {})
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
            "Severity_value": f"{h.get('Severity', 0.0):.12f}" if h.get("Severity") is not None else "N/A",
            "ProbabilityOfOccurrence_label": h.get("ProbabilityOfOccurrence_label", ""),
            "Exposure_label": h.get("Exposure_label", ""),
            "Detectability_label": h.get("Detectability_label", ""),
            "ControlEffectiveness_label": h.get("ControlEffectiveness_label", ""),
            "RawRisk": f"{h.get('RawRisk',0.0):.3f}",
            "AdjustedRisk": f"{h.get('AdjustedRisk',0.0):.3f}",
            "ResidualRisk": f"{h.get('ResidualRisk',0.0):.3f}",
            "EscalatedResidualRiskForMapping": f"{h.get('EscalatedResidualRiskForMapping',0.0):.3f}" if h.get("EscalatedResidualRiskForMapping") is not None else None,
            "IQ_list": [t.get("title", "") for t in expanded["IQ_tests"]],
            "OQ_list": [t.get("title", "") for t in expanded["OQ_tests"]],
            "PQ_list": [t.get("title", "") for t in expanded["PQ_tests"]],
            "IQ_tests": expanded["IQ_tests"],
            "OQ_tests": expanded["OQ_tests"],
            "PQ_tests": expanded["PQ_tests"],
            "hazardContext": h.get("hazardContext", {}),
            "qualificationDepthEscalation": h.get("qualificationDepthEscalation", False),
        })
    ctx["hazards"] = hazards_ctx
    ctx["IQ"] = {"checklist": pkg.get("IQ", {}).get("checklist", [])}
    oq_tests = []
    for h in sorted(hazards_ctx, key=lambda x: x["hazardId"]):
        for t in h["OQ_tests"]:
            oq_tests.append(t)
    ctx["OQ"] = {"tests": oq_tests}
    ctx["PQ"] = pkg.get("PQ", {})
    ctx["csvGuidance"] = pkg.get("csvGuidance", [])
    ctx["evidenceList"] = pkg.get("evidenceList", [])
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
