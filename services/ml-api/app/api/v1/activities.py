"""FastAPI Router for Activities and Teacher Questionnaire Management (Milestone M4)."""

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, require_role
from app.repositories.activity_repository import ActivityRepository
from app.schemas.activities import (
    ActivityCreateRequest,
    ActivityDetailResponse,
    ActivityListItem,
    ActivityResultsResponse,
    ActivityStatus,
    ActivityUpdateRequest,
    CourseSectionItem,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Gestión Docente de Cuestionarios"])


def get_activity_repo() -> ActivityRepository:
    """Dependency injection for ActivityRepository using current database pool."""
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
    return ActivityRepository(pool=_POOL)


@router.get(
    "/courses/{course_id}/sections",
    response_model=list[CourseSectionItem],
    summary="Listar secciones de un curso para asignación de cuestionarios",
)
async def list_course_sections(
    course_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> list[CourseSectionItem]:
    """List sections of a course in the tenant for assignment by teachers."""
    tenant_uuid = UUID(current_user.tenant_id)
    user_uuid = UUID(current_user.user_id)
    return await repo.list_course_sections(
        tenant_id=tenant_uuid,
        course_id=course_id,
        teacher_id=user_uuid,
        role=current_user.role,
    )


@router.post(
    "/activities",
    response_model=ActivityDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear cuestionario / actividad en borrador",
)
async def create_activity(
    payload: ActivityCreateRequest,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> ActivityDetailResponse:
    """Create a new pedagogical activity from approved institutional questions in draft status."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.create_activity(
            tenant_id=tenant_uuid,
            created_by=user_uuid,
            payload=payload,
            role=current_user.role,
            authorized_course_ids=current_user.authorized_course_ids,
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no autorizado",
                "status": 403,
                "detail": str(e),
                "code": "COURSE_NOT_AUTHORIZED",
            },
        ) from e
    except ValueError as e:
        logger.warning("Validation error creating activity: %s", e)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/validation-error",
                "title": "Error de validación",
                "status": 422,
                "detail": str(e),
                "code": "ACTIVITY_VALIDATION_ERROR",
            },
        ) from e
    except Exception as e:
        logger.error("Internal error creating activity: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/internal-error",
                "title": "Error interno",
                "status": 500,
                "detail": "No se pudo crear la actividad educativa.",
                "code": "INTERNAL_SERVER_ERROR",
            },
        ) from e



@router.patch(
    "/activities/{activity_id}",
    response_model=ActivityDetailResponse,
    summary="Modificar borrador de actividad",
)
async def update_activity(
    activity_id: UUID,
    payload: ActivityUpdateRequest,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> ActivityDetailResponse:
    """Update activity metadata or question associations. Rejects question changes if attempts exist."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.update_activity(
            tenant_id=tenant_uuid,
            activity_id=activity_id,
            payload=payload,
            user_id=user_uuid,
            role=current_user.role,
            authorized_course_ids=current_user.authorized_course_ids,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Actividad no encontrada",
                "status": 404,
                "detail": str(e),
                "code": "ACTIVITY_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no autorizado",
                "status": 403,
                "detail": str(e),
                "code": "COURSE_NOT_AUTHORIZED",
            },
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": "Conflicto de modificación",
                "status": 409,
                "detail": str(e),
                "code": "ACTIVITY_HAS_ATTEMPTS",
            },
        ) from e


@router.post(
    "/activities/{activity_id}/publish",
    response_model=ActivityDetailResponse,
    summary="Publicar actividad atómicamente",
)
async def publish_activity(
    activity_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> ActivityDetailResponse:
    """Atomically transition activity to published status, making it visible to enrolled students."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.publish_activity(
            tenant_id=tenant_uuid,
            activity_id=activity_id,
            user_id=user_uuid,
            role=current_user.role,
            authorized_course_ids=current_user.authorized_course_ids,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Actividad no encontrada",
                "status": 404,
                "detail": str(e),
                "code": "ACTIVITY_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no autorizado",
                "status": 403,
                "detail": str(e),
                "code": "COURSE_NOT_AUTHORIZED",
            },
        ) from e
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/validation-error",
                "title": "Error de publicación",
                "status": 422,
                "detail": str(e),
                "code": "ACTIVITY_CANNOT_BE_PUBLISHED",
            },
        ) from e


@router.get(
    "/activities",
    response_model=list[ActivityListItem],
    summary="Listar actividades para el docente",
)
async def list_activities(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
    course_id: Annotated[
        UUID | None, Query(description="Filtrar por curso")
    ] = None,
    status: Annotated[
        ActivityStatus | None, Query(description="Filtrar por estado")
    ] = None,
) -> list[ActivityListItem]:
    """List activities for teacher's courses with participation counts and sections."""
    tenant_uuid = UUID(current_user.tenant_id)
    teacher_uuid = UUID(current_user.user_id)
    return await repo.list_teacher_activities(
        tenant_id=tenant_uuid,
        teacher_id=teacher_uuid,
        role=current_user.role,
        course_id=course_id,
        status=status,
    )


@router.get(
    "/activities/{activity_id}",
    response_model=ActivityDetailResponse,
    summary="Detalle completo de una actividad",
)
async def get_activity(
    activity_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> ActivityDetailResponse:
    """Get full activity details including questions and pedagogical metadata."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.get_activity_by_id(
            tenant_id=tenant_uuid,
            activity_id=activity_id,
            user_id=user_uuid,
            role=current_user.role,
            authorized_course_ids=current_user.authorized_course_ids,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Actividad no encontrada",
                "status": 404,
                "detail": str(e),
                "code": "ACTIVITY_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no autorizado",
                "status": 403,
                "detail": str(e),
                "code": "COURSE_NOT_AUTHORIZED",
            },
        ) from e


@router.get(
    "/activities/{activity_id}/results",
    response_model=ActivityResultsResponse,
    summary="Resultados y analítica de actividad para el docente",
)
async def get_activity_results(
    activity_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[ActivityRepository, Depends(get_activity_repo)],
) -> ActivityResultsResponse:
    """Retrieve aggregate participation, score distribution, question accuracy, and KC mastery."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.get_activity_results(
            tenant_id=tenant_uuid,
            activity_id=activity_id,
            user_id=user_uuid,
            role=current_user.role,
            authorized_course_ids=current_user.authorized_course_ids,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Actividad no encontrada",
                "status": 404,
                "detail": str(e),
                "code": "ACTIVITY_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso no autorizado",
                "status": 403,
                "detail": str(e),
                "code": "COURSE_NOT_AUTHORIZED",
            },
        ) from e

