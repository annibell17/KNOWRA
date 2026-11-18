# backend/app/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables from .env if present
load_dotenv()

app = FastAPI(
    title="KNOWRA Backend",
    version="0.1.0",
)

# Allow CORS for the frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_ORIGIN", "*")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .api import health

app.include_router(health.router)

# Placeholder for future Cognition Engine import
# from .cognitive_engine import engine

@app.get("/ping")
async def ping():
    return {"status": "alive"}
