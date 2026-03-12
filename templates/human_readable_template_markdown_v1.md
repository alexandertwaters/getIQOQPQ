<div align="center">

# Installation Qualification, Operational Qualification, Performance Qualification

</div>

**Cohort**: {{ equipment.cohort }}
**Equipment**: {{ equipment.type }}

{% if equipmentControlsFormatted and equipmentControlsFormatted | length > 0 %}
**Equipment controls**
{% for line in equipmentControlsFormatted %}
- {{ line }}
{% endfor %}
{% endif %}

---

## Executive summary

**Qualification band**: {{ qualificationBand }}

**Residual Risk Index**: {{ ResidualRiskIndex }}

**Recommendation**: {{ recommendation }}

---

## Risk / FMEA summary

| Hazard | Severity | Prob. | Raw | Adj | Residual | Escalated | Escalation |
|--------|----------|-------|-----|-----|----------|-----------|------------|
{% for h in hazards %}| {{ h.hazardId }} | {{ h.Severity_label }} | {{ h.ProbabilityOfOccurrence_label }} | {{ h.RawRisk }} | {{ h.AdjustedRisk }} | {{ h.ResidualRisk }} | {% if h.EscalatedResidualRiskForMapping %}{{ h.EscalatedResidualRiskForMapping }}{% else %}—{% endif %} | {% if h.escalationReason %}{{ h.escalationReason }}{% else %}—{% endif %} |
{% endfor %}

---

## Impact assessment (per hazard)

{% for h in hazards %}
### {{ h.title }}

{{ h.definition }}

| Selected labels | Value |
|-----------------|-------|
| Severity | {{ h.Severity_label }} ({{ h.Severity_value | default('N/A') }}) |
| Probability of occurrence | {{ h.ProbabilityOfOccurrence_label }} |
| Exposure | {{ h.Exposure_label }} |
| Detectability | {{ h.Detectability_label }} |
| Control effectiveness | {{ h.ControlEffectiveness_label }} |

{% if h.hazardContext %}
**Hazard Modifiers**
{% for k, v in h.hazardContext.items() %}
{% if v is not none and v != false and v != '' %}
- {{ k }}: {% if v is sequence and v is not string %}{{ v | join(', ') }}{% else %}{{ v }}{% endif %}
{% endif %}
{% endfor %}
{% endif %}

**Relevant Standards**: {{ h.standards_comma }}

{% if h.qualificationDepthEscalation %}
*Qualification depth escalation: Yes (challenging load/context; extra OQ/PQ items added)*
{% endif %}

#### Option annotations (help and examples)
{% for opt in (h.severityOptions or []) %}
{% if opt.label == h.Severity_label %}
- *{{ opt.label }}*: {{ opt.help | default('') }}{% if opt.example %} Example: {{ opt.example }}{% endif %}

{% endif %}
{% endfor %}
{% for opt in (h.probabilityOptions or []) %}
{% if opt.label == h.ProbabilityOfOccurrence_label %}
- *{{ opt.label }}*: {{ opt.help | default('') }}{% if opt.example %} Example: {{ opt.example }}{% endif %}

{% endif %}
{% endfor %}
{% for opt in (h.exposureOptions or []) %}
{% if opt.label == h.Exposure_label %}
- *{{ opt.label }}*: {{ opt.help | default('') }}{% if opt.example %} Example: {{ opt.example }}{% endif %}

{% endif %}
{% endfor %}
{% for opt in (h.detectabilityOptions or []) %}
{% if opt.label == h.Detectability_label %}
- *{{ opt.label }}*: {{ opt.help | default('') }}{% if opt.example %} Example: {{ opt.example }}{% endif %}

{% endif %}
{% endfor %}
{% for opt in (h.controlEffectivenessOptions or []) %}
{% if opt.label == h.ControlEffectiveness_label %}
- *{{ opt.label }}*: {{ opt.help | default('') }}{% if opt.example %} Example: {{ opt.example }}{% endif %}

{% endif %}
{% endfor %}

#### Numeric values and formula

