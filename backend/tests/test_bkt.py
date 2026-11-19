
import unittest

from app.cognitive_engine.bkt import (
    BKTParameters,
    BayesianKnowledgeTracer,
)


class TestBayesianKnowledgeTracing(unittest.TestCase):

    def setUp(self):
        self.tracer = BayesianKnowledgeTracer()

    def test_correct_answer_updates_knowledge(self):
        result = self.tracer.update(0.20, True)

        self.assertGreater(
            result["updated_knowledge"], 0.20
        )

    def test_incorrect_answer_updates_knowledge(self):
        result = self.tracer.update(0.20, False)

        self.assertLess(
            result["updated_knowledge"], 0.20
        )

    def test_knowledge_stays_between_zero_and_one(self):
        history = self.tracer.trace_sequence(
            [True, False, True, True, False]
        )

        for result in history:
            self.assertGreaterEqual(
                result["updated_knowledge"], 0
            )
            self.assertLessEqual(
                result["updated_knowledge"], 1
            )

    def test_sequence_length(self):
        history = self.tracer.trace_sequence(
            [True, False, True]
        )

        self.assertEqual(len(history), 3)

    def test_invalid_parameters_are_rejected(self):
        with self.assertRaises(ValueError):
            BKTParameters(initial_knowledge=1.5)


if __name__ == "__main__":
    unittest.main()
