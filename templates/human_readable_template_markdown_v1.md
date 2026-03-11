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

{% if IQ.checklist %}
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
