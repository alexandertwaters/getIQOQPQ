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
### Hazard: {{ h.title }} ({{ h.hazardId }})
**Definition**: {{ h.definition }}
**Standards**: {{ h.standards_comma }}
**Contextual tags**: {{ h.contextualTags_comma }}

**Selected inputs**
- **Severity**: {{ h.Severity_label }}
- **Probability of Occurrence**: {{ h.ProbabilityOfOccurrence_label }}
- **Exposure**: {{ h.Exposure_label }}
- **Detectability**: {{ h.Detectability_label }}
- **Control Effectiveness**: {{ h.ControlEffectiveness_label }}

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
