
import logging

from datetime import datetime
from ..content_loader import load_learning_content

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from ..cognitive_engine.bkt import BayesianKnowledgeTracer
from ..cognitive_engine.retention import RetentionModel
from ..cognitive_engine.concept_graph import Concept, ConceptGraph
from ..cognitive_engine.learner_state import LearnerStateManager
from ..cognitive_engine.misconceptions import (
    DiagnosticQuestion,
    MisconceptionDetector,
    MisconceptionRule,
)
from ..cognitive_engine.recommendation_engine import (
    AdaptiveRecommendationEngine,
)
from ..cognitive_engine.learning_pipeline import (
    CognitiveLearningPipeline,
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/cognitive",
    tags=["Cognitive Engine"],
)


def create_demo_pipeline():
    graph = ConceptGraph()

    graph.register_concept(
        Concept("arithmetic", "Arithmetic")
    )

    graph.register_concept(
        Concept(
            "variables",
            "Variables",
            prerequisites=["arithmetic"],
        )
    )

    graph.register_concept(
        Concept(
            "equations",
            "Linear Equations",
            prerequisites=["variables"],
        )
    )

    detector = MisconceptionDetector()

    detector.register_question(
        DiagnosticQuestion(
            question_id="demo_equation_01",
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
    )

    learner_manager = LearnerStateManager()

    recommendation_engine = AdaptiveRecommendationEngine(
        concept_graph=graph,
        learner_manager=learner_manager,
    )

    return CognitiveLearningPipeline(
        misconception_detector=detector,
        learner_manager=learner_manager,
        recommendation_engine=recommendation_engine,
    )


# Load the production learning module once.
learning_content = load_learning_content()


def create_content_pipeline(content=None):
    """
    Build the production cognitive pipeline from loaded learning content.
    """

    content = content or learning_content

    learner_manager = LearnerStateManager()

    recommendation_engine = AdaptiveRecommendationEngine(
        concept_graph=content.concept_graph,
        learner_manager=learner_manager,
    )

    return CognitiveLearningPipeline(
        misconception_detector=content.misconception_detector,
        learner_manager=learner_manager,
        recommendation_engine=recommendation_engine,
    )


# The application uses the real JSON-backed learning module.
cognitive_pipeline = create_content_pipeline()
@router.get("/learners/{learner_id}/progress")
async def get_learner_progress(learner_id: str):
    """
    Return the current progress of a learner across concepts.
    """

    learner_concepts = (
        cognitive_pipeline.learner_manager.learners.get(learner_id)
    )

    if not learner_concepts:
        raise HTTPException(
            status_code=404,
            detail="Learner progress not found.",
        )

    concepts = []

    for concept_id, state in learner_concepts.items():
        concepts.append(
            {
                "concept_id": concept_id,
                "concept_name": (
                    learning_content.concept_graph
                    .concepts[concept_id].name
                ),
                "knowledge_probability": (
                    state.knowledge_probability
                ),
                "attempts": state.attempts,
                "correct_attempts": state.correct_attempts,
                "misconception_history": (
                    state.misconception_history
                ),
                "last_attempt_at": (
                    state.last_attempt_at.isoformat()
                    if state.last_attempt_at
                    else None
                ),
                "retention": (
                    cognitive_pipeline.learner_manager
                    .estimate_retention(learner_id, concept_id)
                ),
                "retention_anchor_at": (
                    state.retention_anchor_at.isoformat()
                    if state.retention_anchor_at
                    else None
                ),
            }
        )

    return {
        "learner_id": learner_id,
        "total_concepts_attempted": len(concepts),
        "concepts": concepts,
    }
@router.get("/modules")
async def get_modules():
    """
    Return available learning module information.
    """

    concepts = [
        {
            "concept_id": concept.concept_id,
            "name": concept.name,
            "description": concept.description,
            "prerequisites": concept.prerequisites,
        }
        for concept in learning_content.concept_graph.concepts.values()
    ]

    return {
        "module_id": learning_content.module_id,
        "title": learning_content.title,
        "description": learning_content.description,
        "concepts": concepts,
    }
@router.get("/questions")
async def get_questions(concept_id: str | None = None):
    """
    Return learner-facing questions without exposing answer keys.
    """

    questions = []

    for question in learning_content.questions.values():

        if concept_id and question["concept_id"] != concept_id:
            continue

        questions.append(
            {
                "question_id": question["question_id"],
                "concept_id": question["concept_id"],
                "difficulty": question["difficulty"],
                "type": question["type"],
                "prompt": question["prompt"],
                "options": question["options"],
                "tags": question["tags"],
            }
        )

    if concept_id and concept_id not in learning_content.concept_graph.concepts:
        raise HTTPException(
            status_code=404,
            detail="Unknown concept ID.",
        )

    return {
        "module_id": learning_content.module_id,
        "total_questions": len(questions),
        "questions": questions,
    }


class BKTUpdateRequest(BaseModel):
    prior_knowledge: float = Field(ge=0, le=1)
    correct: bool


@router.post("/bkt/update")
async def update_knowledge(request: BKTUpdateRequest):
    tracer = BayesianKnowledgeTracer()

    return tracer.update(
        prior_knowledge=request.prior_knowledge,
        correct=request.correct,
    )


class RetentionEstimateRequest(BaseModel):
    initial_retention: float = Field(ge=0, le=1)
    elapsed_days: float = Field(ge=0)


@router.post("/retention/estimate")
async def estimate_retention(request: RetentionEstimateRequest):
    model = RetentionModel()

    return model.estimate(
        initial_retention=request.initial_retention,
        elapsed_days=request.elapsed_days,
    )


class AnswerSubmissionRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=128)
    question_id: str = Field(min_length=1, max_length=128)
    selected_option_id: str = Field(min_length=1, max_length=128)
    timestamp: datetime | None = None


@router.post("/answer/submit")
async def submit_answer(
    request: AnswerSubmissionRequest,
    http_request: Request,
):
    try:
        # Process the answer through KNOWRA's cognitive engine.
        result = cognitive_pipeline.process_answer(
            learner_id=request.learner_id,
            question_id=request.question_id,
            selected_option_id=request.selected_option_id,
            timestamp=request.timestamp,
        )

        # Retrieve the updated learner state.
        learner_state = cognitive_pipeline.learner_manager.get_state(
            result["learner_id"],
            result["concept_id"],
        )

        # Retrieve the repository initialised during application startup.
        repository = http_request.app.state.learner_repository

        # Extract the diagnosis details.
        diagnosis = result["diagnosis"]

        # Persist the learner state and answer event atomically.
        await repository.save_submission(
            state=learner_state,
            question_id=result["question_id"],
            selected_option_id=request.selected_option_id,
            is_correct=diagnosis["is_correct"],
            misconception_id=diagnosis["diagnosis"],
            submitted_at=datetime.fromisoformat(
                result["processed_at"]
            ),
        )

        return result

    except ValueError as error:
        message = str(error)

        if message == "Unknown question ID.":
            raise HTTPException(
                status_code=404,
                detail=message,
            )

        raise HTTPException(
            status_code=400,
            detail=message,
        )

    except Exception:
        logger.exception(
            "Failed to process or persist an answer submission."
        )

        raise HTTPException(
            status_code=500,
            detail="Unable to persist answer submission.",
        )
