# Comprehensive Qualification Package

## Equipment Overview

| Field | Value |
|------|-------|
| Cohort | {{ equipment.cohort }} |
| Equipment Type | {{ equipment.type }} |
| Equipment ID / Model | {{ equipment.model if equipment.model else "To be completed" }} |
| Qualification Approach | V-model (TRS -> IQ, FRS -> OQ, URS -> PQ) |

---

# Validation Master Plan (VMP)

## Scope
{{ VMP.scope if VMP.scope else "Define equipment scope, boundaries, and intended validated lifecycle usage." }}

## Objective
{{ VMP.objective if VMP.objective else "Establish the strategy and controls to qualify equipment and maintain validated state." }}

## Roles and Responsibilities
{{ VMP.roles if VMP.roles else "Engineering, Validation, QA, Operations, and System Owner." }}

## Qualification Strategy
{{ VMP.qualificationStrategy if VMP.qualificationStrategy else "Use a V-model workflow: TRS verifies IQ, FRS verifies OQ, URS verifies PQ." }}

## Requalification Plan
Base Frequency: {{ Requalification.frequency if Requalification.frequency else "Annual" }}

Triggers:
{% if Requalification.triggers %}
{% for trig in Requalification.triggers %}
- {{ trig }}
{% endfor %}
{% else %}
- Relocation or move
- Major repair or maintenance
- Process or configuration change
- Out-of-tolerance/deviation event
{% endif %}

Rationale: {{ Requalification.rationale if Requalification.rationale else "Risk and process criticality based." }}

## Deliverables
{{ VMP.deliverables if VMP.deliverables else "This package plus approved execution records, deviations, and final report." }}

---

# User Requirements Specification (URS)

| Item ID | Requirement | Rationale | Acceptance Criteria | Test Method | Critical to Quality | Responsible |
|--------|-------------|-----------|---------------------|-------------|---------------------|-------------|
{% for row in URS.tableRows %}
| {{ row.itemId }} | {{ row.requirement }} | {{ row.rationale }} | {{ row.acceptanceCriteria }} | {{ row.testMethod }} | {{ row.ctq }} | {{ row.responsible }} |
{% endfor %}
{% if not URS.tableRows %}
| — | No URS rows selected | — | — | — | — | — |
{% endif %}

---

# Functional Requirements Specification (FRS)

| Item ID | Requirement | Rationale | Acceptance Criteria | Test Method | Critical to Quality | Responsible |
|--------|-------------|-----------|---------------------|-------------|---------------------|-------------|
{% for row in FRS.tableRows %}
| {{ row.itemId }} | {{ row.requirement }} | {{ row.rationale }} | {{ row.acceptanceCriteria }} | {{ row.testMethod }} | {{ row.ctq }} | {{ row.responsible }} |
{% endfor %}
{% if not FRS.tableRows %}
| — | No FRS rows selected | — | — | — | — | — |
{% endif %}

---

# Technical Requirements Specification (TRS)

| Item ID | Requirement | Rationale | Acceptance Criteria | Test Method | Critical to Quality | Responsible |
|--------|-------------|-----------|---------------------|-------------|---------------------|-------------|
{% for row in TRS.tableRows %}
| {{ row.itemId }} | {{ row.requirement }} | {{ row.rationale }} | {{ row.acceptanceCriteria }} | {{ row.testMethod }} | {{ row.ctq }} | {{ row.responsible }} |
{% endfor %}
{% if not TRS.tableRows %}
| — | No TRS rows selected | — | — | — | — | — |
{% endif %}

---

# Installation Qualification (IQ) Protocol

## Purpose
{{ IQ.purpose if IQ.purpose else "Verify installation, utilities, configuration baseline, and readiness for operation." }}

## Prerequisites
{{ IQ.prerequisites if IQ.prerequisites else "Approved protocol, calibrated instruments, installation complete, required documentation available." }}

## Execution Notes
{{ IQ.executionNotes if IQ.executionNotes else "Execute in sequence, document objective evidence, and resolve deviations per QMS." }}

| Protocol ID | Test | Objective | Setup | Steps | Data to Record | Acceptance Criteria |
|------------|------|-----------|-------|-------|----------------|---------------------|
{% for t in IQ.testScripts %}
| {{ t.testId }} | {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {{ t.steps }} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not IQ.testScripts %}
| — | No IQ tests mapped | — | — | — | — | — |
{% endif %}

---

# Operational Qualification (OQ) Protocol

## Purpose
{{ OQ.purpose if OQ.purpose else "Verify functional operation across intended ranges, challenges, alarms, and controls." }}

## Prerequisites
{{ OQ.prerequisites if OQ.prerequisites else "IQ complete, approved methods available, calibrated challenge instruments ready." }}

## Execution Notes
{{ OQ.executionNotes if OQ.executionNotes else "Document each run, challenge condition, and objective evidence for pass/fail decisions." }}

| Protocol ID | Test | Objective | Setup | Steps | Data to Record | Acceptance Criteria |
|------------|------|-----------|-------|-------|----------------|---------------------|
{% for t in OQ.tests %}
| {{ t.testId }} | {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {% for s in t.steps %}{{ s }}{% if not loop.last %}; {% endif %}{% endfor %} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not OQ.tests %}
| — | No OQ tests mapped | — | — | — | — | — |
{% endif %}

---

# Performance Qualification (PQ) Protocol

## Purpose
{{ PQ.purpose if PQ.purpose else "Verify repeatable performance under representative and worst-case production conditions." }}

## Prerequisites
{{ PQ.prerequisites if PQ.prerequisites else "OQ complete, approved load definitions, trained operators, and release criteria defined." }}

## Execution Notes
{{ PQ.executionNotes if PQ.executionNotes else "Execute planned runs with representative materials/operators and complete objective evidence capture." }}

| Protocol ID | Test | Objective | Setup | Steps | Data to Record | Acceptance Criteria |
|------------|------|-----------|-------|-------|----------------|---------------------|
{% for t in PQ.tests %}
| {{ t.testId }} | {{ t.title }} | {{ t.objective }} | {{ t.setup }} | {% for s in t.steps %}{{ s }}{% if not loop.last %}; {% endif %}{% endfor %} | {{ t.dataToRecord }} | {{ t.acceptanceCriteria }} |
{% endfor %}
{% if not PQ.tests %}
| — | No PQ tests mapped | — | — | — | — | — |
{% endif %}

---

# Traceability Matrix

| Source | Source ID | Source Title | Target Protocol | Target Test |
|--------|-----------|--------------|-----------------|-------------|
{% for row in traceabilityMatrix %}
| {{ row.sourceType }} | {{ row.sourceId }} | {{ row.sourceTitle }} | {{ row.targetProtocol }} | {{ row.targetTest }} |
{% endfor %}
{% if not traceabilityMatrix %}
| — | — | No traceability rows generated | — | — |
{% endif %}
