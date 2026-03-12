# Executable Plan: Pre-Vacuum Steam Sterilizer Scope

**Goal**: Achieve the depth and granularity needed for FDA QSR (21 CFR 820), ISO 13485, and widespread U.S. medical device industry use for the Pre-Vacuum Steam Sterilizer equipment type. The example document (AMSCO 600, wrapped trays, ISO 8, HMI with export/printout, 2 loads/day) was illustrative; naming conventions, test IDs, and specific IDs therein serve as guidance, not prescriptive requirements. Once dialed in, this will serve as the template for expanding to other equipment types.

---

## User Notes (incorporated)

- **No model field**: Equipment type should suffice; qualification-relevant equipment-specific information is selectable at other wizard points.
- **Production throughput**: Low/Medium/High is sufficient with clear descriptions/examples to help the user select.
- **Utilities**: OK as-is; research needed to ensure all qualification-relevant utilities per equipment type are present.
- **Equipment controls**: Research needed to ensure all qualification-relevant controls per equipment type are present.
- **Hazard catalog**: Research needed to ensure all qualification-relevant hazards per equipment type are present.
- **Contextual modifiers**: Research needed to ensure all qualification-relevant modifiers per equipment are present.
- **Example document**: Purely illustrative; naming, test IDs, and other specific IDs are guidance only.

---

## 1. Gap Analysis: Example Depth vs. Current State

### 1.1 User Inputs (Wizard)

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Equipment type** | `equipment.type` = Pre-Vacuum Steam Sterilizer | OK; no model field needed per user notes |
| **Throughput** | `productionThroughput` = Low/Medium/High with descriptions | OK; descriptions/examples added to help user select |
| **Load definition** (e.g., pouched instruments on wrapped trays) | hazardContext: load_type, load_config, load_density | Largely present; context options extended |
| **HMI/CSV scope** (logs cycle data, export, used for release) | Equipment controls added | CTRL_STER_PV_002b, 002c; hazard context hmiUsedForRelease |
| **Cleanroom class** | Present | OK |
| **Product contact** | Present | OK |
| **Utilities** | Present (multi-select) | Need verification evidence fields? Or OK as-is |
| **Equipment controls** (BI program, Bowie-Dick, thermocouple mapping, etc.) | Present via equipment_controls_catalog | May need more granular options for STER_PV |
| **FAT/SAT availability** | Not captured | New contextual modifier |

### 1.2 Hazard Catalog (Hazcat)

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Hazard list** | H_STER_PV_001–005, H_DATA_001 in hazcat | Phase 1 complete: H_STER_PV_003 (sensor drift), 004 (residual moisture), 005 (operator burn), H_DATA_001 (data integrity) added |
| **hazardousSituation** | Not in hazcat; only `definition` | Add `hazardousSituation` and `harm` per hazard |
| **Contextual modifiers** | hazard_context_options extended | Phase 1 complete: thermocouple_mapping_available, bi_program, fat_sat_available, bowie_dick_testing, hmi_used_for_release, etc. |
| **recommendedControls_and_tests** | Ruleset maps ruleId→IQ/OQ/PQ | Expand to include engineering/administrative/monitoring controls and explicit test IDs |

### 1.3 Risk Calculations

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Formulas** | Same (Raw, Adjusted, Residual) | OK |
| **Policy escalations** | productContact + Catastrophic → ×10 | Present |
| **HMI/data escalation** | HMI used for release → ×2 | **Missing**; add for H_DATA_001 |
| **residualRiskDecision** with recommendation text | Not produced | Add per-hazard recommendation in engine or template |

### 1.4 IQ Protocol

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Structured checklist** | Generic "Installation verification", "Utilities verification", etc. | Need **STER_PV-specific** IQ checklist: IQ-MECH-01/02, IQ-UTIL-01–06, IQ-SENS-01–03, IQ-SAF-01–03, IQ-HMI-01–05, IQ-DOC-01/02, IQ-SPARE-01, IQ-ENV-01/02, IQ-CAL-01, IQ-TRAIN-01, IQ-TRACE-01, IQ-REVIEW-01, IQ-COMMS-01 |
| **Fields per item** | Item text only | Need: ItemID, Category, Description, Expected, Measured, EvidenceFileName, Result, Owner, SignoffDate |
| **Evidence naming convention** | None | Add template: SITE_EQUIPID_TESTID_YYYYMMDD_HHMM.ext |

