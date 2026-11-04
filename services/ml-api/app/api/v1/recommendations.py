"""FastAPI router for student retention inference and adaptive recommendations."""

from __future__ import annotations

import logging
from datetime import UTC
from typing import Annotated
from uuid import UUID

import asyncpg
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.adaptation.adaptation_engine import AdaptationEngine
from app.core.auth import AuthenticatedUser, require_role
from app.prediction.inference_service import RetentionInferenceService
from app.schemas.adaptation import (
    AdaptationEvaluationResponse,
    CompleteRecommendationResponse,
    RecommendationItemResponse,
    RecommendationStatusEnum,
)
from app.schemas.prediction import StudentRetentionSummaryResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Recomendaciones y Retención Adaptativa"])


def get_db_pool() -> asyncpg.Pool:
    """Dependency injection for asyncpg pool."""
    from app.content_generation.infrastructure.database import _POOL

    if _POOL is None or getattr(_POOL, "_closed", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Database connection pool is unavailable.",
        )
    return _POOL


def get_inference_service() -> RetentionInferenceService:
    return RetentionInferenceService()


def get_adaptation_engine() -> AdaptationEngine:
    return AdaptationEngine()


@router.get(
    "/students/me/retention",
    response_model=StudentRetentionSummaryResponse,
    summary="Consultar estimaciones de retención del estudiante autenticado",
)
async def get_my_retention(
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student", "admin", "super_admin"))],
    pool: Annotated[asyncpg.Pool, Depends(get_db_pool)],
    inference_service: Annotated[RetentionInferenceService, Depends(get_inference_service)],
    knowledge_component_id: Annotated[UUID | None, Query(description="Filtrar por KC específico")] = None,
    tau: Annotated[float, Query(ge=0.10, le=0.99, description="Umbral de retención crítico")] = 0.650,
) -> StudentRetentionSummaryResponse:
    """Retorna las probabilidades de retención temporal estimadas para los KCs del estudiante."""
    user_uuid = UUID(current_user.user_id)
    tenant_uuid = UUID(current_user.tenant_id)
    return await inference_service.get_student_retention_profile(
        pool=pool,
        student_id=user_uuid,
        tenant_id=tenant_uuid,
        knowledge_component_id=knowledge_component_id,
        tau=tau,
        persist_predictions=True,
    )


@router.get(
    "/students/me/recommendations",
    response_model=list[RecommendationItemResponse],
    summary="Listar recomendaciones activas del estudiante autenticado",
)
async def get_my_recommendations(
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student", "admin", "super_admin"))],
    pool: Annotated[asyncpg.Pool, Depends(get_db_pool)],
    adaptation_engine: Annotated[AdaptationEngine, Depends(get_adaptation_engine)],
    include_completed: Annotated[bool, Query(description="Incluir recomendaciones ya completadas")] = False,
) -> list[RecommendationItemResponse]:
    """Retorna las recomendaciones de repaso espaciado asignadas al estudiante autenticado."""
    user_uuid = UUID(current_user.user_id)
    tenant_uuid = UUID(current_user.tenant_id)
    return await adaptation_engine.get_active_recommendations(
        pool=pool,
        student_id=user_uuid,
        tenant_id=tenant_uuid,
        include_completed=include_completed,
    )


@router.post(
    "/students/me/recommendations/evaluate",
    response_model=AdaptationEvaluationResponse,
    summary="Evaluar estado de retención y programar recomendaciones adaptativas",
)
async def evaluate_my_recommendations(
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student", "admin", "super_admin"))],
    pool: Annotated[asyncpg.Pool, Depends(get_db_pool)],
    inference_service: Annotated[RetentionInferenceService, Depends(get_inference_service)],
    adaptation_engine: Annotated[AdaptationEngine, Depends(get_adaptation_engine)],
    tau: Annotated[float, Query(ge=0.10, le=0.99, description="Umbral crítico de retención")] = 0.650,
) -> AdaptationEvaluationResponse:
    """Evalúa los KCs del estudiante y genera recomendaciones respetando el cooldown anti-fatiga de 24h."""
    user_uuid = UUID(current_user.user_id)
    tenant_uuid = UUID(current_user.tenant_id)

    # 1. Infer retention states
    profile = await inference_service.get_student_retention_profile(
        pool=pool,
        student_id=user_uuid,
        tenant_id=tenant_uuid,
        tau=tau,
        persist_predictions=True,
    )

    # 2. Adaptation policy decision
    return await adaptation_engine.evaluate_and_generate_recommendations(
        pool=pool,
        student_id=user_uuid,
        tenant_id=tenant_uuid,
        retention_predictions=profile.kcs,
        tau=tau,
    )


@router.post(
    "/students/me/recommendations/{recommendation_id}/complete",
    response_model=CompleteRecommendationResponse,
    summary="Registrar cumplimiento de una recomendación de repaso",
)
async def complete_my_recommendation(
    recommendation_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student", "admin", "super_admin"))],
    pool: Annotated[asyncpg.Pool, Depends(get_db_pool)],
    adaptation_engine: Annotated[AdaptationEngine, Depends(get_adaptation_engine)],
) -> CompleteRecommendationResponse:
    """Marca una recomendación como completada tras verificar propiedad y tenant isolation."""
    from datetime import datetime

    user_uuid = UUID(current_user.user_id)
    tenant_uuid = UUID(current_user.tenant_id)
    now = datetime.now(UTC)
    updated = await adaptation_engine.mark_recommendation_completed(
        pool=pool,
        recommendation_id=recommendation_id,
        student_id=user_uuid,
        tenant_id=tenant_uuid,
    )

    if not updated:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://plataformamicro.edu.pe/errors/recommendation-not-found",
                "title": "Recomendación no encontrada",
                "status": 404,
                "detail": f"No se encontró recomendación pendiente con id {recommendation_id} para el usuario activo.",
            },
        )

    return CompleteRecommendationResponse(
        id=recommendation_id,
        status=RecommendationStatusEnum.COMPLETED,
        completed_at=now,
        message="Recomendación completada exitosamente.",
    )
