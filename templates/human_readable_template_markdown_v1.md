# Installation Qualification, Operational Qualification, Performance Qualification

---

**Cohort:** {{ equipment.cohort }}

**Equipment:** {{ equipment.type }}

{% if equipmentControlsFormatted and equipmentControlsFormatted | length > 0 %}
**Equipment controls**
{% for line in equipmentControlsFormatted %}
- {{ line }}
{% endfor %}
{% endif %}

---

# Executive summary

**Qualification band:** {{ qualificationBand }}

**Residual Risk Index:** {{ ResidualRiskIndex }}

**Recommendation:** {{ recommendation }}

---

# Validation Master Plan (VMP)

| Topic | Details |
|------|---------|
| Scope | {{ VMP.scope if VMP.scope else "To be completed by site." }} |
| Roles and responsibilities | {{ VMP.roles if VMP.roles else "Engineering, Validation, QA, Operations." }} |
| Timeline | {{ VMP.timeline if VMP.timeline else "To be defined in project plan." }} |
| Deliverables | {{ VMP.deliverables if VMP.deliverables else "VMP, URS, DQ, IQ/OQ/PQ protocols, reports, traceability matrix." }} |
| Training plan | {{ VMP.trainingPlan if VMP.trainingPlan else "Training records required before protocol execution." }} |
| Supplier evidence plan | {{ VMP.supplierEvidencePlan if VMP.supplierEvidencePlan else "Collect FAT/SAT, calibration, manuals, software baseline." }} |

{% if VMP.generatedItems %}
**Generated VMP focus items**
{% for item in VMP.generatedItems %}
- {{ item }}
{% endfor %}
{% endif %}

---

# User Requirements Specification (URS)

| Requirement area | Details |
|------------------|---------|
| Intended use | {{ URS.intendedUse if URS.intendedUse else "Define intended sterilization use and process context." }} |
| Critical process parameters | {{ URS.criticalProcessParameters if URS.criticalProcessParameters else "Define temperature, pressure, dwell, load limits, and alarms." }} |
| Environmental needs | {{ URS.environmentNeeds if URS.environmentNeeds else "Define utilities, cleanroom/environment constraints, and monitoring." }} |
| Throughput rationale | {{ URS.throughputRationale if URS.throughputRationale else "Define throughput and cycle/day expectations." }} |
| Acceptance criteria | {{ URS.acceptanceCriteria if URS.acceptanceCriteria else "Define measurable acceptance criteria for IQ/OQ/PQ." }} |

{% if URS.generatedItems %}
**Generated URS focus items**
{% for item in URS.generatedItems %}
- {{ item }}
{% endfor %}
{% endif %}

---

# Design Qualification (DQ)

| DQ element | Details |
|------------|---------|
| Design summary | {{ DQ.designSummary if DQ.designSummary else "Document chosen equipment design and key features." }} |
| URS alignment | {{ DQ.ursAlignment if DQ.ursAlignment else "Document design-to-URS conformance prior to installation." }} |
| Supplier/design evidence | {{ DQ.supplierAssessment if DQ.supplierAssessment else "Capture supplier docs, drawings, software baseline, FAT/SAT." }} |
| Open items | {{ DQ.openItems if DQ.openItems else "Track residual design gaps and mitigation actions." }} |

{% if DQ.generatedItems %}
**Generated DQ focus items**
{% for item in DQ.generatedItems %}
- {{ item }}
{% endfor %}
{% endif %}

---

# Risk / FMEA summary

Concise risk overview. Hazard names and scores below; escalation noted when applied.

| Hazard | Severity | Probability | Exposure | Detectability | Control | Raw | Adj. | Residual | Escalated | Escalation note |
|--------|----------|-------------|----------|---------------|---------|-----|------|----------|-----------|-----------------|
{% for h in hazards %}| {{ h.title }} | {{ h.Severity_label }} ({{ h.Severity_value }}) | {{ h.ProbabilityOfOccurrence_label }} ({{ h.ProbabilityOfOccurrence_value }}) | {{ h.Exposure_label }} ({{ h.Exposure_value }}) | {{ h.Detectability_label }} ({{ h.Detectability_value }}) | {{ h.ControlEffectiveness_label }} ({{ h.ControlEffectiveness_value }}) | {{ h.RawRisk }} | {{ h.AdjustedRisk }} | {{ h.ResidualRisk }} | {% if h.EscalatedResidualRiskForMapping %}{{ h.EscalatedResidualRiskForMapping }}{% else %}—{% endif %} | {% if h.escalationReason %}{{ h.escalationReason }}{% else %}—{% endif %} |
{% endfor %}

---

# Installation Qualification (IQ)

## IQ checklist

| Category | Description | Expected | Measured | Result | Owner | Signoff |
|----------|-------------|----------|----------|--------|-------|---------|
{% if IQ.checklistItems %}
{% for it in IQ.checklistItems %}
| {{ it.category }} | {{ it.description }} | {{ it.expected }} | | | | |
{% endfor %}
{% elif IQ.checklist %}
{% for item in IQ.checklist %}
| — | {{ item }} | Per specification | | | | |
{% endfor %}
{% else %}
| — | Installation verification per supplier drawing | Per specification | | | | |
{% endif %}

## IQ test scripts (representative)

Representative objectives, setup, steps, data to record, and acceptance criteria. Adapt to site procedures.

