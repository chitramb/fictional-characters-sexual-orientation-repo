"""Regression tests for neutral Fandom discovery and explicit-only identity parsing."""
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from src.fandom_universes import _character_categories, _orientation
from src.merge_candidates import merge
from src.audit_candidates import audit


class FandomOrientationTests(unittest.TestCase):
    def test_explicit_infobox_orientation_is_extracted(self):
        value, reason = _orientation(
            "{{Character\n| name = Example\n| sexuality = Bisexual\n| occupation = Pilot\n}}"
        )
        self.assertEqual(value, "bisexual")
        self.assertIn("explicitly gives", reason)

    def test_orientation_in_plot_text_is_not_extracted(self):
        value, _ = _orientation(
            "The story mentions a gay activist, but no orientation infobox field exists."
        )
        self.assertEqual(value, "Not stated")

    def test_negative_explicit_field_is_not_misclassified(self):
        value, _ = _orientation("{{Character\n| sexuality = Not gay\n| age = 30\n}}")
        self.assertEqual(value, "Not stated")

    def test_general_character_categories_exclude_identity_directories(self):
        payload = {
            "query": {
                "allcategories": [
                    {"category": "Characters", "size": 50},
                    {"category": "Bisexual characters", "size": 500},
                    {"category": "Genderqueer characters", "size": 450},
                    {"category": "Characters by sexual orientation", "size": 420},
                    {"category": "Minor characters", "size": 400},
                    {"category": "Female characters", "size": 300},
                ]
            }
        }
        response = Mock()
        response.json.return_value = payload
        response.status_code = 200
        response.raise_for_status.return_value = None
        session = Mock()
        session.get.return_value = response
        categories = _character_categories(session, "https://example.fandom.com/api.php")
        self.assertIn("Characters", categories)
        self.assertIn("Minor characters", categories)
        self.assertIn("Female characters", categories)
        self.assertNotIn("Bisexual characters", categories)
        self.assertNotIn("Genderqueer characters", categories)
        self.assertNotIn("Characters by sexual orientation", categories)


class MergeSemanticsTests(unittest.TestCase):
    def test_p21_semantics_and_explicit_gender_identity_remain_separate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            row = {
                "character": "Example Character",
                "work": "Example Work",
                "medium": "Book",
                "orientation": "Not stated",
                "sex_or_gender": "female",
                "gender_identity": "Not stated",
                "source": "https://www.wikidata.org/wiki/Q123",
                "source_id": "Q123",
                "source_name": "Wikidata",
                "source_revision_id": 456,
                "source_revision_timestamp": "2026-01-01T00:00:00Z",
                "evidence_status": "candidate",
            }
            (root / "wikidata_character_candidates.jsonl").write_text(
                json.dumps(row) + "\n", encoding="utf-8"
            )
            summary = merge(root)
            merged = json.loads((root / "all_character_candidates.jsonl").read_text(encoding="utf-8"))
            self.assertEqual(merged["sex_or_gender"], "female")
            self.assertEqual(merged["gender_identity"], "Not stated")
            self.assertEqual(merged["sources"][0]["source_revision_id"], 456)
            self.assertEqual(summary["records_with_sex_or_gender_value"], 1)
            self.assertEqual(summary["records_with_explicit_gender_identity"], 0)


class CandidateAuditTests(unittest.TestCase):
    def test_duplicate_names_are_flagged_not_collapsed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            rows = [
                {"character": "Alex", "work": "Universe A", "work_scope": "universe",
                 "orientation": "Not stated", "sex_or_gender": "Not stated",
                 "gender_identity": "Not stated", "sources": [{"source_name": "Fandom:A"}]},
                {"character": " Alex ", "work": "Universe B", "work_scope": "universe",
                 "orientation": "Not stated", "sex_or_gender": "Not stated",
                 "gender_identity": "Not stated", "sources": [{"source_name": "Fandom:B"}]},
            ]
            source = root / "dictionary.jsonl"
            source.write_text("".join(json.dumps(row) + "\n" for row in rows), encoding="utf-8")
            report = audit(source, root / "quality_audit.json")
            self.assertEqual(report["candidate_records"], 2)
            self.assertEqual(report["distinct_normalized_character_names"], 1)
            self.assertEqual(report["duplicate_name_groups_not_automatically_merged"], 1)
            self.assertEqual(report["same_name_across_multiple_work_or_universe_labels"], 1)


if __name__ == "__main__":
    unittest.main()
