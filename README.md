# getIQOQPQ

Repository for deterministic IQ/OQ/PQ advisory package generation.

Run the pipeline:
1. Create venv and install: python -m venv .venv; .\.venv\Scripts\Activate; pip install -r requirements.txt
2. Validate: python engine/schema_validator.py data/hazcat_v1.1_equipment_types.json
3. Dry run: python engine/engine_core.py --mode dryrun --vectors data/unit_test_vectors_v1.json --output artifacts/dryrun
4. Render: python engine/render_engine.py <package.json> templates/human_readable_template_markdown_v1.md rules/hazard_to_language_map_v1.json artifacts/dryrun/rendered
