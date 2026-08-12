import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from grantcompass.score import gpa_fit, keyword_match_score, score_record  # noqa: E402


class TestGpaFit(unittest.TestCase):
    def test_meets_minimum_daad(self):
        self.assertEqual(gpa_fit(3.6, 4.0, "DAAD Scholarship Database"), "meets_minimum")

    def test_below_minimum_erasmus(self):
        # normalized 2.4/4.0 vs Erasmus Mundus typical minimum 3.0
        self.assertEqual(gpa_fit(2.4, 4.0, "Erasmus Mundus Joint Masters Catalogue"), "below_typical_minimum")

    def test_borderline_default(self):
        # normalized 2.9/4.0 vs default minimum 3.0, within 0.15 margin
        self.assertEqual(gpa_fit(2.9, 4.0, "some unknown source"), "borderline")

    def test_scale_normalization(self):
        # 3.5/5.0 normalizes to 2.8/4.0 -> below Erasmus Mundus 3.0 minimum, outside borderline margin
        self.assertEqual(gpa_fit(3.5, 5.0, "MSCA Doctoral Networks"), "below_typical_minimum")


class TestKeywordMatch(unittest.TestCase):
    def test_full_match(self):
        score = keyword_match_score("Robotics and Embedded Systems Lab", ["robotics", "embedded systems"])
        self.assertEqual(score, 1.0)

    def test_partial_match(self):
        score = keyword_match_score("Robotics Lab", ["robotics", "quantum computing"])
        self.assertEqual(score, 0.5)

    def test_no_keywords(self):
        self.assertEqual(keyword_match_score("anything", []), 0.0)

    def test_no_match(self):
        self.assertEqual(keyword_match_score("Marine Biology Dept", ["robotics"]), 0.0)


class TestScoreRecord(unittest.TestCase):
    def test_sort_key_prefers_gpa_fit_over_match(self):
        applicant = {"gpa": 3.6, "gpa_scale": 4.0, "field_keywords": ["robotics"]}
        good_fit_low_match = score_record(
            {"name": "Prof A", "institution": "TU Delft"}, applicant, "DAAD Scholarship Database"
        )
        bad_fit_high_match = score_record(
            {"name": "Robotics Prof B", "institution": "Robotics Institute"}, applicant, "Erasmus Mundus Joint Masters Catalogue"
        )
        # bad_fit uses a GPA well below Erasmus Mundus min via a second applicant
        low_gpa_applicant = {"gpa": 2.0, "gpa_scale": 4.0, "field_keywords": ["robotics"]}
        bad_fit_high_match = score_record(
            {"name": "Robotics Prof B", "institution": "Robotics Institute"}, low_gpa_applicant, "Erasmus Mundus Joint Masters Catalogue"
        )
        self.assertGreater(good_fit_low_match["sort_key"], bad_fit_high_match["sort_key"])


if __name__ == "__main__":
    unittest.main()
