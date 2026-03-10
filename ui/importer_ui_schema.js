// ui/importer_ui_schema.js
// Reads data/ui_wiring_schema_v1.1.json and writes discrete UI stepper component JSON files
// Usage: node ui/importer_ui_schema.js
// Output: ui/stepper_components/entry_screen.json
//         ui/stepper_components/hazard_stepper.json
//         ui/stepper_components/review_screen.json

const fs = require('fs');
const path = require('path');

const REPO_ROOT = path.resolve(__dirname, '..');
const DATA_DIR = path.join(REPO_ROOT, 'data');
const UI_DIR = path.join(REPO_ROOT, 'ui');
const OUT_DIR = path.join(UI_DIR, 'stepper_components');

function readJson(filePath) {
  const raw = fs.readFileSync(filePath, { encoding: 'utf8' });
  try {
    return JSON.parse(raw);
  } catch (err) {
    console.error('Failed to parse JSON:', filePath, err.message);
    process.exit(2);
  }
}

function writeJson(filePath, obj) {
  const content = JSON.stringify(obj, null, 2);
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, content, { encoding: 'utf8' });
  console.log('Wrote', filePath);
}

function main() {
  const schemaPath = path.join(DATA_DIR, 'ui_wiring_schema_v1.1.json');
  if (!fs.existsSync(schemaPath)) {
    console.error('Missing UI wiring schema at', schemaPath);
    process.exit(1);
  }
  const schema = readJson(schemaPath);
  if (!schema.uiSchemaVersion) {
    console.warn('Warning: uiSchemaVersion not present in schema');
  }
  const entry = schema.entryScreen;
  const hazardSel = schema.hazardSelectionScreen;
  const perHazard = schema.perHazardStepper;
  const review = schema.reviewScreen;

  if (!entry || !entry.fields) {
    console.error('entryScreen with fields required');
    process.exit(3);
  }
  const entryOut = { id: 'entryScreen', title: 'Equipment and Site Context', ...entry };
  writeJson(path.join(OUT_DIR, 'entry_screen.json'), entryOut);

  const hazardOut = hazardSel && perHazard
    ? { hazardSelection: hazardSel, perHazardStepper: perHazard }
    : perHazard || hazardSel || {};
  writeJson(path.join(OUT_DIR, 'hazard_stepper.json'), hazardOut);

  if (!review || typeof review !== 'object') {
    console.error('reviewScreen required');
    process.exit(4);
  }
  writeJson(path.join(OUT_DIR, 'review_screen.json'), review);

  console.log('UI importer completed successfully');
}

if (require.main === module) {
  main();
}

module.exports = { readJson, writeJson };
