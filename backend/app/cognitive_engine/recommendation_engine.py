
from .concept_graph import ConceptGraph
from .learner_state import LearnerStateManager


class AdaptiveRecommendationEngine:
    """
    Explainable, rule-based recommendation engine.

    Uses:
    - Concept prerequisites
    - Learner knowledge estimates
    - Estimated retention
    - Recorded misconception patterns
    """

    def __init__(
        self,
        concept_graph: ConceptGraph,
        learner_manager: LearnerStateManager,
        mastery_threshold=0.80,
        retention_threshold=0.60,
        repeated_misconception_threshold=2,
    ):
        if not 0 <= mastery_threshold <= 1:
            raise ValueError("Invalid mastery threshold.")

        if not 0 <= retention_threshold <= 1:
            raise ValueError("Invalid retention threshold.")

        if (
            not isinstance(repeated_misconception_threshold, int)
            or isinstance(repeated_misconception_threshold, bool)
            or repeated_misconception_threshold < 1
        ):
            raise ValueError(
                "Misconception threshold must be a positive integer."
            )

        self.concept_graph = concept_graph
        self.learner_manager = learner_manager

        self.mastery_threshold = mastery_threshold
        self.retention_threshold = retention_threshold
        self.repeated_misconception_threshold = (
            repeated_misconception_threshold
        )

    def recommend_next_step(
        self,
        learner_id,
        target_concept_id,
        as_of=None
    ):
        """
        Examine the target's learning path and recommend
        the earliest concept requiring intervention.
        """

        learning_path = self.concept_graph.get_learning_path(
            target_concept_id
        )

        for concept_id in learning_path:

            state = self.learner_manager.get_or_create_state(
                learner_id,
                concept_id
            )

            retention_result = (
                self.learner_manager.estimate_retention(
                    learner_id,
                    concept_id,
                    as_of=as_of
                )
            )

            retention = retention_result["estimated_retention"]
            knowledge = state.knowledge_probability

            is_target = concept_id == target_concept_id

            # Count recorded occurrences of each misconception.
            misconception_counts = {}

            for entry in state.misconception_history:
                misconception_id = entry["misconception_id"]

                misconception_counts[misconception_id] = (
                    misconception_counts.get(misconception_id, 0) + 1
                )

            repeated = [
                misconception_id
                for misconception_id, count
                in misconception_counts.items()
                if count >= self.repeated_misconception_threshold
            ]

            # Repeated errors receive targeted intervention.
            if repeated:
                return {
                    "learner_id": learner_id,
                    "target_concept_id": target_concept_id,
                    "recommended_concept_id": concept_id,
                    "action": "targeted_remediation",
                    "reason": "Repeated misconception detected.",
                    "misconceptions": repeated,
                    "knowledge_probability": knowledge,
                    "estimated_retention": retention,
                }

            # Mastery is checked before progression.
            if knowledge < self.mastery_threshold:
                action = (
                    "practice_target"
                    if is_target
                    else "practice_prerequisite"
                )

                return {
                    "learner_id": learner_id,
                    "target_concept_id": target_concept_id,
                    "recommended_concept_id": concept_id,
                    "action": action,
                    "reason": "Knowledge estimate is below the mastery threshold.",
                    "knowledge_probability": knowledge,
                    "estimated_retention": retention,
                }

            # A mastered concept may still need revision.
            if retention < self.retention_threshold:
                action = (
                    "review_target"
                    if is_target
                    else "review_prerequisite"
                )

                return {
                    "learner_id": learner_id,
                    "target_concept_id": target_concept_id,
                    "recommended_concept_id": concept_id,
                    "action": action,
                    "reason": "Estimated retention is below the revision threshold.",
                    "knowledge_probability": knowledge,
                    "estimated_retention": retention,
                }

        return {
            "learner_id": learner_id,
            "target_concept_id": target_concept_id,
            "recommended_concept_id": target_concept_id,
            "action": "progress",
            "reason": "All concepts in the learning path meet the configured thresholds.",
            "knowledge_probability": (
                self.learner_manager.get_state(
                    learner_id,
                    target_concept_id
                ).knowledge_probability
            ),
            "estimated_retention": (
                self.learner_manager.estimate_retention(
                    learner_id,
                    target_concept_id,
                    as_of=as_of
                )["estimated_retention"]
            ),
        }