### 1.5 OQ Protocol

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Test scripts** | Langmap has title, objective, setup, steps; ruleset provides test IDs | Need **full scripts** per testID: OQ_BD_01, OQ_MAP_01, OQ_VAC_01, OQ_STEAM_01, OQ_SENS_01, OQ_CTRL_01, OQ_HMI_01, OQ_BI_01 |
| **Data to record, acceptance criteria, evidence files** | Partially in langmap | Expand langmap to include dataToRecord, acceptanceCriteria, evidenceFiles, roles, estimatedDuration |
| **CSV/HMI tests** | Not present | Add CSV_OQ_01–04, CSV_PQ_01 with full scripts (export integrity, printout match, audit trail, backup/restore) |

### 1.6 PQ Protocol

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Worst-case load definition** | Empty string | Populate from hazard context (e.g., "Full wrapped tray loads with pouched instruments") |
| **BI placement matrix** | Empty | Add template: 12 BIs per cycle, placement description per BI |
| **PQ cycles** | Fixed 3 | OK |
| **Acceptance criteria** | Generic | Add: "All BIs no growth; OQ parameters met per cycle" |
| **PQ worksheet template** | None | Add CSV template for BI placement and incubation log |

### 1.7 Output Documents

| Example Expectation | Current State | Gap |
|--------------------|---------------|-----|
| **Risk Management File / FMEA table** | Impact assessment in template | Expand to full FMEA: hazardousSituation, harm, contextualModifiers (structured), calculations with escalation, recommendedControls, residualRiskDecision |
| **IQ checklist CSV** | None | Generate CSV with ItemID, Category, Description, Expected, EvidenceFileName, etc. |
| **OQ test scripts** | OQ tests from langmap | Ensure each test has full script (objective, preconditions, steps, data, acceptance, evidence) |
| **PQ worksheets** | None | Generate PQ worksheet and BI incubation log CSV templates |
| **Traceability matrix** | hazard→test IDs in draft | Formalize: Hazard | Control | IQ/OQ/PQ Test ID | Acceptance | Role |

---

## 2. Phase 1: Data and Schema (Pre-Vacuum Steam Sterilizer Only)

### 2.1 New/Modified Data Files

| File | Action |
|------|--------|
| `data/prevacuum_sterilizer/` (new folder) | Create scope-limited data for STER_PV |
| `data/prevacuum_sterilizer/hazards_ster_pv.json` | Full hazard set: H_STER_PV_001–005, H_DATA_001 with hazardousSituation, harm, contextualModifiers schema |
| `data/prevacuum_sterilizer/hazard_context_options_ster_pv.json` | Enhanced context: loadType, loadConfig, loadDensity, thermocoupleMappingAvailable, BIProgram, FAT_SAT, throughput_per_day, hmiUsedForRelease |
| `data/prevacuum_sterilizer/equipment_controls_ster_pv.json` | STER_PV equipment controls (may extend equipment_controls_catalog) |
| `data/prevacuum_sterilizer/iq_checklist_ster_pv.json` | Full IQ checklist with ItemID, Category, Description, Expected, EvidenceFileName, Owner |
| `rules/langmap_ster_pv_comprehensive.json` | OQ/CSV test scripts: OQ_BD_01, OQ_MAP_01, OQ_VAC_01, OQ_STEAM_01, OQ_SENS_01, OQ_CTRL_01, OQ_HMI_01, OQ_BI_01, CSV_OQ_01–04, CSV_PQ_01 with full fields |
| `data/prevacuum_sterilizer/pq_templates_ster_pv.json` | BI placement matrix template, worst-case load definition template, PQ worksheet CSV headers |

### 2.2 Engine Changes

| Component | Change |
|-----------|--------|
| `engine/engine_core.py` | When equipmentTypeId == STER_PV_AUT, load STER_PV-specific hazards and IQ checklist from prevacuum_sterilizer |
| `engine/risk_adjustments.py` | Add HMI escalation: if hmiUsedForRelease and hazardId == H_DATA_001, multiply ResidualRisk by 2 |
| `engine/rules_executor.py` | For STER_PV: apply STER_PV IQ checklist (from iq_checklist_ster_pv.json), populate PQ.worstCaseLoadDefinition from hazard context, populate PQ.biologicalIndicatorPlacement from template |
| `engine/calculator.py` | No change (formulas already match) |

### 2.3 Payload / API

