
from dataclasses import dataclass, field
from datetime import datetime, timezone

from .bkt import BayesianKnowledgeTracer
from .retention import RetentionModel


@dataclass
class LearnerConceptState:
    """Current state of one learner for one concept."""

    learner_id: str
    concept_id: str

    knowledge_probability: float = 0.20

    # Retention is tracked separately from knowledge mastery.
    retention_anchor: float = 1.0
    retention_anchor_at: datetime | None = None

    attempts: int = 0
    correct_attempts: int = 0

    last_attempt_at: datetime | None = None

    misconception_history: list = field(default_factory=list)


class LearnerStateManager:
    """
    Maintains in-memory learner states across concepts.

    BKT updates knowledge estimates.
    RetentionModel estimates decay from the most recent
    explicitly recorded review event.
    """

    def __init__(
        self,
        bkt_tracer=None,
        retention_model=None
    ):
        self.bkt_tracer = (
            bkt_tracer or BayesianKnowledgeTracer()
        )

        self.retention_model = (
            retention_model or RetentionModel()
        )

        self.learners = {}

    @staticmethod
    def _validate_id(value, field_name):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(
                f"{field_name} must be a non-empty string."
            )

    @staticmethod
    def _validate_timestamp(timestamp):
        if timestamp is None:
            return datetime.now(timezone.utc)

        if not isinstance(timestamp, datetime):
            raise ValueError("Timestamp must be a datetime.")

        if timestamp.tzinfo is None:
            raise ValueError("Timestamp must include a timezone.")

        return timestamp

    def get_or_create_state(self, learner_id, concept_id):
        self._validate_id(learner_id, "Learner ID")
        self._validate_id(concept_id, "Concept ID")

        if learner_id not in self.learners:
            self.learners[learner_id] = {}

        learner_concepts = self.learners[learner_id]

        if concept_id not in learner_concepts:
            learner_concepts[concept_id] = LearnerConceptState(
                learner_id=learner_id,
                concept_id=concept_id,
                knowledge_probability=(
                    self.bkt_tracer.parameters.initial_knowledge
                ),
            )

        return learner_concepts[concept_id]

    def get_state(self, learner_id, concept_id):
        self._validate_id(learner_id, "Learner ID")
        self._validate_id(concept_id, "Concept ID")

        try:
            return self.learners[learner_id][concept_id]
        except KeyError:
            raise ValueError("Learner concept state not found.")

    def record_attempt(
        self,
        learner_id,
        concept_id,
        correct,
        misconception_id=None,
        timestamp=None
    ):
        if not isinstance(correct, bool):
            raise ValueError("Correct must be a boolean.")

        if misconception_id is not None:
            self._validate_id(
                misconception_id,
                "Misconception ID"
            )

        timestamp = self._validate_timestamp(timestamp)

        state = self.get_or_create_state(
            learner_id,
            concept_id
        )

        if (
            state.last_attempt_at is not None
            and timestamp < state.last_attempt_at
        ):
            raise ValueError(
                "Attempt timestamp cannot precede the previous attempt."
            )

        update = self.bkt_tracer.update(
            state.knowledge_probability,
            correct
        )

        state.knowledge_probability = (
            update["updated_knowledge"]
        )

        state.attempts += 1

        if correct:
            state.correct_attempts += 1

        state.last_attempt_at = timestamp

        if misconception_id is not None:
            state.misconception_history.append({
                "misconception_id": misconception_id,
                "timestamp": timestamp.isoformat(),
            })

        return {
            "learner_id": learner_id,
            "concept_id": concept_id,
            "knowledge_probability": (
                state.knowledge_probability
            ),
            "attempts": state.attempts,
            "correct_attempts": state.correct_attempts,
            "misconception_recorded": (
                misconception_id is not None
            ),
            "bkt_update": update,
        }

    def record_review(
        self,
        learner_id,
        concept_id,
        retention_anchor=1.0,
        timestamp=None
    ):
        """
        Record an explicit learning/review event.

        This establishes a new retention reference point.
        It does not directly change BKT knowledge mastery.
        """

        if not isinstance(retention_anchor, (int, float)):
            raise ValueError("Retention anchor must be numeric.")

        if not 0 <= retention_anchor <= 1:
            raise ValueError(
                "Retention anchor must be between 0 and 1."
            )

        minimum_anchor = (
            self.retention_model.parameters.minimum_retention
        )

        if retention_anchor < minimum_anchor:
            raise ValueError(
                f"Retention anchor must be at least {minimum_anchor}."
            )

        timestamp = self._validate_timestamp(timestamp)

        state = self.get_or_create_state(
            learner_id,
            concept_id
        )

        if (
            state.retention_anchor_at is not None
            and timestamp < state.retention_anchor_at
        ):
            raise ValueError(
                "Review timestamp cannot precede the previous review."
            )

        state.retention_anchor = float(retention_anchor)
        state.retention_anchor_at = timestamp

        return {
            "learner_id": learner_id,
            "concept_id": concept_id,
            "retention_anchor": state.retention_anchor,
            "review_timestamp": timestamp.isoformat(),
        }

    def estimate_retention(
        self,
        learner_id,
        concept_id,
        as_of=None
    ):
        timestamp = self._validate_timestamp(as_of)

        state = self.get_state(
            learner_id,
            concept_id
        )

        if state.retention_anchor_at is None:
            elapsed_days = 0.0
        else:
            elapsed_seconds = (
                timestamp - state.retention_anchor_at
            ).total_seconds()

            if elapsed_seconds < 0:
                raise ValueError(
                    "Estimation time cannot precede the last review."
                )

            elapsed_days = elapsed_seconds / 86400

        return self.retention_model.estimate(
            state.retention_anchor,
            elapsed_days
        )

