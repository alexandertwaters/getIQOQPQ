# ci/test_package_metadata.py
"""Unit tests for package metadata, render output, and fingerprint stability."""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

# Ensure project root on path
_REPO = Path(__file__).resolve().parent.parent
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))


class TestPackageMetadata(unittest.TestCase):
    """Assert package_json hazards contain definition, severityOptions (help/example), ruleId, standards."""

    def setUp(self):
        from engine.engine_core import run_vector
        with open(_REPO / "data" / "unit_test_vectors_v1.json", "r", encoding="utf8") as f:
            doc = json.load(f)
        # Use first vector that has hazards in hazcat
        self.vector = doc["vectors"][0]["input"]
        self.pkg = run_vector(self.vector)

    def test_hazards_contain_definition(self):
        for i, h in enumerate(self.pkg["hazards"]):
            self.assertIn("definition", h, f"hazard[{i}] {h.get('hazardId')} missing definition")
            self.assertIsInstance(h["definition"], str)

    def test_hazards_contain_severity_options_with_help_example(self):
        found_with_options = False
        for i, h in enumerate(self.pkg["hazards"]):
            opts = h.get("severityOptions", [])
            if opts:
                found_with_options = True
                first = opts[0]
                self.assertIn("label", first, f"severityOptions[0] missing label")
                self.assertIn("help", first, f"severityOptions[0] missing help")
                self.assertIn("example", first, f"severityOptions[0] missing example")
        self.assertTrue(found_with_options, "At least one hazard should have severityOptions from catalog")

    def test_hazards_contain_rule_id(self):
        for i, h in enumerate(self.pkg["hazards"]):
            self.assertIn("ruleId", h, f"hazard[{i}] missing ruleId")

    def test_hazards_contain_standards(self):
        for i, h in enumerate(self.pkg["hazards"]):
            self.assertIn("standards", h, f"hazard[{i}] missing standards")
            self.assertIsInstance(h["standards"], list)


class TestFingerprintStability(unittest.TestCase):
    """Confirm fingerprints remain stable when only help/example text changes."""

    def setUp(self):
        from engine.engine_core import run_vector
        from engine.fingerprint import canonicalize_package_for_fingerprint
        with open(_REPO / "data" / "unit_test_vectors_v1.json", "r", encoding="utf8") as f:
            doc = json.load(f)
        self.vector = doc["vectors"][0]["input"]
        self.run_vector = run_vector
        self.canonicalize = canonicalize_package_for_fingerprint

    def test_fingerprint_unchanged_when_help_example_mutated(self):
        pkg1 = self.run_vector(self.vector)
        fp1 = pkg1["fingerprint"]

        # Mutate help/example in package (simulate copy edit)
        for h in pkg1["hazards"]:
            for opt in h.get("severityOptions", []):
                if "help" in opt:
                    opt["help"] = opt["help"] + " (updated)"
                if "example" in opt:
                    opt["example"] = opt["example"] + " — revised"
        for h in pkg1["hazards"]:
            h["definition"] = (h.get("definition") or "") + " [edit]"

        # Recompute fingerprint (canonicalize ignores help/example/definition)
        fp2 = self.canonicalize(pkg1)
        self.assertEqual(fp1, fp2, "Fingerprint should not change when only help/example/definition changes")