| Field | Action |
|-------|--------|
| `equipment.model` | Add to payload (e.g., "AMSCO 600"); optional, user-entered |
| `siteContext.throughputCyclesPerDay` | Add (optional number) when productionThroughput is Medium/High |
| `siteContext.hmiUsedForRelease` | Add boolean |
| `siteContext.hmiExportsData` | Add boolean |

---

## 3. Phase 2: Frontend (Pre-Vacuum Steam Sterilizer Only)

### 3.1 Wizard Additions

| Step | Change |
|------|--------|
| Equipment Type | When STER_PV selected, show optional "Equipment model" text field (e.g., AMSCO 600) |
| Site / Throughput | Add optional "Cycles per day" (number) or refine throughput options |
| Site | Add "HMI used for release decisions" checkbox, "HMI exports cycle data" checkbox |
| Hazards | Ensure hazard context shows: load types (multi-select), load config, load density, thermocouple mapping (Y/N), BI program (Y/N), FAT/SAT (Y/N) for STER_PV hazards |

### 3.2 Conditional Logic

- If `hmiUsedForRelease` = true → include H_DATA_001 in hazard list and include CSV tests in OQ
- If equipment type = STER_PV → use STER_PV-specific IQ checklist and PQ templates

---

## 4. Phase 3: Template and Output (Generated Draft)

### 4.1 Risk / FMEA Section

- Per hazard: hazardId, title, hazardousSituation, harm, contextualModifiers (formatted)
- Scoring: all five dimensions with label and numeric
- Calculations: RawRisk, AdjustedRisk, ResidualRisk, escalation_applied, escalation_reason
- recommendedControls: engineering, administrative, monitoring
- IQ_OQ_PQ_testIDs: list
- residualRiskDecision: RRI_contribution, recommendation, qualificationBandSuggested

### 4.2 IQ Section

- Structured table: ItemID | Category | Description | Expected | Measured | EvidenceFileName | Result | Owner | SignoffDate
- Use STER_PV IQ checklist from data
- Include evidence naming convention template: SITE_EQUIPID_TESTID_YYYYMMDD_HHMM.ext

### 4.3 OQ Section

- One subsection per testID
- Each: TestID | Title | Objective | Preconditions | Steps | Data to Record | Acceptance Criteria | Evidence Files | Roles | Duration
- Include CSV tests when hmiUsedForRelease = true

### 4.4 PQ Section

- Worst-case load definition (from hazard context)
- BI placement matrix (12 BIs template)
- Number of cycles: 3
- Acceptance: primary (zero BI growth), secondary (OQ parameters met)
- PQ worksheet CSV template (headers)

### 4.5 Artifacts

- **IQ checklist CSV**: Generate downloadable CSV with full IQ items
- **PQ worksheet CSV**: Generate template for BI placement and incubation log
- **Traceability matrix**: Hazard | Control | Test ID | Acceptance | Role

---

## 5. Execution Order

### Phase 1: Data Foundation (COMPLETED)

1. ~~Create `data/prevacuum_sterilizer/` folder~~ — Not needed; updates applied to main data files.
2. ~~Add hazards~~ — Hazards H_STER_PV_003, 004, 005, H_DATA_001 added to `hazcat_v1.1_equipment_types - comprehensive.json`.
3. ~~Add IQ checklist~~ — Created `data/iq_checklists.json` with full STER_PV checklist (IQ_MECH_01, IQ_UTIL_01–06, IQ_SENS_01–03, IQ_SAF_01–03, IQ_HMI_01–05, IQ_DOC_01–02, IQ_SITE_01–02, IQ_CAL_01, IQ_TRAIN_01, IQ_TRACE_01, IQ_REV_01).
4. ~~Extend hazard_context_options~~ — Added thermocouple_mapping_available, bi_program, fat_sat_available, bowie_dick_testing, hmi_used_for_release, hmi_exports_data, etc. for all STER_PV hazards.
5. ~~Extend langmap~~ — Added CSV export integrity, printout vs export, CSV backup restore, HMI functions and data export to `hazard_to_language_map_v1 - comprehensive.json`.
6. Throughput descriptions — Added cycle/day examples to `site_context_metadata.json` productionThroughput options.
7. Utilities — Added Cooling Water and Instrument Air to STER_PV `equipment_metadata.json` utilityDescriptors.
8. Equipment controls — Added CTRL_STER_PV_002b (HMI used for release), CTRL_STER_PV_002c (HMI exports data) to `equipment_controls_catalog.json`.

