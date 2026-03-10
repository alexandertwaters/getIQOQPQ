# getIQOQPQ

Repository for deterministic IQ/OQ/PQ advisory package generation.

## Run the pipeline
1. Create venv and install: `python -m venv .venv` then `.\.venv\Scripts\Activate` (Windows) and `pip install -r requirements.txt`
2. Validate: `python engine/schema_validator.py data/hazcat_v1.1_equipment_types.json`
3. Dry run: `python engine/engine_core.py --mode dryrun --vectors data/unit_test_vectors_v1.json --output artifacts/dryrun`
4. Render: `python engine/render_engine.py <package.json> templates/human_readable_template_markdown_v1.md rules/hazard_to_language_map_v1.json artifacts/dryrun/rendered`

## API (Vercel + Supabase)
- `POST /api/v1/generate` – accepts validated input JSON, returns fingerprint and artifact path
- `GET /api/v1/artifact?fingerprint=...` – returns signed URLs for JSON, MD, CSV
- `GET /api/v1/catalog/version` – returns hazcatVersion and rulesetId
- `GET /api/v1/hazards?equipmentTypeId=...` – returns hazards for equipment type
- `GET /api/v1/equipment-types` – returns cohorts and equipment types for wizard

## Deployment
1. Deploy to Vercel; set env vars: `SUPABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `ARTIFACT_BUCKET`
2. Run Supabase migrations in `supabase/migrations/`
3. Create storage bucket `artifacts` (private) in Supabase dashboard
