"""FastAPI Router for teacher dashboard, student roster, courses, and reports telemetry (Milestone M5.4)."""

from __future__ import annotations

import logging
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.core.auth import AuthenticatedUser, require_role
from app.repositories.teacher_repository import TeacherRepository
from app.schemas.teacher_analytics import (
    TeacherCourseDetail,
    TeacherDashboardResponse,
    TeacherReportsResponse,
    TeacherStudentRecord,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teacher", tags=["Analítica y Gestión Docente"])


def get_teacher_repo() -> TeacherRepository:
    """Dependency injection for TeacherRepository using global database pool."""
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
    return TeacherRepository(pool=_POOL)


@router.get(
    "/dashboard",
    response_model=TeacherDashboardResponse,
    summary="Consultar métricas agregadas del panel docente",
)
async def get_teacher_dashboard(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[TeacherRepository, Depends(get_teacher_repo)],
    section_id: Annotated[UUID | None, Query(description="Filtrar por sección")] = None,
) -> TeacherDashboardResponse:
    """Retrieve KPIs, proficiency distribution, and section statistics for teacher."""
    tenant_uuid = UUID(current_user.tenant_id)
    user_uuid = UUID(current_user.user_id)
    return await repo.get_teacher_dashboard(
        tenant_id=tenant_uuid,
        teacher_id=user_uuid,
        role=current_user.role,
        section_id=section_id,
    )


@router.get(
    "/courses",
    response_model=list[TeacherCourseDetail],
    summary="Listar cursos asignados al docente con secciones, unidades y KCs",
)
async def get_teacher_courses(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[TeacherRepository, Depends(get_teacher_repo)],
) -> list[TeacherCourseDetail]:
    """Retrieve courses assigned to the teacher with full curricular tree."""
    tenant_uuid = UUID(current_user.tenant_id)
    user_uuid = UUID(current_user.user_id)
    return await repo.get_teacher_courses(
        tenant_id=tenant_uuid,
        teacher_id=user_uuid,
        role=current_user.role,
    )


@router.get(
    "/students",
    response_model=list[TeacherStudentRecord],
    summary="Directorio de estudiantes de las secciones asignadas al docente",
)
async def get_teacher_students(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[TeacherRepository, Depends(get_teacher_repo)],
    section_id: Annotated[UUID | None, Query(description="Filtrar por sección")] = None,
    search: Annotated[str | None, Query(description="Búsqueda por nombre o código")] = None,
) -> list[TeacherStudentRecord]:
    """Retrieve student roster for teacher's sections."""
    tenant_uuid = UUID(current_user.tenant_id)
    user_uuid = UUID(current_user.user_id)
    return await repo.get_teacher_students(
        tenant_id=tenant_uuid,
        teacher_id=user_uuid,
        role=current_user.role,
        section_id=section_id,
        search=search,
    )


@router.get(
    "/reports",
    response_model=TeacherReportsResponse,
    summary="Reportes avanzados de retención, mapa de calor y trayectoria",
)
async def get_teacher_reports(
    current_user: Annotated[
        AuthenticatedUser, Depends(require_role("teacher", "admin", "super_admin"))
    ],
    repo: Annotated[TeacherRepository, Depends(get_teacher_repo)],
    section_id: Annotated[UUID | None, Query(description="Filtrar por sección")] = None,
    course_id: Annotated[UUID | None, Query(description="Filtrar por curso")] = None,
) -> TeacherReportsResponse:
    """Retrieve telemetry report, mastery heatmap, and forgetting trajectory."""
    tenant_uuid = UUID(current_user.tenant_id)
    user_uuid = UUID(current_user.user_id)
    return await repo.get_teacher_reports(
        tenant_id=tenant_uuid,
        teacher_id=user_uuid,
        role=current_user.role,
        section_id=section_id,
        course_id=course_id,
    )
