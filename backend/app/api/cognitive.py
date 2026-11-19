
from fastapi import APIRouter
from pydantic import BaseModel, Field

from ..cognitive_engine.bkt import BayesianKnowledgeTracer
from ..cognitive_engine.retention import RetentionModel


router = APIRouter(
    prefix="/cognitive",
    tags=["Cognitive Engine"]
)


# -------------------------
# Bayesian Knowledge Tracing
# -------------------------

class BKTUpdateRequest(BaseModel):
    prior_knowledge: float = Field(ge=0, le=1)
    correct: bool


@router.post("/bkt/update")
async def update_knowledge(request: BKTUpdateRequest):
    tracer = BayesianKnowledgeTracer()

    result = tracer.update(
        prior_knowledge=request.prior_knowledge,
        correct=request.correct
    )

    return result


# -------------------------
# Memory Retention
# -------------------------

class RetentionEstimateRequest(BaseModel):
    initial_retention: float = Field(ge=0, le=1)
    elapsed_days: float = Field(ge=0)


@router.post("/retention/estimate")
async def estimate_retention(request: RetentionEstimateRequest):
    model = RetentionModel()

    result = model.estimate(
        initial_retention=request.initial_retention,
        elapsed_days=request.elapsed_days
    )

    return result
