"""FastAPI Application Entry Point for ML-API."""

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import asyncpg
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.activities import router as activities_router
from app.api.v1.content_generation import router as content_generation_router
from app.api.v1.learning import router as learning_router
from app.api.v1.microcontents import router as microcontents_router
from app.api.v1.recommendations import router as recommendations_router
from app.api.v1.teacher_analytics import router as teacher_analytics_router
from app.content_generation.exceptions import ContentGenerationError
from app.content_generation.infrastructure.database import (
    close_db_pool,
    get_db_pool,
)
from app.core.config import settings
from app.core.secrets import get_database_dsn

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Lifespan event handler for database pooling, model loading, and cleanup."""
    # Initialize DB pool if configured
    try:
        if settings.REPOSITORY_BACKEND != "memory":
            dsn = get_database_dsn()
            if dsn:
                await get_db_pool(dsn=dsn)
                logger.info("Database pool initialized in application lifespan.")
    except (OSError, asyncpg.PostgresError) as e:
        logger.warning("Could not connect to database pool at startup: %s", e)
    except RuntimeError as e:
        logger.error("Controlled database initialization failure: %s", e)
        raise

    yield

    # Cleanup on shutdown
    try:
        if settings.REPOSITORY_BACKEND != "memory":
            await close_db_pool()
            logger.info("Database pool closed on application shutdown.")
    except (OSError, asyncpg.PostgresError) as e:
        logger.warning("Error closing database pool: %s", e)



app = FastAPI(
    title="Adaptive Microlearning ML-API",
    version="0.1.0",
    description="Predictive, adaptive and curriculum content generation microservice",
    lifespan=lifespan,
)

# Avoid duplicate Access-Control-Allow-Origin headers in AWS Lambda:
# When deployed to Lambda, Function URL manages CORS headers at the AWS edge.
# FastAPI CORSMiddleware is enabled only for local development/container runs.
is_lambda_runtime = bool(
    os.getenv("AWS_LAMBDA_FUNCTION_NAME")
    or os.getenv("AWS_EXECUTION_ENV")
    or not settings.ENABLE_CORS_MIDDLEWARE
)

if not is_lambda_runtime and settings.ENABLE_CORS_MIDDLEWARE:
    cors_origins_env = os.getenv(
        "CORS_ORIGINS",
        settings.CORS_ORIGINS,
    )
    allowed_origins = [
        origin.strip() for origin in cors_origins_env.split(",") if origin.strip()
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    logger.info("FastAPI CORSMiddleware enabled for origins: %s", allowed_origins)
else:
    logger.info(
        "FastAPI CORSMiddleware disabled: CORS is managed upstream by AWS Function URL."
    )


@app.exception_handler(ContentGenerationError)
async def content_generation_error_handler(
    request: Request,
    exc: ContentGenerationError,
) -> JSONResponse:
    """Format domain exceptions into RFC 7807 Problem Details responses."""
    code_slug = exc.code.lower().replace("_", "-")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": f"https://api.plataformamicro.edu.pe/errors/{code_slug}",
            "title": exc.code,
            "status": exc.status_code,
            "detail": exc.message_safe,
            "code": exc.code,
            "details": exc.details,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request,
    exc: HTTPException,
) -> JSONResponse:
    """Format standard HTTP exceptions into RFC 7807 Problem Details."""
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
            headers=exc.headers,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "type": "https://api.plataformamicro.edu.pe/errors/http-error",
            "title": "HTTP Error",
            "status": exc.status_code,
            "detail": str(exc.detail),
            "code": "HTTP_ERROR",
        },
        headers=exc.headers,
    )


# Health and Liveness Probes
@app.get("/api/v1/health")
async def health_check() -> dict[str, str]:
    """Liveness probe endpoint."""
    return {"status": "ok", "service": "ml-api"}


@app.post("/api/v1/health/warmup")
async def warmup() -> dict[str, str]:
    """Warmup endpoint to mitigate blitz.cloud container cold starts."""
    return {"status": "ready", "warmed": "true"}


# Register API v1 Routers
app.include_router(content_generation_router, prefix="/api/v1")
app.include_router(activities_router, prefix="/api/v1")
app.include_router(learning_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(microcontents_router, prefix="/api/v1")
app.include_router(teacher_analytics_router, prefix="/api/v1")
