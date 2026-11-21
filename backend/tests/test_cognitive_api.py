
import asyncio
import tempfile
import unittest

from unittest.mock import AsyncMock, patch

from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app, lifespan
from app.api.cognitive import create_demo_pipeline
from app.database.repository import LearnerStateRepository
from app.database.database import initialize_database


class TestCognitiveAPI(unittest.TestCase):

    def setUp(self):
        self.temp_directory = tempfile.TemporaryDirectory()

        self.database_path = (
            Path(self.temp_directory.name) / "test_knowra.db"
        )

        self.repository = LearnerStateRepository(
            database_path=self.database_path
        )

        self.pipeline = create_demo_pipeline()

        self.pipeline_patcher = patch(
            "app.api.cognitive.cognitive_pipeline",
            self.pipeline,
        )
        self.pipeline_patcher.start()

        async def initialise_test_database():
            await initialize_database(self.database_path)

        import asyncio
        asyncio.run(initialise_test_database())

        app.state.learner_repository = self.repository

        self.client = TestClient(app)

    def tearDown(self):
        self.client.close()
        self.pipeline_patcher.stop()
        self.temp_directory.cleanup()

    def test_correct_answer_returns_success(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "learner_test_01",
                "question_id": "demo_equation_01",
                "selected_option_id": "b",
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertTrue(data["diagnosis"]["is_correct"])
        self.assertEqual(data["state_update"]["attempts"], 1)
        self.assertEqual(data["state_update"]["correct_attempts"], 1)

    def test_incorrect_answer_detects_misconception(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "learner_test_02",
                "question_id": "demo_equation_01",
                "selected_option_id": "a",
            },
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertFalse(data["diagnosis"]["is_correct"])
        self.assertTrue(
            data["state_update"]["misconception_recorded"]
        )

    def test_repeated_answers_update_learner_progress(self):
        payload = {
            "learner_id": "learner_test_03",
            "question_id": "demo_equation_01",
            "selected_option_id": "b",
        }

        self.client.post(
            "/cognitive/answer/submit",
            json=payload,
        )

        response = self.client.post(
            "/cognitive/answer/submit",
            json=payload,
        )

        self.assertEqual(response.status_code, 200)

        data = response.json()

        self.assertEqual(data["state_update"]["attempts"], 2)
        self.assertEqual(data["state_update"]["correct_attempts"], 2)

    def test_unknown_question_returns_404(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "learner_test_04",
                "question_id": "unknown_question",
                "selected_option_id": "a",
            },
        )

        self.assertEqual(response.status_code, 404)

        self.assertEqual(
            response.json()["detail"],
            "Unknown question ID.",
        )

    def test_invalid_request_returns_422(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "",
                "question_id": "demo_equation_01",
                "selected_option_id": "b",
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_answer_submission_is_persisted(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "persistent_learner",
                "question_id": "demo_equation_01",
                "selected_option_id": "a",
            },
        )

        self.assertEqual(response.status_code, 200)

        import asyncio

        async def inspect_database():
            states = await self.repository.load_all_states()

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
                    ("persistent_learner",),
                ) as cursor:
                    events = await cursor.fetchall()

                return states, events

            finally:
                await connection.close()

        states, events = asyncio.run(inspect_database())

        self.assertEqual(len(states), 1)
        self.assertEqual(states[0].attempts, 1)
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][6], "sign_error")

    def test_saved_state_can_be_restored_into_new_pipeline(self):
        response = self.client.post(
            "/cognitive/answer/submit",
            json={
                "learner_id": "restart_learner",
                "question_id": "demo_equation_01",
                "selected_option_id": "b",
            },
        )

        self.assertEqual(response.status_code, 200)

        import asyncio

        async def load_saved_states():
            return await self.repository.load_all_states()

        saved_states = asyncio.run(load_saved_states())

        # Simulate a fresh cognitive engine after a restart.
        restored_pipeline = create_demo_pipeline()

        for state in saved_states:
            restored_pipeline.learner_manager.learners.setdefault(
                state.learner_id, {}
            )[state.concept_id] = state

        restored_state = (
            restored_pipeline.learner_manager.get_state(
                "restart_learner",
                "equations",
            )
        )

        self.assertEqual(restored_state.attempts, 1)
        self.assertEqual(restored_state.correct_attempts, 1)

    def test_startup_restores_saved_learner_states(self):
        # Create a separate pipeline containing previously saved progress.
        previous_pipeline = create_demo_pipeline()

        previous_pipeline.process_answer(
            learner_id="startup_learner",
            question_id="demo_equation_01",
            selected_option_id="b",
        )

        saved_state = previous_pipeline.learner_manager.get_state(
            "startup_learner",
            "equations",
        )

        # Simulate a fresh application with an empty learner manager.
        fresh_pipeline = create_demo_pipeline()

        repository = type(
            "FakeRepository",
            (),
            {
                "load_all_states": AsyncMock(
                    return_value=[saved_state]
                )
            },
        )()

        previous_repository = getattr(
            app.state,
            "learner_repository",
            None,
        )

        async def run_startup_test():
            with (
                patch(
                    "app.main.initialize_database",
                    new_callable=AsyncMock,
                ) as mock_initialize,
                patch(
                    "app.main.LearnerStateRepository",
                    return_value=repository,
                ),
                patch(
                    "app.api.cognitive.cognitive_pipeline",
                    fresh_pipeline,
                ),
            ):
                async with lifespan(app):
                    mock_initialize.assert_awaited_once()

                    restored_state = (
                        fresh_pipeline.learner_manager.get_state(
                            "startup_learner",
                            "equations",
                        )
                    )

                    self.assertEqual(restored_state.attempts, 1)
                    self.assertEqual(
                        restored_state.correct_attempts,
                        1,
                    )

                    repository.load_all_states.assert_awaited_once()

        try:
            asyncio.run(run_startup_test())
        finally:
            if previous_repository is not None:
                app.state.learner_repository = previous_repository
            elif hasattr(app.state, "learner_repository"):
                del app.state.learner_repository

if __name__ == "__main__":
    unittest.main()
