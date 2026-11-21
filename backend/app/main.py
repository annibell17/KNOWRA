
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import health, cognitive
from .database.database import initialize_database
from .database.repository import LearnerStateRepository


load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialise persistent storage and restore learner states
    whenever the backend starts.
    """

    # 1. Create database tables if they do not already exist.
    await initialize_database()

    # 2. Create the repository.
    repository = LearnerStateRepository()

    # 3. Load previously saved learner states.
    saved_states = await repository.load_all_states()

    # 4. Restore those states into the cognitive engine.
    learner_manager = cognitive.cognitive_pipeline.learner_manager

    for state in saved_states:
        learner_manager.learners.setdefault(
            state.learner_id, {}
        )[state.concept_id] = state

    # 5. Make the repository available to API endpoints.
    app.state.learner_repository = repository

    print(
        f"KNOWRA persistence initialised. "
        f"Restored {len(saved_states)} learner concept states."
    )

    yield


app = FastAPI(
    title="KNOWRA Backend",
    version="0.1.0",
    lifespan=lifespan,
)


# Allow CORS for the frontend during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers.
app.include_router(health.router)
app.include_router(cognitive.router)


@app.get("/ping")
async def ping():
    return {"status": "alive"}
