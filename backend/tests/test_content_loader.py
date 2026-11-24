import json
import tempfile
import unittest
from pathlib import Path

from app.content_loader import load_learning_content


class TestContentLoader(unittest.TestCase):

    def test_loads_algebra_module(self):
        content = load_learning_content()

        self.assertEqual(
            content.module_id,
            "algebra_linear_equations",
        )
        self.assertEqual(len(content.concept_graph.concepts), 3)
        self.assertEqual(len(content.questions), 9)

    def test_loads_correct_learning_path(self):
        content = load_learning_content()

        self.assertEqual(
            content.concept_graph.get_learning_path("equations"),
            ["arithmetic", "variables", "equations"],
        )

    def test_registers_all_questions_for_diagnosis(self):
        content = load_learning_content()

        self.assertEqual(
            set(content.questions),
            set(content.misconception_detector.questions),
        )

    def test_question_references_valid_concept(self):
        content = load_learning_content()

        for question in content.questions.values():
            self.assertIn(
                question["concept_id"],
                content.concept_graph.concepts,
            )

    def test_question_contains_presentation_data(self):
        content = load_learning_content()

        question = content.questions["eq_003"]

        self.assertTrue(question["prompt"])
        self.assertGreaterEqual(len(question["options"]), 2)
        self.assertTrue(question["explanation"])

    def test_rejects_mismatched_module_ids(self):
        with tempfile.TemporaryDirectory() as directory:
            concepts_path = Path(directory) / "concepts.json"
            questions_path = Path(directory) / "questions.json"

            concepts_path.write_text(
                json.dumps({
                    "module_id": "module_a",
                    "concepts": [
                        {
                            "concept_id": "arithmetic",
                            "name": "Arithmetic",
                            "prerequisites": [],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            questions_path.write_text(
                json.dumps({
                    "module_id": "module_b",
                    "questions": [],
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "module IDs do not match",
            ):
                load_learning_content(
                    concepts_path,
                    questions_path,
                )

    def test_rejects_question_with_unknown_concept(self):
        with tempfile.TemporaryDirectory() as directory:
            concepts_path = Path(directory) / "concepts.json"
            questions_path = Path(directory) / "questions.json"

            concepts = {
                "module_id": "test_module",
                "concepts": [
                    {
                        "concept_id": "arithmetic",
                        "name": "Arithmetic",
                        "prerequisites": [],
                    }
                ],
            }

            questions = {
                "module_id": "test_module",
                "questions": [
                    {
                        "question_id": "q1",
                        "concept_id": "unknown",
                        "prompt": "Test question?",
                        "options": [
                            {"option_id": "a", "text": "A"},
                            {"option_id": "b", "text": "B"},
                        ],
                        "correct_option_id": "a",
                        "misconception_rules": [],
                    }
                ],
            }

            concepts_path.write_text(
                json.dumps(concepts),
                encoding="utf-8",
            )
            questions_path.write_text(
                json.dumps(questions),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "unknown concept",
            ):
                load_learning_content(
                    concepts_path,
                    questions_path,
                )

    def test_rejects_question_with_invalid_correct_option(self):
        with tempfile.TemporaryDirectory() as directory:
            concepts_path = Path(directory) / "concepts.json"
            questions_path = Path(directory) / "questions.json"

            concepts_path.write_text(
                json.dumps({
                    "module_id": "test_module",
                    "concepts": [
                        {
                            "concept_id": "arithmetic",
                            "name": "Arithmetic",
                            "prerequisites": [],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            questions_path.write_text(
                json.dumps({
                    "module_id": "test_module",
                    "questions": [
                        {
                            "question_id": "q1",
                            "concept_id": "arithmetic",
                            "prompt": "Test question?",
                            "options": [
                                {"option_id": "a", "text": "A"},
                                {"option_id": "b", "text": "B"},
                            ],
                            "correct_option_id": "missing",
                            "misconception_rules": [],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "no matching correct option",
            ):
                load_learning_content(
                    concepts_path,
                    questions_path,
                )

    def test_rejects_misconception_rule_for_unknown_option(self):
        with tempfile.TemporaryDirectory() as directory:
            concepts_path = Path(directory) / "concepts.json"
            questions_path = Path(directory) / "questions.json"

            concepts_path.write_text(
                json.dumps({
                    "module_id": "test_module",
                    "concepts": [
                        {
                            "concept_id": "arithmetic",
                            "name": "Arithmetic",
                            "prerequisites": [],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            questions_path.write_text(
                json.dumps({
                    "module_id": "test_module",
                    "questions": [
                        {
                            "question_id": "q1",
                            "concept_id": "arithmetic",
                            "prompt": "Test question?",
                            "options": [
                                {"option_id": "a", "text": "A"},
                                {"option_id": "b", "text": "B"},
                            ],
                            "correct_option_id": "a",
                            "misconception_rules": [
                                {
                                    "option_id": "missing",
                                    "misconception_id": "test_error",
                                    "description": "Test diagnostic rule.",
                                }
                            ],
                        }
                    ],
                }),
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                ValueError,
                "unknown option",
            ):
                load_learning_content(
                    concepts_path,
                    questions_path,
                )


if __name__ == "__main__":
    unittest.main()