### Phase 2: Engine Wiring (COMPLETED)

6. ~~Add STER_PV branch~~ — equipmentTypeId passed via vector; engine_core already receives it.
7. ~~Add H_DATA_001 and CSV tests~~ — ruleset rule for R_DATA_001 adds CSV OQ/IQ/PQ when qualificationBand Targeted/Full.
8. ~~Add HMI escalation~~ — apply_policy_escalations: H_DATA_001 ×2 when hmiUsedForRelease (from equipmentControls.CTRL_STER_PV_002b or siteContext.hmiUsedForRelease).
9. ~~Update rules_executor~~ — for STER_PV: load iq_checklists.json for full IQ checklist; _build_pq_worst_case_load, _build_pq_bi_placement, _build_pq_acceptance_criteria populate PQ; _build_csv_guidance and _build_evidence_list when hmiUsedForRelease.

### Phase 3: Template and Render (COMPLETED)

10. ~~Update template~~ — FMEA summary table, IQ structured table (when checklistItems present), evidence naming convention, PQ BI placement matrix (12 BIs template), traceability matrix.
11. ~~Add CSV export~~ — IQ_checklist.csv (structured items when STER_PV), PQ_worksheet.csv (BI placement template for sterilizers).

### Step 4: Frontend

12. Add equipment model (optional), throughput cycles/day (optional), hmiUsedForRelease, hmiExportsData.
13. Ensure hazard context UI shows all STER_PV modifiers.

### Step 5: Validation

14. Run end-to-end: STER_PV, AMSCO 600, ISO 8, wrapped trays, 2 loads/day, product contact, HMI for release.
15. Compare output to example document; iterate until acceptable.

---

## 6. File Inventory for Pre-Vacuum Scope

### New Files to Create

```
data/prevacuum_sterilizer/
  hazards_ster_pv.json          # H_STER_PV_001-005, H_DATA_001
  iq_checklist_ster_pv.json     # Full IQ checklist
  hazard_context_options_ster_pv.json  # Enhanced context (or extend hazard_context_options)
  pq_templates_ster_pv.json     # BI matrix, worst-case load template

rules/
  langmap_ster_pv_comprehensive.json   # OQ + CSV test scripts
```

### Files to Modify

```
data/hazcat_v1.1_equipment_types - comprehensive.json  # Add H_STER_PV_004, 005, H_DATA_001 OR use prevacuum subset
data/hazard_context_options.json                       # Add STER_PV modifiers
engine/engine_core.py
engine/risk_adjustments.py
engine/rules_executor.py
engine/render_engine.py
templates/human_readable_template_markdown_v1.md
public/index.html
api/generate.py
```

---

## 7. Out-of-Scope for Phase 1

- Other equipment types (Sterilizer only)
- Excel/DOCX export of IQ checklist (CSV first)
- Full validation of numeric formulas (assume current formulas are correct)
- Traceability matrix as separate artifact (can be in draft first)

---

## 8. Success Criteria

1. **User can enter**: Equipment type STER_PV, model (e.g., AMSCO 600), ISO 8, wrapped trays/pouched instruments, 2 loads/day, product contact, HMI for release, equipment controls (BI, Bowie-Dick, etc.).
2. **Generated draft includes**:
   - FMEA-style hazard table with hazardousSituation, harm, modifiers, calculations, escalation, recommendation
   - Full IQ checklist (25+ items) with ItemID, Category, Expected, EvidenceFileName, Owner
   - Full OQ test scripts (OQ_BD_01, OQ_MAP_01, OQ_VAC_01, OQ_STEAM_01, OQ_SENS_01, OQ_CTRL_01, OQ_HMI_01, OQ_BI_01) plus CSV_OQ_01–04 when HMI for release
   - PQ with worst-case load definition, BI placement matrix (12 BIs), acceptance criteria
   - Downloadable IQ checklist CSV and PQ worksheet CSV template
3. **Traceability**: Each hazard maps to IQ/OQ/PQ test IDs; test IDs resolve to full script content.

---

## Appendix A: Example Content for Data Population

Use these as reference when populating the STER_PV data files.

### A.1 Hazard IDs and Titles

