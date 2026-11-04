"""FastAPI Router for microcontents and content exposure telemetry (Milestone M5.4)."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, require_role
from app.repositories.microcontent_repository import MicrocontentRepository
from app.schemas.microcontents import (
    MicrocontentCreateRequest,
    MicrocontentDetailResponse,
    MicrocontentListItem,
    MicrocontentUpdateRequest,
    RecordExposureRequest,
    RecordExposureResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="", tags=["Gestión de Microcontenidos y Telemetría de Exposición"])


def get_microcontent_repo() -> MicrocontentRepository:
    """Dependency injection for MicrocontentRepository using global database pool."""
    from app.content_generation.infrastructure.database import _POOL

    if _POOL is None or getattr(_POOL, "_closed", True):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/database-unavailable",
                "title": "Servicio no disponible",
                "status": 503,
                "detail": "El pool de conexiones a PostgreSQL no está disponible.",
                "code": "DATABASE_UNAVAILABLE",
            },
        )
    return MicrocontentRepository(pool=_POOL)


@router.get(
    "/microcontents/{microcontent_id}",
    response_model=MicrocontentDetailResponse,
    summary="Obtener detalle de microcontenido para visualización de lectura",
)
async def get_microcontent(
    microcontent_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("student", "teacher", "admin", "super_admin"))
    ],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
) -> MicrocontentDetailResponse:
    """Retrieve full microcontent data. Students can only view published microcontents."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        user_uuid = UUID(current_user.user_id)
        return await repo.get_microcontent_by_id(
            tenant_id=tenant_uuid,
            microcontent_id=microcontent_id,
            user_role=current_user.role,
            user_id=user_uuid,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Microcontenido no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "MICROCONTENT_NOT_FOUND",
            },
        ) from e
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso restringido",
                "status": 403,
                "detail": str(e),
                "code": "MICROCONTENT_NOT_PUBLISHED",
            },
        ) from e


@router.post(
    "/microcontents/{microcontent_id}/exposures",
    response_model=RecordExposureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evento de exposición a microcontenido (alias)",
)
@router.post(
    "/students/me/microcontents/{microcontent_id}/exposures",
    response_model=RecordExposureResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar evento de exposición a microcontenido (initial_study o review_study)",
)
async def record_microcontent_exposure(
    microcontent_id: UUID,
    payload: RecordExposureRequest,
    current_user: Annotated[AuthenticatedUser, Depends(require_role("student"))],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
) -> RecordExposureResponse:
    """Record learning exposure telemetry in append-only content_exposure_events and optionally complete recommendation."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        student_uuid = UUID(current_user.user_id)
        return await repo.record_exposure(
            tenant_id=tenant_uuid,
            student_id=student_uuid,
            microcontent_id=microcontent_id,
            payload=payload,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Microcontenido no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "MICROCONTENT_NOT_FOUND",
            },
        ) from e


@router.get(
    "/microcontents",
    response_model=list[MicrocontentListItem],
    summary="Listar microcontenidos del tenant con filtros curriculares",
)
async def list_microcontents(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
    course_id: Annotated[UUID | None, Query(description="Filtrar por curso")] = None,
    unit_id: Annotated[UUID | None, Query(description="Filtrar por unidad")] = None,
    kc_id: Annotated[UUID | None, Query(description="Filtrar por KC")] = None,
) -> list[MicrocontentListItem]:
    """List microcontents in the teacher's tenant."""
    tenant_uuid = UUID(current_user.tenant_id)
    return await repo.list_microcontents(
        tenant_id=tenant_uuid,
        course_id=course_id,
        unit_id=unit_id,
        kc_id=kc_id,
    )


@router.post(
    "/microcontents",
    response_model=MicrocontentDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Crear borrador de microcontenido",
)
async def create_microcontent(
    payload: MicrocontentCreateRequest,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
) -> MicrocontentDetailResponse:
    """Author a new microcontent in draft state."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        creator_uuid = UUID(current_user.user_id)
        return await repo.create_microcontent(
            tenant_id=tenant_uuid,
            creator_id=creator_uuid,
            payload=payload,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Componente no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "KC_NOT_FOUND",
            },
        ) from e


@router.patch(
    "/microcontents/{microcontent_id}",
    response_model=MicrocontentDetailResponse,
    summary="Actualizar borrador de microcontenido",
)
async def update_microcontent(
    microcontent_id: UUID,
    payload: MicrocontentUpdateRequest,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
) -> MicrocontentDetailResponse:
    """Update microcontent fields."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        return await repo.update_microcontent(
            tenant_id=tenant_uuid,
            microcontent_id=microcontent_id,
            payload=payload,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Microcontenido no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "MICROCONTENT_NOT_FOUND",
            },
        ) from e


@router.post(
    "/microcontents/{microcontent_id}/publish",
    response_model=MicrocontentDetailResponse,
    summary="Publicar microcontenido para estudiantes",
)
async def publish_microcontent(
    microcontent_id: UUID,
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[MicrocontentRepository, Depends(get_microcontent_repo)],
) -> MicrocontentDetailResponse:
    """Publish microcontent to enrolled students."""
    try:
        tenant_uuid = UUID(current_user.tenant_id)
        return await repo.publish_microcontent(
            tenant_id=tenant_uuid,
            microcontent_id=microcontent_id,
        )
    except KeyError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Microcontenido no encontrado",
                "status": 404,
                "detail": str(e),
                "code": "MICROCONTENT_NOT_FOUND",
            },
        ) from e