| Area | Objective | Setup | Steps | Data to record | Acceptance |
|------|-----------|-------|-------|----------------|------------|
{% for row in IQ.testScripts %}
| {{ row.category }} | {{ row.objective }} | {{ row.setup }} | {{ row.steps }} | {{ row.dataToRecord }} | {{ row.acceptanceCriteria }} |
{% endfor %}
{% if not IQ.testScripts %}
| Installation | Verify equipment installed per specification | Drawings and supplier docs available | 1. Review spec and drawings. 2. Verify each item. 3. Record results | Pass/Fail, evidence reference | Conforms to supplier and site requirements |
{% endif %}

---

# Operational Qualification (OQ)

Test scripts below. Each test is listed once; group execution by procedure where applicable.

| Test | Objective | Setup | Steps | Data to record | Acceptance |
|------|-----------|-------|-------|----------------|------------|
{% for t in OQ.tests %}
| {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {% for step in t.steps %}{{ step }}{% if not loop.last %}; {% endif %}{% endfor %} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not OQ.tests %}
| — | No OQ tests generated | — | — | — | — |
{% endif %}

---

# Performance Qualification (PQ)

**PQ plan summary:** {{ PQ.plan }}

**Number of PQ cycles:** {{ PQ.pqCycles }}

**Worst-case load definition:** {{ PQ.worstCaseLoadDefinition }}

**Biological indicator placement:** {{ PQ.biologicalIndicatorPlacement }}

**Acceptance criteria:** {{ PQ.acceptanceCriteria }}

## PQ test script (representative)

| Objective | Setup | Steps | Data to record | Acceptance |
|-----------|-------|-------|----------------|------------|
| Demonstrate sterilization under worst-case load using biological indicators | BIs at worst-case locations; load per validated configuration | 1. Place BIs per placement plan. 2. Run cycle per validated parameters. 3. Retrieve BIs and incubate per manufacturer. 4. Record results | Cycle log; BI placement; incubation results; BI lot | All BIs no growth; cycle parameters within OQ limits |

{% if PQ.biologicalIndicatorPlacement and equipment.equipmentTypeId in ['STER_PV_AUT', 'STER_GRAV_AUT'] %}
## BI placement matrix (template)

| Cycle | BI number | Location | Placement description | Incubation result | Date |
|-------|-----------|----------|------------------------|-------------------|------|
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
| 2 | 1 | | | | |
| 2 | 2 | | | | |
| 2 | 3 | | | | |
| 2 | 4 | | | | |
| 2 | 5 | | | | |
| 2 | 6 | | | | |
| 2 | 7 | | | | |
| 2 | 8 | | | | |
| 2 | 9 | | | | |
| 2 | 10 | | | | |
| 2 | 11 | | | | |
| 2 | 12 | | | | |
| 3 | 1 | | | | |
| 3 | 2 | | | | |
| 3 | 3 | | | | |
| 3 | 4 | | | | |
| 3 | 5 | | | | |
| 3 | 6 | | | | |
| 3 | 7 | | | | |
| 3 | 8 | | | | |
| 3 | 9 | | | | |
| 3 | 10 | | | | |
| 3 | 11 | | | | |
| 3 | 12 | | | | |
{% endif %}

---

# Traceability matrix

| Hazard | Test type | Test |
|--------|-----------|------|
{% for row in traceabilityMatrix %}
| {{ row.hazardTitle }} | {{ row.testType }} | {{ row.testTitle }} |
{% endfor %}
{% if not traceabilityMatrix %}
| — | — | No traceability data |
{% endif %}

---

# Computerized system verification guidance

| Computerized system item | Value |
|--------------------------|-------|
| Computerized / software impacts quality | {% if computerizedValidation.computerized %}Yes{% else %}No{% endif %} |
| Software classification | {{ computerizedValidation.softwareClassification if computerizedValidation.softwareClassification else "Not specified" }} |
| Part 11 controls | {{ computerizedValidation.part11Controls if computerizedValidation.part11Controls else "Document audit trail, access control, and e-record controls as applicable." }} |
| Data integrity controls | {{ computerizedValidation.dataIntegrityControls if computerizedValidation.dataIntegrityControls else "Document backup/restore, reconciliation, and review controls." }} |
| Patch/configuration history | {{ computerizedValidation.patchConfigHistory if computerizedValidation.patchConfigHistory else "Maintain change history and validated-state assessment." }} |

{% if csvGuidance %}
{% for item in csvGuidance %}
- {{ item }}
{% endfor %}
{% else %}
None applicable.
{% endif %}

---

# Evidence list

{% if evidenceList %}
{% for item in evidenceList %}
- {{ item }}
{% endfor %}
{% else %}
None listed.
{% endif %}

---

# Requalification plan

| Item | Details |
|------|---------|
| Base frequency | {{ Requalification.frequency if Requalification.frequency else "Annual" }} |
| Rationale | {{ Requalification.rationale if Requalification.rationale else "Risk and process criticality based." }} |

| Trigger | Included |
|---------|----------|
{% if Requalification.triggers %}
{% for trig in Requalification.triggers %}
| {{ trig }} | Yes |
{% endfor %}
{% else %}
| Relocation or move | Yes |
| Major repair or maintenance affecting function | Yes |
| Process parameter or load pattern change | Yes |
| Out-of-tolerance/deviation event | Yes |
{% endif %}

{% if Requalification.generatedItems %}
**Generated requalification focus items**
{% for item in Requalification.generatedItems %}
- {{ item }}
{% endfor %}
{% endif %}

---

# Signatures

**Prepared by:** ____________________  **Date:** __________

**Reviewed by:** ____________________  **Date:** __________

**Approved by:** ____________________  **Date:** __________

---

Advisory note: This draft is advisory. Final protocols, acceptance criteria, and approvals must be completed in your QMS.
