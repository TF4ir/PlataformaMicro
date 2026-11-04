"""FastAPI Router for Student Learning Flow, Attempts, and Answer Events (Milestone M4)."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, status

from app.core.auth import AuthenticatedUser, require_role
from app.repositories.learning_repository import LearningRepository
from app.schemas.learning import (
    AttemptResultsResponse,
    StartAttemptRequest,
    StartAttemptResponse,
    StudentActivityDetail,
    StudentActivityListItem,
    StudentCourseItem,
    SubmitAnswerRequest,
    SubmitAnswerResponse,
    SubmitAttemptResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Flujo de Aprendizaje del Estudiante"])


def get_learning_repo() -> LearningRepository:
    """Dependency injection for LearningRepository using current database pool."""
    from app.content_generation.infrastructure.database import _POOL

    if _POOL is None or getattr(_POOL, "_closed", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/database-unavailable",
                "title": "Base de datos no disponible",
                "status": 503,
                "detail": "El pool de conexiones a PostgreSQL no está inicializado.",
                "code": "DATABASE_UNAVAILABLE",
            },
        )
    return LearningRepository(pool=_POOL)


@router.get(
    "/students/me/courses",
    response_model=list[StudentCourseItem],
    summary="Listar cursos matriculados del estudiante",
)
async def list_student_courses(
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> list[StudentCourseItem]:
    """Retrieve enrolled courses and assigned sections for the authenticated student."""
    tenant_uuid = UUID(current_user.tenant_id)
    student_uuid = UUID(current_user.user_id)
    return await repo.list_student_courses(
        tenant_id=tenant_uuid,
        student_id=student_uuid,
    )


@router.get(
    "/students/me/activities",
    response_model=list[StudentActivityListItem],
    summary="Listar actividades asignadas al estudiante",
)
async def list_student_activities(
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> list[StudentActivityListItem]:
    """Retrieve published activities assigned to student's enrolled sections."""
    tenant_uuid = UUID(current_user.tenant_id)
    student_uuid = UUID(current_user.user_id)
    return await repo.list_student_activities(
        tenant_id=tenant_uuid,
        student_id=student_uuid,
    )


@router.get(
    "/students/me/activities/{activity_id}",
    response_model=StudentActivityDetail,
    summary="Obtener cuestionario seguro para el estudiante",
)
async def get_student_activity(
    activity_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> StudentActivityDetail:
    """Retrieve sanitized activity questions without leaking answers or teacher explanations."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        student_uuid = UUID(current_user.user_id)
        return await repo.get_student_activity_detail(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            activity_id=activity_id,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Actividad no disponible",
                "status": 404,
                "detail": str(e),
                "code": "ACTIVITY_NOT_FOUND_OR_ENROLLED",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no permitido",
                "status": 403,
                "detail": str(e),
                "code": "ACTIVITY_NOT_ACCESSIBLE",
            },
        ) from e


@router.post(
    "/students/me/activities/{activity_id}/attempts",
    response_model=StartAttemptResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Iniciar o reanudar intento de actividad",
)
async def start_attempt(
    activity_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
    payload: StartAttemptRequest | None = None,
    x_idempotency_key: Annotated[UUID | None, Header(alias="X-Idempotency-Key")] = None,
) -> StartAttemptResponse:
    """Safely start a new attempt or return the existing in-progress attempt."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        student_uuid = UUID(current_user.user_id)
        idempotency_uuid = x_idempotency_key or (payload.idempotency_key if payload else None)

        return await repo.start_attempt(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            activity_id=activity_id,
            idempotency_key=idempotency_uuid,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Intento no permitido",
                "status": 403,
                "detail": str(e),
                "code": "ATTEMPT_NOT_PERMITTED",
            },
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/validation-error",
                "title": "Error de disponibilidad",
                "status": 422,
                "detail": str(e),
                "code": "ACTIVITY_SCHEDULE_ERROR",
            },
        ) from e


@router.post(
    "/students/me/attempts/{attempt_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar respuesta y evaluar (answer_events inmutable)",
)
@router.post(
    "/learning/attempts/{attempt_id}/answers",
    response_model=SubmitAnswerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar respuesta (ruta canónica ADR-0003)",
)
async def submit_answer(
    attempt_id: UUID,
    payload: SubmitAnswerRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
    x_idempotency_key: Annotated[UUID | None, Header(alias="X-Idempotency-Key")] = None,
) -> SubmitAnswerResponse:
    """Record student response in append-only answer_events table with backend validation of correctness."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        student_uuid = UUID(current_user.user_id)
        if x_idempotency_key and not payload.idempotency_key:
            payload.idempotency_key = x_idempotency_key

        return await repo.record_answer(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            attempt_id=attempt_id,
            payload=payload,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Intento no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "ATTEMPT_NOT_FOUND",
            },
        ) from e
    except ValueError as e:
        msg = str(e)
        status_to_use = (
            status.HTTP_409_CONFLICT
            if "already completed" in msg
            else status.HTTP_422_UNPROCESSABLE_CONTENT
        )
        raise HTTPException(
            status_code=status_to_use,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/validation-error",
                "title": "Error de validación de respuesta",
                "status": status_to_use,
                "detail": msg,
                "code": "ANSWER_VALIDATION_ERROR",
            },
        ) from e


@router.post(
    "/students/me/attempts/{attempt_id}/submit",
    response_model=SubmitAttemptResponse,
    summary="Finalizar y calificar intento de actividad",
)
async def submit_attempt(
    attempt_id: UUID,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> SubmitAttemptResponse:
    """Finalize the attempt, evaluate total score based on answer_events, and lock session."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        student_uuid = UUID(current_user.user_id)
        return await repo.submit_attempt(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            attempt_id=attempt_id,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Intento no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "ATTEMPT_NOT_FOUND",
            },
        ) from e


@router.get(
    "/students/me/attempts/{attempt_id}/results",
    response_model=AttemptResultsResponse,
    summary="Consultar resultados y retroalimentación del intento",
)
async def get_attempt_results(
    attempt_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("student", "teacher", "admin", "super_admin"))
    ],
    repo: Annotated[LearningRepository, Depends(get_learning_repo)],
) -> AttemptResultsResponse:
    """Retrieve full attempt results including question review and Knowledge Component breakdown."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.get_attempt_results(
            tenant_id=tenant_uuid,
            user_id=user_uuid,
            role=current_user.role,
            attempt_id=attempt_id,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Intento no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "ATTEMPT_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso prohibido",
                "status": 403,
                "detail": str(e),
                "code": "FORBIDDEN_ATTEMPT_ACCESS",
            },
        ) from e
