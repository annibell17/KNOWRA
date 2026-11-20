
from datetime import datetime
from fastapi import APIRouter, HTTPException
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


router = APIRouter(
    prefix="/cognitive",
    tags=["Cognitive Engine"],
)


# --------------------------------
# Shared cognitive pipeline
# --------------------------------

def create_demo_pipeline():
    """
    Build a clearly labelled demo learning environment.

    These concepts and questions are test fixtures,
    not a production question bank.
    """

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


# One shared instance for the running application.
cognitive_pipeline = create_demo_pipeline()


# --------------------------------
# Bayesian Knowledge Tracing
# --------------------------------

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


# --------------------------------
# Memory Retention
# --------------------------------

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


# --------------------------------
# Complete cognitive pipeline
# --------------------------------

class AnswerSubmissionRequest(BaseModel):
    learner_id: str = Field(min_length=1, max_length=128)
    question_id: str = Field(min_length=1, max_length=128)
    selected_option_id: str = Field(min_length=1, max_length=128)
    timestamp: datetime | None = None


@router.post("/answer/submit")
async def submit_answer(request: AnswerSubmissionRequest):
    try:
        result = cognitive_pipeline.process_answer(
            learner_id=request.learner_id,
            question_id=request.question_id,
            selected_option_id=request.selected_option_id,
            timestamp=request.timestamp,
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
