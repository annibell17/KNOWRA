# backend/app/api/health.py

from fastapi import APIRouter

router = APIRouter()

@router.get("/health", tags=["Health"])
async def health_check():
    """Simple health endpoint used by monitoring tools."""
    return {"status": "ok"}
