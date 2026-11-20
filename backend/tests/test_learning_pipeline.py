
import unittest
from datetime import datetime, timezone

from app.cognitive_engine.concept_graph import Concept, ConceptGraph
from app.cognitive_engine.learner_state import LearnerStateManager
from app.cognitive_engine.misconceptions import (
    DiagnosticQuestion,
    MisconceptionDetector,
    MisconceptionRule,
)
from app.cognitive_engine.recommendation_engine import (
    AdaptiveRecommendationEngine,
)
from app.cognitive_engine.learning_pipeline import (
    CognitiveLearningPipeline,
)


class TestCognitiveLearningPipeline(unittest.TestCase):

    def setUp(self):
        # 1. Build the concept graph.
        self.graph = ConceptGraph()

        self.graph.register_concept(
            Concept("arithmetic", "Arithmetic")
        )

        self.graph.register_concept(
            Concept(
                "variables",
                "Variables",
                prerequisites=["arithmetic"],
            )
        )

        self.graph.register_concept(
            Concept(
                "equations",
                "Linear Equations",
                prerequisites=["variables"],
            )
        )

        # 2. Register a diagnostic question.
        self.detector = MisconceptionDetector()

        question = DiagnosticQuestion(
            question_id="q1",
            concept_id="equations",
            correct_option_id="b",
            misconception_rules=[
                MisconceptionRule(
                    option_id="a",
                    misconception_id="sign_error",
                    description="Incorrect handling of negative signs.",
                ),
                MisconceptionRule(
                    option_id="c",
                    misconception_id="inverse_operation_error",
                    description="Incorrect use of inverse operations.",
                ),
            ],
        )

        self.detector.register_question(question)

        # 3. Create learner state manager.
        self.manager = LearnerStateManager()

        # 4. Create recommendation engine.
        self.recommender = AdaptiveRecommendationEngine(
            concept_graph=self.graph,
            learner_manager=self.manager,
        )

        # 5. Connect the cognitive components.
        self.pipeline = CognitiveLearningPipeline(
            misconception_detector=self.detector,
            learner_manager=self.manager,
            recommendation_engine=self.recommender,
        )

        # 6. Use a fixed UTC timestamp.
        self.now = datetime(
            2026, 11, 20, 12, 0,
            tzinfo=timezone.utc,
        )

        # 7. Mark prerequisite concepts as mastered.
        # This allows recommendations to reach "equations".
        for concept_id in ["arithmetic", "variables"]:
            state = self.manager.get_or_create_state(
                "learner_1",
                concept_id,
            )
            state.knowledge_probability = 0.95

    def test_correct_answer_updates_learner_state(self):
        result = self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="b",
            timestamp=self.now,
        )

        state = self.manager.get_state(
            "learner_1",
            "equations",
        )

        self.assertEqual(state.attempts, 1)
        self.assertEqual(state.correct_attempts, 1)
        self.assertGreater(
            state.knowledge_probability,
            0.20,
        )
        self.assertFalse(
            result["state_update"]["misconception_recorded"]
        )

    def test_wrong_answer_records_misconception(self):
        self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="a",
            timestamp=self.now,
        )

        state = self.manager.get_state(
            "learner_1",
            "equations",
        )

        self.assertEqual(state.attempts, 1)
        self.assertEqual(state.correct_attempts, 0)
        self.assertEqual(len(state.misconception_history), 1)
        self.assertEqual(
            state.misconception_history[0]["misconception_id"],
            "sign_error",
        )

    def test_unknown_wrong_answer_is_not_misdiagnosed(self):
        result = self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="unknown_option",
            timestamp=self.now,
        )

        state = self.manager.get_state(
            "learner_1",
            "equations",
        )

        self.assertEqual(state.attempts, 1)
        self.assertEqual(len(state.misconception_history), 0)
        self.assertFalse(
            result["state_update"]["misconception_recorded"]
        )

    def test_repeated_misconception_triggers_remediation(self):
        # Submit the same mapped misconception twice.
        for _ in range(2):
            self.pipeline.process_answer(
                learner_id="learner_1",
                question_id="q1",
                selected_option_id="a",
                timestamp=self.now,
            )

        state = self.manager.get_state(
            "learner_1",
            "equations",
        )

        self.assertEqual(state.attempts, 2)
        self.assertEqual(len(state.misconception_history), 2)

        result = self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="a",
            timestamp=self.now,
        )

        self.assertEqual(
            result["recommendation"]["action"],
            "targeted_remediation",
        )

    def test_pipeline_returns_recommendation(self):
        result = self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="b",
            timestamp=self.now,
        )

        self.assertIn("recommendation", result)
        self.assertIsNotNone(result["recommendation"])
        self.assertIn("action", result["recommendation"])

    def test_unknown_question_is_rejected(self):
        with self.assertRaises(ValueError):
            self.pipeline.process_answer(
                learner_id="learner_1",
                question_id="unknown_question",
                selected_option_id="a",
                timestamp=self.now,
            )

    def test_learner_states_are_isolated(self):
        self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="b",
            timestamp=self.now,
        )

        learner_one_state = self.manager.get_state(
            "learner_1",
            "equations",
        )

        self.assertIsNotNone(learner_one_state)

        # A different learner should not have this state.
        with self.assertRaises(ValueError):
            self.manager.get_state(
                "learner_2",
                "equations",
            )

    def test_pipeline_returns_processing_timestamp(self):
        result = self.pipeline.process_answer(
            learner_id="learner_1",
            question_id="q1",
            selected_option_id="b",
            timestamp=self.now,
        )

        self.assertEqual(
            result["processed_at"],
            self.now.isoformat(),
        )


if __name__ == "__main__":
    unittest.main()