| hazardId      | title                                              |
|---------------|----------------------------------------------------|
| H_STER_PV_001 | Sterility failure (cold spots)                     |
| H_STER_PV_002 | Inadequate air removal / non-condensable gases     |
| H_STER_PV_003 | Sensor drift / inaccurate temperature/pressure     |
| H_STER_PV_004 | Residual sterilant or moisture on product          |
| H_STER_PV_005 | Operator burn / steam release                      |
| H_DATA_001    | Data integrity (HMI export/printout incorrect)     |

### A.2 IQ Checklist Items (by Category)

| ItemID     | Category   | Description (short)                                      |
|------------|------------|----------------------------------------------------------|
| IQ-MECH-01 | Mechanical | Equipment received per spec; no damage                   |
| IQ-MECH-02 | Mechanical | Installed per supplier DQ; correct orientation           |
| IQ-UTIL-01 | Utilities  | Steam supply; pressure, dryness verified                 |
| IQ-UTIL-02 | Utilities  | Vacuum source; capacity verified                         |
| IQ-UTIL-03 | Utilities  | Electrical supply; voltage, grounding                    |
| IQ-UTIL-04 | Utilities  | Instrument air (if applicable)                           |
| IQ-UTIL-05 | Utilities  | Cooling water (if applicable)                            |
| IQ-UTIL-06 | Utilities  | Drain system; verified                                   |
| IQ-SENS-01 | Sensors    | Temperature sensors; specs verified                      |
| IQ-SENS-02 | Sensors    | Pressure sensors; specs verified                         |
| IQ-SENS-03 | Sensors    | Vacuum sensors; specs verified                           |
| IQ-SAF-01  | Safety     | Safety interlocks; door, pressure relief                 |
| IQ-SAF-02  | Safety     | Over-temperature / over-pressure alarms                  |
| IQ-SAF-03  | Safety     | Emergency stop; verified                                 |
| IQ-HMI-01  | HMI        | HMI displays; screens per spec                           |
| IQ-HMI-02  | HMI        | Cycle selection; programs available                      |
| IQ-HMI-03  | HMI        | Data logging; export and printout capability             |
| IQ-HMI-04  | HMI        | Audit trail; enabled, tamper-evident                     |
| IQ-HMI-05  | HMI        | Backup/restore; procedure documented                     |
| IQ-DOC-01  | Documentation | Manuals, drawings, calibration certs               |
| IQ-DOC-02  | Documentation | SOPs drafted; calibration schedule                  |
| IQ-SPARE-01| Site       | Spare parts list; critical spares identified             |
| IQ-ENV-01  | Site       | Room conditions; adequate clearance, ventilation         |
| IQ-ENV-02  | Site       | Utilities connections; labeled, traceable                |
| IQ-CAL-01  | Tools      | Calibration; TCs, pressure gauges within cal             |
| IQ-TRAIN-01| Training   | Operators trained on SOPs                                |
| IQ-TRACE-01| Traceability | Equipment ID, serial; traceability to asset registry |
| IQ-REVIEW-01| Review    | DQ/FAT/SAT reviewed; deviations closed                   |
| IQ-COMMS-01| Review    | Supplier communications; escalation path                 |

### A.3 OQ Test IDs and Titles

| TestID   | Title                           |
|----------|---------------------------------|
| OQ_BD_01 | Bowie-Dick / air removal test   |
| OQ_MAP_01| Thermocouple mapping            |
| OQ_VAC_01| Vacuum rate / hold              |
| OQ_STEAM_01 | Steam penetration / equilibration |
| OQ_SENS_01 | Sensor accuracy / response    |
| OQ_CTRL_01 | Controller interlocks / alarms |
| OQ_HMI_01 | HMI functions; cycle run, data export |
| OQ_BI_01 | Biological indicator (BI) challenge |

### A.4 CSV/HMI Test IDs (when hmiUsedForRelease = true)

| TestID   | Title                                      |
|----------|--------------------------------------------|
| CSV_OQ_01| CSV export integrity; format, checksum     |
| CSV_OQ_02| Printout vs export; data match             |
| CSV_OQ_03| Audit trail; tamper test, sequence         |
| CSV_OQ_04| Backup/restore; data recovery              |
| CSV_PQ_01| PQ CSV/printout verification               |

### A.5 Evidence Naming Convention

```
SITE_EQUIPID_TESTID_YYYYMMDD_HHMM.ext
Example: SITE_AMSCO600_IQ_MECH01_20250309_1430.pdf
```

---

*This plan is designed to be executed incrementally. Each step can be implemented and tested before proceeding.*