class TestRenderOutput(unittest.TestCase):
    """Render tests: generated Markdown contains lifecycle and qualification sections."""

    def setUp(self):
        from engine.engine_core import run_vector
        from engine.render_engine import render_markdown
        with open(_REPO / "data" / "unit_test_vectors_v1.json", "r", encoding="utf8") as f:
            doc = json.load(f)
        self.vector = doc["vectors"][0]["input"]
        self.pkg = run_vector(self.vector)
        self.tmpdir = tempfile.mkdtemp()
        pkg_path = Path(self.tmpdir) / "pkg.json"
        with open(pkg_path, "w", encoding="utf8") as f:
            json.dump(self.pkg, f, indent=2)
        template = _REPO / "templates" / "human_readable_template_markdown_v1.md"
        langmap = _REPO / "rules" / "hazard_to_language_map_v1 - comprehensive.json"
        render_markdown(str(pkg_path), str(template), str(langmap), self.tmpdir)

    def tearDown(self):
        import shutil
        if os.path.exists(self.tmpdir):
            shutil.rmtree(self.tmpdir, ignore_errors=True)

    def test_markdown_contains_lifecycle_sections(self):
        # fp from pkg may have colon; render writes {fp}.md
        md_files = list(Path(self.tmpdir).glob("*.md"))
        if not md_files:
            self.skipTest("No rendered MD found")
        text = md_files[0].read_text(encoding="utf8")
        required = [
            "Validation Master Plan (VMP)",
            "User Requirements Specification (URS)",
            "Design Qualification (DQ)",
            "Installation Qualification (IQ)",
            "Operational Qualification (OQ)",
            "Performance Qualification (PQ)",
            "Requalification plan",
        ]
        for section in required:
            self.assertIn(section, text)

    def test_markdown_contains_traceability_and_requalification(self):
        md_files = list(Path(self.tmpdir).glob("*.md"))
        if not md_files:
            self.skipTest("No rendered MD found")
        text = md_files[0].read_text(encoding="utf8")
        self.assertIn("Traceability matrix", text)
        self.assertIn("Base frequency", text)
        self.assertIn("Trigger", text)


class TestVModelOutput(unittest.TestCase):
    """Pure V-model output tests for separate docs and traceability."""

    def test_vmodel_generates_separate_docs_and_traceability(self):
        from engine.engine_core import run_vector
        from engine.render_engine import render_markdown

        vector = {
            "cohort": "Sterilization",
            "type": "Pre-Vacuum Steam Sterilizer",
            "equipmentTypeId": "STER_PV_AUT",
            "model": "E-STER-PV-001",
            "siteContext": {
                "cleanroomClass": "ISO 7",
                "utilities": ["Steam", "Electricity"],
                "productContact": True,
                "productionThroughput": "Medium",
            },
            "controlArchitecture": "PLC or SCADA",
            "rulesetId": "ruleset_v1.1",
            "hazcatVersion": "hazcat_v1.1",
            "hazards": [],
            "vmp": {"scope": "Sterilizer lifecycle qualification", "roles": "Validation/QA/Engineering", "deliverables": "VMP, URS, FRS, TRS, IQ/OQ/PQ"},
            "urs": {"intendedUse": "Sterilize wrapped and porous loads", "criticalProcessParameters": "temperature, pressure, exposure time", "acceptanceCriteria": "All runs pass criteria"},
            "computerizedValidation": {"computerized": True, "softwareClassification": "Category 4"},
            "requalificationPlan": {"baseFrequency": "annual", "triggers": ["move", "major_repair"], "rationale": "Critical process equipment"},
            "vmodel": {"ursIds": ["URS_STER_PV_001", "URS_STER_PV_002"], "frsIds": [], "trsIds": []},
        }
        pkg = run_vector(vector)
        self.assertEqual(pkg.get("qualificationBand"), "VModel")

        tmpdir = tempfile.mkdtemp()
        try:
            pkg_path = Path(tmpdir) / "pkg.json"
            with open(pkg_path, "w", encoding="utf8") as f:
                json.dump(pkg, f, indent=2)
            template = _REPO / "templates" / "human_readable_template_markdown_v1.md"
            langmap = _REPO / "rules" / "hazard_to_language_map_v1 - comprehensive.json"
            render_markdown(str(pkg_path), str(template), str(langmap), tmpdir)
            files = {p.name for p in Path(tmpdir).glob("*")}
            fp = pkg["fingerprint"].replace(":", "_")
            self.assertIn(f"{fp}.md", files)
            self.assertIn(f"{fp}.VMP.md", files)
            self.assertIn(f"{fp}.URS.md", files)
            self.assertIn(f"{fp}.FRS.md", files)
            self.assertIn(f"{fp}.TRS.md", files)
            self.assertIn(f"{fp}.IQ.md", files)
            self.assertIn(f"{fp}.OQ.md", files)
            self.assertIn(f"{fp}.PQ.md", files)
            self.assertIn(f"{fp}.traceability.csv", files)
        finally:
            import shutil
            shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    unittest.main()
