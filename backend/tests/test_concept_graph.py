
import unittest

from app.cognitive_engine.concept_graph import (
    Concept,
    ConceptGraph,
)


class TestConceptGraph(unittest.TestCase):

    def setUp(self):
        self.graph = ConceptGraph()

        self.graph.register_concept(
            Concept("arithmetic", "Arithmetic")
        )

        self.graph.register_concept(
            Concept(
                "variables",
                "Variables",
                ["arithmetic"]
            )
        )

        self.graph.register_concept(
            Concept(
                "expressions",
                "Algebraic Expressions",
                ["variables"]
            )
        )

        self.graph.register_concept(
            Concept(
                "linear_equations",
                "Linear Equations",
                ["expressions"]
            )
        )

        self.graph.register_concept(
            Concept(
                "simultaneous_equations",
                "Simultaneous Equations",
                ["linear_equations"]
            )
        )

    def test_concept_registration(self):
        self.assertIn("arithmetic", self.graph.concepts)

    def test_duplicate_concept_is_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.register_concept(
                Concept("arithmetic", "Duplicate")
            )

    def test_unknown_prerequisite_is_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.register_concept(
                Concept("fractions", "Fractions", ["unknown"])
            )

    def test_self_prerequisite_is_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.register_concept(
                Concept("self", "Self", ["self"])
            )

    def test_duplicate_prerequisites_are_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.register_concept(
                Concept(
                    "duplicate_test",
                    "Duplicate Test",
                    ["arithmetic", "arithmetic"]
                )
            )

    def test_learning_path_order(self):
        path = self.graph.get_learning_path(
            "linear_equations"
        )

        self.assertEqual(
            path,
            [
                "arithmetic",
                "variables",
                "expressions",
                "linear_equations",
            ]
        )

    def test_shared_prerequisites_are_not_repeated(self):
        self.graph.register_concept(
            Concept(
                "equation_applications",
                "Equation Applications",
                ["expressions", "linear_equations"]
            )
        )

        path = self.graph.get_learning_path(
            "equation_applications"
        )

        self.assertEqual(len(path), len(set(path)))
        self.assertEqual(path.count("expressions"), 1)

    def test_missing_prerequisites(self):
        missing = self.graph.get_missing_prerequisites(
            "linear_equations",
            {"arithmetic", "variables"}
        )

        self.assertEqual(
            missing,
            ["expressions"]
        )

    def test_mastered_prerequisites_return_empty_list(self):
        missing = self.graph.get_missing_prerequisites(
            "linear_equations",
            {"arithmetic", "variables", "expressions"}
        )

        self.assertEqual(missing, [])

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            self.graph.get_learning_path("unknown")


if __name__ == "__main__":
    unittest.main()
