
import unittest
from datetime import datetime, timedelta, timezone

from app.cognitive_engine.learner_state import (
    LearnerStateManager,
)


class TestLearnerStateManager(unittest.TestCase):

    def setUp(self):
        self.manager = LearnerStateManager()

        self.start = datetime(
            2026, 11, 19, 10, 0,
            tzinfo=timezone.utc
        )

    def test_state_is_created(self):
        state = self.manager.get_or_create_state(
            "learner_1",
            "algebra"
        )

        self.assertEqual(state.learner_id, "learner_1")
        self.assertEqual(state.concept_id, "algebra")
        self.assertEqual(state.attempts, 0)

    def test_initial_knowledge_comes_from_bkt(self):
        state = self.manager.get_or_create_state(
            "learner_1",
            "algebra"
        )

        self.assertEqual(state.knowledge_probability, 0.20)

    def test_attempt_updates_knowledge(self):
        result = self.manager.record_attempt(
            "learner_1",
            "algebra",
            True,
            timestamp=self.start
        )

        self.assertGreater(
            result["knowledge_probability"],
            0.20
        )

    def test_attempt_counter_increments(self):
        self.manager.record_attempt(
            "learner_1", "algebra", True,
            timestamp=self.start
        )

        self.manager.record_attempt(
            "learner_1", "algebra", False,
            timestamp=self.start + timedelta(minutes=5)
        )

        state = self.manager.get_state(
            "learner_1", "algebra"
        )

        self.assertEqual(state.attempts, 2)
        self.assertEqual(state.correct_attempts, 1)

    def test_misconception_is_recorded(self):
        self.manager.record_attempt(
            "learner_1",
            "algebra",
            False,
            misconception_id="sign_error",
            timestamp=self.start
        )

        state = self.manager.get_state(
            "learner_1", "algebra"
        )

        self.assertEqual(
            state.misconception_history[0]["misconception_id"],
            "sign_error"
        )

    def test_learners_have_independent_states(self):
        self.manager.record_attempt(
            "learner_1", "algebra", True,
            timestamp=self.start
        )

        state_2 = self.manager.get_or_create_state(
            "learner_2", "algebra"
        )

        self.assertEqual(state_2.attempts, 0)
        self.assertEqual(state_2.knowledge_probability, 0.20)

    def test_concepts_have_independent_states(self):
        self.manager.record_attempt(
            "learner_1", "algebra", True,
            timestamp=self.start
        )

        state = self.manager.get_or_create_state(
            "learner_1", "geometry"
        )

        self.assertEqual(state.attempts, 0)

    def test_retention_decreases_over_time(self):
        self.manager.record_review(
            "learner_1",
            "algebra",
            timestamp=self.start
        )

        day_1 = self.manager.estimate_retention(
            "learner_1",
            "algebra",
            as_of=self.start + timedelta(days=1)
        )

        day_7 = self.manager.estimate_retention(
            "learner_1",
            "algebra",
            as_of=self.start + timedelta(days=7)
        )

        self.assertGreater(
            day_1["estimated_retention"],
            day_7["estimated_retention"]
        )

    def test_review_does_not_change_knowledge(self):
        state = self.manager.get_or_create_state(
            "learner_1", "algebra"
        )

        initial_knowledge = state.knowledge_probability

        self.manager.record_review(
            "learner_1",
            "algebra",
            timestamp=self.start
        )

        self.assertEqual(
            state.knowledge_probability,
            initial_knowledge
        )

    def test_invalid_attempt_type_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.record_attempt(
                "learner_1",
                "algebra",
                "correct",
                timestamp=self.start
            )

    def test_invalid_retention_anchor_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.record_review(
                "learner_1",
                "algebra",
                retention_anchor=0.01,
                timestamp=self.start
            )

    def test_unknown_state_is_rejected(self):
        with self.assertRaises(ValueError):
            self.manager.get_state(
                "unknown_learner",
                "algebra"
            )

    def test_naive_timestamp_is_rejected(self):
        naive_time = datetime(2026, 11, 19, 10, 0)

        with self.assertRaises(ValueError):
            self.manager.record_attempt(
                "learner_1",
                "algebra",
                True,
                timestamp=naive_time
            )

    def test_out_of_order_attempt_is_rejected(self):
        self.manager.record_attempt(
            "learner_1",
            "algebra",
            True,
            timestamp=self.start
        )

        with self.assertRaises(ValueError):
            self.manager.record_attempt(
                "learner_1",
                "algebra",
                False,
                timestamp=self.start - timedelta(minutes=1)
            )


if __name__ == "__main__":
    unittest.main()

