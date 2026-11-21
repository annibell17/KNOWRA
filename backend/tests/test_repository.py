
import unittest
import tempfile

from pathlib import Path
from datetime import datetime, timezone, timedelta

from app.database.database import initialize_database
from app.database.repository import LearnerStateRepository
from app.cognitive_engine.learner_state import LearnerConceptState


class TestLearnerStateRepository(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_directory.name) / "test_knowra.db"
        )

        await initialize_database(self.database_path)

        self.repository = LearnerStateRepository(
            self.database_path
        )

    async def asyncTearDown(self):
        self.temp_directory.cleanup()

    async def test_save_and_load_learner_state(self):
        timestamp = datetime.now(timezone.utc)

        state = LearnerConceptState(
            learner_id="learner_001",
            concept_id="linear_equations",
            knowledge_probability=0.75,
            retention_anchor=0.90,
            retention_anchor_at=timestamp,
            attempts=5,
            correct_attempts=4,
            last_attempt_at=timestamp,
            misconception_history=[
                {
                    "misconception_id": "sign_error",
                    "timestamp": timestamp.isoformat(),
                }
            ],
        )

        await self.repository.save_state(state)

        loaded_states = await self.repository.load_all_states()

        self.assertEqual(len(loaded_states), 1)

        loaded = loaded_states[0]

        self.assertEqual(loaded.learner_id, "learner_001")
        self.assertEqual(loaded.concept_id, "linear_equations")
        self.assertAlmostEqual(loaded.knowledge_probability, 0.75)
        self.assertAlmostEqual(loaded.retention_anchor, 0.90)
        self.assertEqual(loaded.attempts, 5)
        self.assertEqual(loaded.correct_attempts, 4)
        self.assertEqual(loaded.retention_anchor_at, timestamp)
        self.assertEqual(loaded.last_attempt_at, timestamp)
        self.assertEqual(len(loaded.misconception_history), 1)
        self.assertEqual(
            loaded.misconception_history[0]["misconception_id"],
            "sign_error",
        )

    async def test_save_state_updates_existing_record(self):
        state = LearnerConceptState(
            learner_id="learner_002",
            concept_id="algebra",
            knowledge_probability=0.30,
        )

        await self.repository.save_state(state)

        state.knowledge_probability = 0.85
        state.attempts = 3
        state.correct_attempts = 2

        await self.repository.save_state(state)

        loaded_states = await self.repository.load_all_states()

        self.assertEqual(len(loaded_states), 1)
        self.assertAlmostEqual(
            loaded_states[0].knowledge_probability,
            0.85,
        )
        self.assertEqual(loaded_states[0].attempts, 3)

    async def test_save_and_load_multiple_learners(self):
        first = LearnerConceptState(
            learner_id="learner_A",
            concept_id="fractions",
        )

        second = LearnerConceptState(
            learner_id="learner_B",
            concept_id="fractions",
        )

        await self.repository.save_state(first)
        await self.repository.save_state(second)

        loaded_states = await self.repository.load_all_states()

        self.assertEqual(len(loaded_states), 2)

        learner_ids = {
            state.learner_id for state in loaded_states
        }

        self.assertEqual(
            learner_ids,
            {"learner_A", "learner_B"},
        )

    async def test_save_answer_event(self):
        timestamp = datetime.now(timezone.utc)

        await self.repository.save_answer_event(
            learner_id="learner_003",
            question_id="question_001",
            concept_id="linear_equations",
            selected_option_id="a",
            is_correct=False,
            misconception_id="sign_error",
            submitted_at=timestamp,
        )

        import aiosqlite

        connection = await aiosqlite.connect(
            self.database_path
        )

        try:
            async with connection.execute(
                """
                SELECT *
                FROM answer_events
                WHERE learner_id = ?
                """,
                ("learner_003",),
            ) as cursor:
                row = await cursor.fetchone()

            self.assertIsNotNone(row)
            self.assertEqual(row[1], "learner_003")
            self.assertEqual(row[2], "question_001")
            self.assertEqual(row[3], "linear_equations")
            self.assertEqual(row[4], "a")
            self.assertEqual(row[5], 0)
            self.assertEqual(row[6], "sign_error")
            self.assertEqual(row[7], timestamp.isoformat())

        finally:
            await connection.close()

    async def test_save_answer_event_without_misconception(self):
        timestamp = datetime.now(timezone.utc)

        await self.repository.save_answer_event(
            learner_id="learner_004",
            question_id="question_002",
            concept_id="arithmetic",
            selected_option_id="b",
            is_correct=True,
            misconception_id=None,
            submitted_at=timestamp,
        )

        import aiosqlite

        connection = await aiosqlite.connect(
            self.database_path
        )

        try:
            async with connection.execute(
                """
                SELECT is_correct, misconception_id
                FROM answer_events
                WHERE learner_id = ?
                """,
                ("learner_004",),
            ) as cursor:
                row = await cursor.fetchone()

            self.assertEqual(row[0], 1)
            self.assertIsNone(row[1])

        finally:
            await connection.close()

    async def test_load_empty_database(self):
        loaded_states = await self.repository.load_all_states()

        self.assertEqual(loaded_states, [])


if __name__ == "__main__":
    unittest.main()
