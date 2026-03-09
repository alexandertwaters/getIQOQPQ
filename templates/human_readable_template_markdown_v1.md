# Installation Qualification, Operational Qualification, Performance Qualification
**Equipment**: {{equipment.type}}  
**Model**: {{equipment.model}}  
**Cohort**: {{equipment.cohort}}  
**Site context**: Cleanroom {{siteContext.cleanroomClass}}; Utilities: {{siteContext.utilities_comma}}; Product contact: {{siteContext.productContact_label}}; Throughput: {{siteContext.productionThroughput}}  
**Ruleset**: {{rulesetId}}  •  **Hazard catalog**: {{hazcatVersion}}  
**Package fingerprint**: {{fingerprint}}

---

## Executive summary
**Qualification band**: **{{qualificationBand}}**  
**Residual Risk Index**: **{{ResidualRiskIndex}}**  
**Recommendation**: {{recommendation}}

---

## Impact assessment (per hazard)
{{#each hazards}}
### Hazard: {{title}} ({{hazardId}})
**Definition**: {{definition}}  
**Standards**: {{standards_comma}}  
**Contextual tags**: {{contextualTags_comma}}

**Selected inputs**  
- **Severity**: {{Severity_label}}  
- **Probability of Occurrence**: {{ProbabilityOfOccurrence_label}}  
- **Exposure**: {{Exposure_label}}  
- **Detectability**: {{Detectability_label}}  
- **Control Effectiveness**: {{ControlEffectiveness_label}}

**Numeric calculations**  
- Raw Risk = {{RawRisk}}  
- Adjusted Risk = {{AdjustedRisk}}  
- Residual Risk = {{ResidualRisk}}  
{{#if EscalatedResidualRiskForMapping}}- Escalated Residual Risk (for mapping) = {{EscalatedResidualRiskForMapping}}{{/if}}

**Advisory mapping**  
- **Mapped IQ items**: {{#if IQ_list}}{{IQ_list}}{{else}}None applicable{{/if}}  
- **Mapped OQ tests**: {{#if OQ_list}}{{OQ_list}}{{else}}None applicable{{/if}}  
- **Mapped PQ plan items**: {{#if PQ_list}}{{PQ_list}}{{else}}None applicable{{/if}}

---
{{/each}}

## Installation Qualification (IQ) — Checklist
{{#if IQ.checklist}}
{{#each IQ.checklist}}
- [ ] **{{.}}**
{{/each}}
{{else}}
- None applicable
{{/if}}

## Operational Qualification (OQ) — Test scripts
{{#if OQ.tests}}
{{#each OQ.tests}}
### Test: {{title}}
**Objective**: {{objective}}  
**Setup**: {{setup}}  
**Steps**:
{{#each steps}}
1. {{.}}
{{/each}}
**Data to record**: {{dataToRecord}}  
**Acceptance criteria**: {{acceptanceCriteria}}

{{/each}}
{{else}}
No OQ tests generated.
{{/if}}

## Performance Qualification (PQ) — Plan
**PQ plan summary**: {{PQ.plan}}  
**Number of PQ cycles**: {{PQ.pqCycles}}  
**Worst‑case load definition**: {{PQ.worstCaseLoadDefinition}}  
**Biological indicator placement**: {{PQ.biologicalIndicatorPlacement}}  
**Acceptance criteria**: {{PQ.acceptanceCriteria}}

---

## Computerized system verification guidance
{{#if csvGuidance}}
{{#each csvGuidance}}
- {{.}}
{{/each}}
{{else}}
None applicable
{{/if}}

---

## Evidence list
{{#if evidenceList}}
{{#each evidenceList}}
- {{.}}
{{/each}}
{{else}}
- None listed
{{/if}}

---

## Traceability appendix
- **Ruleset executed**: {{rulesetId}}  
- **Hazard catalog**: {{hazcatVersion}}  
- **Executed ruleIds**: {{executedRuleIds_comma}}  
- **Per‑hazard numeric table**: attached CSV in artifact bundle

---

## Signatures
**Prepared by**: ____________________  **Date**: __________  
**Reviewed by**: ____________________  **Date**: __________  
**Approved by**: ____________________  **Date**: __________

---

**Advisory note**: This draft is advisory. Final protocols, acceptance criteria, and approvals must be completed in your QMS.
