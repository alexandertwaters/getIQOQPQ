# Installation Qualification, Operational Qualification, Performance Qualification
**Equipment**: {{ equipment.type }}
**Model**: {{ equipment.model }}
**Cohort**: {{ equipment.cohort }}
**Site context**: Cleanroom {{ siteContext.cleanroomClass }}; Utilities: {{ siteContext.utilities_comma }}; Product contact: {{ siteContext.productContact_label }}; Throughput: {{ siteContext.productionThroughput }}
**Ruleset**: {{ rulesetId }}  •  **Hazard catalog**: {{ hazcatVersion }}
**Package fingerprint**: {{ fingerprint }}

---

## Executive summary
**Qualification band**: **{{ qualificationBand }}**
**Residual Risk Index**: **{{ ResidualRiskIndex }}**
**Recommendation**: {{ recommendation }}

---

## Impact assessment (per hazard)
{% for h in hazards %}
### {{ h.hazardId }} — {{ h.title }}

**Definition**: {{ h.definition }}

**Selected labels**
- Severity: **{{ h.Severity_label }}** (value: {{ h.Severity_value | default('N/A') }})
- Probability: **{{ h.ProbabilityOfOccurrence_label }}**
- Exposure: **{{ h.Exposure_label }}**
- Detectability: **{{ h.Detectability_label }}**
- Control Effectiveness: **{{ h.ControlEffectiveness_label }}**

**Contextual tags (catalog):** {{ h.contextualTags_catalog_comma }}
**Contextual tags (selected):** {{ h.contextualTags_selected_comma }}

**Rule:** {{ h.ruleId }}
**Standards:** {{ h.standards_comma }}

{% if h.severityOptions %}
**Option help and examples (Severity)**
{% for opt in h.severityOptions %}
- **{{ opt.label }}** — {{ opt.help | default('') }}; example: {{ opt.example | default('') }}
{% endfor %}
{% endif %}
{% if h.probabilityOptions %}
**Option help and examples (Probability)**
{% for opt in h.probabilityOptions %}
- **{{ opt.label }}** — {{ opt.help | default('') }}; example: {{ opt.example | default('') }}
{% endfor %}
{% endif %}
{% if h.exposureOptions %}
**Option help and examples (Exposure)**
{% for opt in h.exposureOptions %}
- **{{ opt.label }}** — {{ opt.help | default('') }}; example: {{ opt.example | default('') }}
{% endfor %}
{% endif %}
{% if h.detectabilityOptions %}
**Option help and examples (Detectability)**
{% for opt in h.detectabilityOptions %}
- **{{ opt.label }}** — {{ opt.help | default('') }}; example: {{ opt.example | default('') }}
{% endfor %}
{% endif %}
{% if h.controlEffectivenessOptions %}
**Option help and examples (Control Effectiveness)**
{% for opt in h.controlEffectivenessOptions %}
- **{{ opt.label }}** — {{ opt.help | default('') }}; example: {{ opt.example | default('') }}
{% endfor %}
{% endif %}

**Numeric calculations**
- Raw Risk = {{ h.RawRisk }}
- Adjusted Risk = {{ h.AdjustedRisk }}
- Residual Risk = {{ h.ResidualRisk }}
{% if h.EscalatedResidualRiskForMapping %}- Escalated Residual Risk (for mapping) = {{ h.EscalatedResidualRiskForMapping }}{% endif %}

**Advisory mapping**
- **Mapped IQ items**: {% if h.IQ_list %}{{ h.IQ_list | join(', ') }}{% else %}None applicable{% endif %}
- **Mapped OQ tests**: {% if h.OQ_list %}{{ h.OQ_list | join(', ') }}{% else %}None applicable{% endif %}
- **Mapped PQ plan items**: {% if h.PQ_list %}{{ h.PQ_list | join(', ') }}{% else %}None applicable{% endif %}

---
{% endfor %}

## Installation Qualification (IQ) — Checklist
{% if IQ.checklist %}
{% for item in IQ.checklist %}
- [ ] **{{ item }}**
{% endfor %}
{% else %}
- None applicable
{% endif %}

## Operational Qualification (OQ) — Test scripts
{% if OQ.tests %}
{% for t in OQ.tests %}
### Test: {{ t.title }}
**Objective**: {{ t.objective }}
**Setup**: {{ t.setup }}
**Steps**:
{% for step in t.steps %}
1. {{ step }}
{% endfor %}
**Data to record**: {{ t.dataToRecord }}
**Acceptance criteria**: {{ t.acceptanceCriteria }}

{% endfor %}
{% else %}
No OQ tests generated.
{% endif %}

## Performance Qualification (PQ) — Plan
**PQ plan summary**: {{ PQ.plan }}
**Number of PQ cycles**: {{ PQ.pqCycles }}
**Worst‑case load definition**: {{ PQ.worstCaseLoadDefinition }}
**Biological indicator placement**: {{ PQ.biologicalIndicatorPlacement }}
**Acceptance criteria**: {{ PQ.acceptanceCriteria }}

---

## Computerized system verification guidance
{% if csvGuidance %}
{% for item in csvGuidance %}
- {{ item }}
{% endfor %}
{% else %}
None applicable
{% endif %}

---

## Evidence list
{% if evidenceList %}
{% for item in evidenceList %}
- {{ item }}
{% endfor %}
{% else %}
None listed
{% endif %}

---

## Traceability appendix
- **Ruleset executed**: {{ rulesetId }}
- **Hazard catalog**: {{ hazcatVersion }}
- **Executed ruleIds**: {{ executedRuleIds_comma }}
- **Per‑hazard numeric table**: attached CSV in artifact bundle

---

## Signatures
**Prepared by**: ____________________  **Date**: __________
**Reviewed by**: ____________________  **Date**: __________
**Approved by**: ____________________  **Date**: __________

---

**Advisory note**: This draft is advisory. Final protocols, acceptance criteria, and approvals must be completed in your QMS.
