
import json
import aiosqlite

from datetime import datetime
from pathlib import Path

from .database import DATABASE_PATH
from app.cognitive_engine.learner_state import LearnerConceptState


class LearnerStateRepository:
    """
    Handles persistent storage and retrieval of learner states
    and answer events using SQLite.
    """

    def __init__(self, database_path=DATABASE_PATH):
        self.database_path = Path(database_path)

    async def _connect(self):
        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        connection = await aiosqlite.connect(
            self.database_path
        )

        connection.row_factory = aiosqlite.Row
        return connection

    @staticmethod
    def _parse_datetime(value):
        if value is None:
            return None

        return datetime.fromisoformat(value)

    @staticmethod
    def _state_values(state):
        return (
            state.learner_id,
            state.concept_id,
            state.knowledge_probability,
            state.retention_anchor,
            (
                state.retention_anchor_at.isoformat()
                if state.retention_anchor_at else None
            ),
            state.attempts,
            state.correct_attempts,
            (
                state.last_attempt_at.isoformat()
                if state.last_attempt_at else None
            ),
            json.dumps(state.misconception_history),
        )

    async def _upsert_state(self, connection, state):
        await connection.execute(
            """
            INSERT INTO learner_concept_states (
                learner_id,
                concept_id,
                knowledge_probability,
                retention_anchor,
                retention_anchor_at,
                attempts,
                correct_attempts,
                last_attempt_at,
                misconception_history
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)

            ON CONFLICT(learner_id, concept_id)
            DO UPDATE SET
                knowledge_probability = excluded.knowledge_probability,
                retention_anchor = excluded.retention_anchor,
                retention_anchor_at = excluded.retention_anchor_at,
                attempts = excluded.attempts,
                correct_attempts = excluded.correct_attempts,
                last_attempt_at = excluded.last_attempt_at,
                misconception_history = excluded.misconception_history
            """,
            self._state_values(state),
        )

    async def save_state(self, state):
        """
        Insert or update one learner's state for a concept.
        """

        connection = await self._connect()

        try:
            await self._upsert_state(connection, state)
            await connection.commit()

        except Exception:
            await connection.rollback()
            raise

        finally:
            await connection.close()

    async def load_all_states(self):
        """
        Load every saved learner-concept state from SQLite.
        Returns a list of LearnerConceptState objects.
        """

        connection = await self._connect()

        try:
            async with connection.execute(
                """
                SELECT *
                FROM learner_concept_states
                ORDER BY learner_id, concept_id
                """
            ) as cursor:
                rows = await cursor.fetchall()

            states = []

            for row in rows:
                state = LearnerConceptState(
                    learner_id=row["learner_id"],
                    concept_id=row["concept_id"],
                    knowledge_probability=row["knowledge_probability"],
                    retention_anchor=row["retention_anchor"],
                    retention_anchor_at=self._parse_datetime(
                        row["retention_anchor_at"]
                    ),
                    attempts=row["attempts"],
                    correct_attempts=row["correct_attempts"],
                    last_attempt_at=self._parse_datetime(
                        row["last_attempt_at"]
                    ),
                    misconception_history=json.loads(
                        row["misconception_history"]
                    ),
                )

                states.append(state)

            return states

        finally:
            await connection.close()

    async def save_answer_event(
        self,
        learner_id,
        question_id,
        concept_id,
        selected_option_id,
        is_correct,
        misconception_id,
        submitted_at,
    ):
        """
        Store an individual answer submission.
        """

        if isinstance(submitted_at, datetime):
            submitted_at = submitted_at.isoformat()

        connection = await self._connect()

        try:
            await connection.execute(
                """
                INSERT INTO answer_events (
                    learner_id,
                    question_id,
                    concept_id,
                    selected_option_id,
                    is_correct,
                    misconception_id,
                    submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    learner_id,
                    question_id,
                    concept_id,
                    selected_option_id,
                    int(is_correct),
                    misconception_id,
                    submitted_at,
                ),
            )

            await connection.commit()

        except Exception:
            await connection.rollback()
            raise

        finally:
            await connection.close()

    async def save_submission(
        self,
        state,
        question_id,
        selected_option_id,
        is_correct,
        misconception_id,
        submitted_at,
    ):
        """
        Atomically save an updated learner state and its answer event.

        Both database writes succeed together, or neither is committed.
        """

        if isinstance(submitted_at, datetime):
            submitted_at = submitted_at.isoformat()

        connection = await self._connect()

        try:
            # Write 1: persist the updated learner state.
            await self._upsert_state(connection, state)

            # Write 2: record the submitted answer.
            await connection.execute(
                """
                INSERT INTO answer_events (
                    learner_id,
                    question_id,
                    concept_id,
                    selected_option_id,
                    is_correct,
                    misconception_id,
                    submitted_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    state.learner_id,
                    question_id,
                    state.concept_id,
                    selected_option_id,
                    int(is_correct),
                    misconception_id,
                    submitted_at,
                ),
            )

            # Commit both writes together.
            await connection.commit()

        except Exception:
            await connection.rollback()
            raise

        finally:
            await connection.close()
