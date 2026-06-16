"""
OneAI Orchestration Platform - FastAPI Application Entry Point
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings

# Create the FastAPI app
app = FastAPI(
    title="OneAI Orchestration Platform",
    description="AI orchestration system with intelligent task routing",
    version="1.0.0",
)

# Allow frontend to call the API (CORS)
origins = [o.strip() for o in settings.cors_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register all API routes under /api prefix
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "message": "OneAI Orchestration Platform API",
        "docs": "/docs",
        "health": "/api/health",
    }
