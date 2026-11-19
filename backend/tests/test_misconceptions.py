
import unittest

from app.cognitive_engine.misconceptions import (
    MisconceptionRule,
    DiagnosticQuestion,
    MisconceptionDetector,
)


class TestMisconceptionDetector(unittest.TestCase):

    def setUp(self):
        self.detector = MisconceptionDetector()

        question = DiagnosticQuestion(
            question_id="ALG001",
            concept_id="linear_equations",
            correct_option_id="B",
            misconception_rules=[
                MisconceptionRule(
                    option_id="A",
                    misconception_id="inverse_operation_error",
                    description="May have added instead of subtracting.",
                    confidence=0.85,
                ),
                MisconceptionRule(
                    option_id="C",
                    misconception_id="division_error",
                    description="May have incorrectly divided the equation.",
                    confidence=0.75,
                ),
            ],
        )

        self.detector.register_question(question)

    def test_correct_answer(self):
        result = self.detector.diagnose("ALG001", "B")
        self.assertTrue(result["is_correct"])
        self.assertIsNone(result["diagnosis"])

    def test_mapped_misconception(self):
        result = self.detector.diagnose("ALG001", "A")
        self.assertFalse(result["is_correct"])
        self.assertEqual(
            result["diagnosis"],
            "inverse_operation_error"
        )

    def test_another_mapped_misconception(self):
        result = self.detector.diagnose("ALG001", "C")
        self.assertEqual(
            result["diagnosis"],
            "division_error"
        )

    def test_unknown_wrong_answer_is_not_guessed(self):
        result = self.detector.diagnose("ALG001", "D")
        self.assertFalse(result["is_correct"])
        self.assertIsNone(result["diagnosis"])

    def test_unknown_question_is_rejected(self):
        with self.assertRaises(ValueError):
            self.detector.diagnose("UNKNOWN", "A")

    def test_duplicate_question_is_rejected(self):
        question = DiagnosticQuestion(
            question_id="ALG001",
            concept_id="linear_equations",
            correct_option_id="B",
            misconception_rules=[],
        )

        with self.assertRaises(ValueError):
            self.detector.register_question(question)

    def test_duplicate_option_rules_are_rejected(self):
        question = DiagnosticQuestion(
            question_id="ALG002",
            concept_id="linear_equations",
            correct_option_id="C",
            misconception_rules=[
                MisconceptionRule("A", "error_one", "First error"),
                MisconceptionRule("A", "error_two", "Second error"),
            ],
        )

        with self.assertRaises(ValueError):
            self.detector.register_question(question)

    def test_invalid_confidence_is_rejected(self):
        question = DiagnosticQuestion(
            question_id="ALG003",
            concept_id="linear_equations",
            correct_option_id="B",
            misconception_rules=[
                MisconceptionRule(
                    "A", "error_one", "Invalid confidence", 1.5
                ),
            ],
        )

        with self.assertRaises(ValueError):
            self.detector.register_question(question)


if __name__ == "__main__":
    unittest.main()

