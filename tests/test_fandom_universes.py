"""Regression tests for neutral Fandom discovery and explicit-only identity parsing."""
import unittest
from unittest.mock import Mock

from src.fandom_universes import _character_categories, _orientation


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


if __name__ == "__main__":
    unittest.main()