- Severity = {{ h.Severity_value | default('N/A') }}
- Probability = {{ h.ProbabilityOfOccurrence_value | default('N/A') }}
- Exposure = {{ h.Exposure_value | default('N/A') }}
- Detectability = {{ h.Detectability_value | default('N/A') }}
- Control effectiveness = {{ h.ControlEffectiveness_value | default('N/A') }}

*Raw Risk = Severity × Probability of Occurrence*

*Adjusted Risk = Raw Risk × Exposure × (1 − Detectability)*

*Residual Risk = Adjusted Risk × Control Effectiveness*

- Raw Risk = {{ h.RawRisk }}
- Adjusted Risk = {{ h.AdjustedRisk }}
- Residual Risk = {{ h.ResidualRisk }}
{% if h.EscalatedResidualRiskForMapping %}- Escalated (for mapping) = {{ h.EscalatedResidualRiskForMapping }}{% endif %}

#### Advisory Qualification

- **IQ items**: {% if h.IQ_list %}{{ h.IQ_list | join('; ') }}{% else %}None applicable{% endif %}
- **OQ tests**: {% if h.OQ_list %}{{ h.OQ_list | join('; ') }}{% else %}None applicable{% endif %}
- **PQ items**: {% if h.PQ_list %}{{ h.PQ_list | join('; ') }}{% else %}None applicable{% endif %}

---
{% endfor %}

## Installation Qualification (IQ) — Checklist

{% if IQ.evidenceNamingConvention %}
**Evidence naming convention**: `{{ IQ.evidenceNamingConvention }}`  
{% if IQ.evidenceNamingHelp %}{{ IQ.evidenceNamingHelp }}{% endif %}
{% endif %}

{% if IQ.checklistItems %}
| ItemID | Category | Description | Expected | Measured | EvidenceFileName | Result | Owner | SignoffDate |
|--------|----------|-------------|----------|----------|------------------|--------|-------|-------------|
{% for it in IQ.checklistItems %}
| {{ it.itemId }} | {{ it.category }} | {{ it.description }} | {{ it.expected }} | | {{ it.evidenceFileName }} | | | |
{% endfor %}
{% elif IQ.checklist %}
{% for item in IQ.checklist %}
- [ ] {{ item }}
{% endfor %}
{% else %}
- Installation verification per supplier drawing
{% endif %}

## Operational Qualification (OQ) — Test scripts

{% if OQ.tests %}
{% for t in OQ.tests %}
### {{ t.title }}

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

{% if PQ.biologicalIndicatorPlacement and equipment.equipmentTypeId in ['STER_PV_AUT', 'STER_GRAV_AUT'] %}
#### BI placement matrix (template)

| Cycle | BI_ID | Location | Placement description | Incubation result | Date |
|-------|-------|----------|------------------------|-------------------|------|
| 1 | 1 | | | | |
| 1 | 2 | | | | |
| 1 | 3 | | | | |
| 1 | 4 | | | | |
| 1 | 5 | | | | |
| 1 | 6 | | | | |
| 1 | 7 | | | | |
| 1 | 8 | | | | |
| 1 | 9 | | | | |
| 1 | 10 | | | | |
| 1 | 11 | | | | |
| 1 | 12 | | | | |
| 2 | 1–12 | (repeat per cycle) | | | |
| 3 | 1–12 | (repeat per cycle) | | | |
{% endif %}

---

## Traceability matrix

| Hazard | Test type | Test ID | ruleId |
|--------|-----------|---------|--------|
{% for row in traceabilityMatrix %}| {{ row.hazardId }} | {{ row.testType }} | {{ row.testId }} | {{ row.ruleId }} |
{% endfor %}
{% if not traceabilityMatrix %}
No traceability data.
{% endif %}

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

## Signatures

**Prepared by**: ____________________  **Date**: __________

**Reviewed by**: ____________________  **Date**: __________

**Approved by**: ____________________  **Date**: __________

---

*Advisory note: This draft is advisory. Final protocols, acceptance criteria, and approvals must be completed in your QMS.*
