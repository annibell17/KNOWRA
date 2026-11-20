
from datetime import datetime, timezone

from .misconceptions import MisconceptionDetector
from .learner_state import LearnerStateManager
from .recommendation_engine import AdaptiveRecommendationEngine


class CognitiveLearningPipeline:
    """
    Coordinates KNOWRA's cognitive components.

    Workflow:
    1. Diagnose the learner's answer.
    2. Update the learner's knowledge estimate.
    3. Record any mapped misconception.
    4. Generate an adaptive learning recommendation.
    """

    def __init__(
        self,
        misconception_detector: MisconceptionDetector,
        learner_manager: LearnerStateManager,
        recommendation_engine: AdaptiveRecommendationEngine,
    ):
        self.misconception_detector = misconception_detector
        self.learner_manager = learner_manager
        self.recommendation_engine = recommendation_engine

    def process_answer(
        self,
        learner_id,
        question_id,
        selected_option_id,
        timestamp=None,
    ):
        """
        Process one submitted answer through the cognitive engine.
        """

        # Use one timestamp consistently across the entire event.
        event_timestamp = timestamp or datetime.now(timezone.utc)

        # Step 1: Verify that the question exists.
        question = self.misconception_detector.questions.get(
            question_id
        )

        if question is None:
            raise ValueError("Unknown question ID.")

        # Step 2: Diagnose the submitted answer.
        diagnosis = self.misconception_detector.diagnose(
            question_id,
            selected_option_id,
        )

        # Step 3: Update the learner's cognitive state.
        state_update = self.learner_manager.record_attempt(
            learner_id=learner_id,
            concept_id=question.concept_id,
            correct=diagnosis["is_correct"],
            misconception_id=diagnosis["diagnosis"],
            timestamp=event_timestamp,
        )

        # Step 4: Generate the next learning recommendation.
        recommendation = (
            self.recommendation_engine.recommend_next_step(
                learner_id=learner_id,
                target_concept_id=question.concept_id,
                as_of=event_timestamp,
            )
        )

        # Step 5: Return one consolidated result.
        return {
            "learner_id": learner_id,
            "question_id": question_id,
            "concept_id": question.concept_id,
            "diagnosis": diagnosis,
            "state_update": state_update,
            "recommendation": recommendation,
            "processed_at": event_timestamp.isoformat(),
        }

