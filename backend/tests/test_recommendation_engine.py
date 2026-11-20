
import unittest
from datetime import datetime, timedelta, timezone

from app.cognitive_engine.concept_graph import (
    Concept,
    ConceptGraph,
)

from app.cognitive_engine.learner_state import (
    LearnerStateManager,
)

from app.cognitive_engine.recommendation_engine import (
    AdaptiveRecommendationEngine,
)


class TestAdaptiveRecommendationEngine(unittest.TestCase):

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
                "Expressions",
                ["variables"]
            )
        )

        self.graph.register_concept(
            Concept(
                "equations",
                "Linear Equations",
                ["expressions"]
            )
        )

        self.manager = LearnerStateManager()

        self.engine = AdaptiveRecommendationEngine(
            self.graph,
            self.manager
        )

        self.now = datetime(
            2026, 11, 20, 10, 0,
            tzinfo=timezone.utc
        )

        # Prepare a learner who has mastered the prerequisites.
        for concept_id in [
            "arithmetic",
            "variables",
            "expressions"
        ]:
            state = self.manager.get_or_create_state(
                "learner_1",
                concept_id
            )
            state.knowledge_probability = 0.95

            self.manager.record_review(
                "learner_1",
                concept_id,
                retention_anchor=0.95,
                timestamp=self.now
            )

    def test_low_prerequisite_mastery_is_prioritized(self):
        state = self.manager.get_state(
            "learner_1",
            "variables"
        )
        state.knowledge_probability = 0.30

        result = self.engine.recommend_next_step(
            "learner_1",
            "equations",
            as_of=self.now
        )

        self.assertEqual(
            result["recommended_concept_id"],
            "variables"
        )
        self.assertEqual(
            result["action"],
            "practice_prerequisite"
        )

    def test_low_target_mastery_recommends_practice(self):
        state = self.manager.get_or_create_state(
            "learner_1",
            "equations"
        )
        state.knowledge_probability = 0.40

        result = self.engine.recommend_next_step(
            "learner_1",
            "equations",
            as_of=self.now
        )

        self.assertEqual(
            result["action"],
            "practice_target"
        )

   
    def test_repeated_misconception_triggers_remediation(self):
        state = self.manager.get_state(
            "learner_1",
            "expressions"
        )

        state.misconception_history = [
            {
                "misconception_id": "sign_error",
                "timestamp": self.now.isoformat()
            },
            {
                "misconception_id": "sign_error",
                "timestamp": self.now.isoformat()
            }
        ]

        result = self.engine.recommend_next_step(
            "learner_1",
            "equations",
            as_of=self.now
        )

        self.assertEqual(
            result["action"],
            "targeted_remediation"
        )
        self.assertIn(
            "sign_error",
            result["misconceptions"]
        )

    def test_low_retention_triggers_revision(self):
        state = self.manager.get_state(
            "learner_1",
            "variables"
        )

        state.retention_anchor = 0.95
        state.retention_anchor_at = (
            self.now - timedelta(days=30)
        )

        result = self.engine.recommend_next_step(
            "learner_1",
            "equations",
            as_of=self.now
        )

        self.assertEqual(
            result["recommended_concept_id"],
            "variables"
        )
        self.assertEqual(
            result["action"],
            "review_prerequisite"
        )


    def test_all_strong_concepts_allow_progression(self):
        state = self.manager.get_or_create_state(
            "learner_1",
            "equations"
        )
        state.knowledge_probability = 0.95

        self.manager.record_review(
            "learner_1",
            "equations",
            retention_anchor=0.95,
            timestamp=self.now
        )

        result = self.engine.recommend_next_step(
            "learner_1",
            "equations",
            as_of=self.now
        )

        self.assertEqual(result["action"], "progress")

    def test_recommendations_are_learner_specific(self):
        result = self.engine.recommend_next_step(
            "learner_2",
            "equations",
            as_of=self.now
        )

        self.assertEqual(
            result["recommended_concept_id"],
            "arithmetic"
        )
        self.assertEqual(
            result["action"],
            "practice_prerequisite"
        )

    def test_invalid_mastery_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            AdaptiveRecommendationEngine(
                self.graph,
                self.manager,
                mastery_threshold=1.5
            )

    def test_invalid_retention_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            AdaptiveRecommendationEngine(
                self.graph,
                self.manager,
                retention_threshold=-0.1
            )

    def test_invalid_misconception_threshold_is_rejected(self):
        with self.assertRaises(ValueError):
            AdaptiveRecommendationEngine(
                self.graph,
                self.manager,
                repeated_misconception_threshold=0
            )

    def test_unknown_target_is_rejected(self):
        with self.assertRaises(ValueError):
            self.engine.recommend_next_step(
                "learner_1",
                "unknown_concept",
                as_of=self.now
            )


if __name__ == "__main__":
    unittest.main()

