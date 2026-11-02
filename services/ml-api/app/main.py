"""FastAPI Application Entry Point for ML-API."""

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for model loading and resource cleanup."""
    # Initialization (e.g. warmup, artifact verification)
    yield
    # Cleanup on shutdown


app = FastAPI(
    title="Adaptive Microlearning ML-API",
    version="0.1.0",
    description="Predictive and adaptive service for student retention and recommendation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/v1/health")
async def health_check() -> Dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "ml-api"}


@app.post("/api/v1/health/warmup")
async def warmup() -> Dict[str, str]:
    """Warmup endpoint to mitigate blitz.cloud container cold starts."""
    return {"status": "ready", "warmed": "true"}
