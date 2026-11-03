"""REST API endpoints for curriculum content generation and draft quarantine.

Implements ADR-0004:
- POST /api/v1/content-generation/jobs (HTTP 202 Accepted)
- GET /api/v1/content-generation/jobs/{job_id} (HTTP 200 OK)
- GET /api/v1/content-generation/jobs/{job_id}/drafts (HTTP 200 OK)

Enforces:
- Multi-tenant isolation by institutional boundary.
- Teacher and admin role-based authorization.
- Parametrized PostgreSQL persistence and draft quarantine.
- RFC 7807 Problem Details on domain errors.
"""

import logging
import uuid
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict, Field

from app.content_generation.dependencies import (
    get_draft_repository,
    get_job_repository,
)
from app.content_generation.exceptions import (
    ContentGenerationError,
    InvalidJobStateTransitionError,
)
from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    JobRepositoryProtocol,
)
from app.content_generation.services.document_validation import (
    validate_storage_authorization,
)
from app.core.auth import AuthenticatedUser, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-generation", tags=["Generación de Contenido Docente"])


# ==============================================================================
# Request and Response Pydantic v2 Schemas (aligned with openapi.json)
# ==============================================================================


class CreateGenerationJobRequest(BaseModel):
    """Payload to request assisted question generation from uploaded curriculum materials."""

    model_config = ConfigDict(extra="forbid")

    storage_path: str = Field(
        ...,
        description="Ruta relativa del archivo en el bucket privado teacher-materials",
    )
    original_filename: str = Field(
        ...,
        min_length=1,
        description="Nombre original del archivo PDF o PPTX cargado",
    )
    mime_type: str = Field(
        ...,
        description="Tipo MIME verificado del documento",
    )
    file_size_bytes: int = Field(
        ...,
        ge=1,
        le=31457280,
        description="Tamaño del archivo en bytes (límite 30 MB)",
    )
    file_checksum: str = Field(
        ...,
        min_length=32,
        description="Hash SHA-256 del contenido del archivo para integridad e idempotencia",
    )
    course_id: str | None = Field(
        default=None,
        description="UUID del curso curricular asociado (opcional)",
    )
    unit_id: str | None = Field(
        default=None,
        description="UUID de la unidad curricular (opcional)",
    )
    storage_bucket: str = Field(
        default="teacher-materials",
        description="Nombre del bucket privado en Supabase Storage",
    )
    target_num_questions: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Número de reactivos solicitados",
    )
    provider: str = Field(
        default="mock",
        description="Proveedor LLM seleccionado",
    )
    model_id: str = Field(
        default="mock-v1",
        description="Identificador del modelo LLM",
    )


class GenerationJobResponse(BaseModel):
    """Processing and lifecycle status telemetry for a content generation job."""

    model_config = ConfigDict(extra="forbid")

    job_id: str
    tenant_id: str
    course_id: str | None = None
    unit_id: str | None = None
    created_by: str
    status: str
    original_filename: str
    total_drafts_count: int = 0
    provider: str
    model_id: str
    error_code: str | None = None
    error_message_safe: str | None = None
    error_message: str | None = None
    created_at: datetime
    completed_at: datetime | None = None
    updated_at: datetime | None = None


class QuestionDraftOptionResponse(BaseModel):
    """An option or distractor within a generated draft question."""

    model_config = ConfigDict(extra="forbid")

    text: str
    is_correct: bool
    misconception_explanation: str | None = None


class QuestionDraftSourceReferenceResponse(BaseModel):
    """Provenance citation to the source document page or slide."""

    model_config = ConfigDict(extra="forbid")

    type: str
    index: int
    snippet: str


class QuestionDraftItem(BaseModel):
    """AI-generated question draft in quarantine awaiting teacher review."""

    model_config = ConfigDict(extra="forbid")

    id: str
    generation_job_id: str
    knowledge_component_id: str | None = None
    suggested_kc_name: str
    question_text: str
    explanation: str
    options: list[QuestionDraftOptionResponse]
    suggested_difficulty: float = 0.500
    suggested_bloom_level: str = "understand"
    source_references: list[QuestionDraftSourceReferenceResponse]
    status: str = "draft"
    approved_question_id: str | None = None
    created_at: datetime | None = None


def _map_job_record_to_response(
    job: ContentGenerationJobRecord,
    drafts_count: int = 0,
) -> GenerationJobResponse:
    """Helper to convert domain record into API response schema."""
    return GenerationJobResponse(
        job_id=job.id,
        tenant_id=job.tenant_id,
        course_id=job.course_id,
        unit_id=job.unit_id,
        created_by=job.created_by,
        status=job.status,
        original_filename=job.original_filename,
        total_drafts_count=drafts_count,
        provider=job.provider,
        model_id=job.model_id,
        error_code=job.error_code,
        error_message_safe=job.error_message_safe,
        error_message=job.error_message_safe,
        created_at=job.created_at or datetime.now(),
        completed_at=job.completed_at,
        updated_at=job.updated_at,
    )


# ==============================================================================
# Endpoint Implementations
# ==============================================================================


@router.post(
    "/jobs",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=GenerationJobResponse,
    summary="Crear trabajo de generación de preguntas asistido por IA",
)
async def create_generation_job(
    request: CreateGenerationJobRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
) -> GenerationJobResponse:
    """Enqueues a new content generation job in PostgreSQL after validating tenant and storage security."""
    # 1. Role validation: Only teachers, admins, and super_admins can trigger generation
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para crear trabajos de generación.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    # 2. Storage bucket guard
    if request.storage_bucket != "teacher-materials":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/invalid-storage",
                "title": "Bucket No Permitido",
                "status": 400,
                "detail": "Los materiales docentes deben almacenarse en el bucket 'teacher-materials'.",
                "code": "INVALID_STORAGE_BUCKET",
            },
        )

    # 3. MIME type validation
    allowed_mimes = (
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    )
    if request.mime_type not in allowed_mimes:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/unsupported-media-type",
                "title": "Tipo de Medio No Soportado",
                "status": 415,
                "detail": "Solo se admiten documentos en formato PDF y presentaciones PPTX.",
                "code": "UNSUPPORTED_MIME_TYPE",
            },
        )

    # 4. Storage path security and tenant boundary isolation check
    try:
        validate_storage_authorization(
            storage_path=request.storage_path,
            tenant_id=user.tenant_id,
            storage_bucket=request.storage_bucket,
        )
    except ContentGenerationError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "type": f"https://api.plataformamicro.edu.pe/errors/{e.code.lower().replace('_', '-')}",
                "title": e.code,
                "status": e.status_code,
                "detail": e.message_safe,
                "code": e.code,
            },
        ) from e

    # 5. Teacher assigned course check
    if (
        user.role == "teacher"
        and request.course_id
        and request.course_id not in user.authorized_course_ids
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Curso No Asignado",
                "status": 403,
                "detail": "El docente no tiene asignado el curso solicitado.",
                "code": "COURSE_NOT_ASSIGNED",
            },
        )

    # 6. Instantiate domain record
    new_job_id = str(uuid.uuid4())
    job_record = ContentGenerationJobRecord(
        id=new_job_id,
        tenant_id=user.tenant_id,
        created_by=user.user_id,
        storage_bucket=request.storage_bucket,
        storage_path=request.storage_path,
        original_filename=request.original_filename,
        mime_type=request.mime_type,
        file_size_bytes=request.file_size_bytes,
        file_checksum=request.file_checksum,
        status="queued",
        provider=request.provider,
        model_id=request.model_id,
        course_id=request.course_id,
        unit_id=request.unit_id,
    )

    # 7. Persist to PostgreSQL
    try:
        created_job = await job_repo.create_job(job_record)
    except InvalidJobStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": "Conflicto de Idempotencia",
                "status": 409,
                "detail": e.message_safe,
                "code": "ACTIVE_JOB_ALREADY_EXISTS",
            },
        ) from e

    return _map_job_record_to_response(created_job, drafts_count=0)


@router.get(
    "/jobs/{job_id}",
    status_code=status.HTTP_200_OK,
    response_model=GenerationJobResponse,
    summary="Consultar estado y telemetría de un trabajo de generación",
)
async def get_generation_job(
    job_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
) -> GenerationJobResponse:
    """Fetch status and metadata for a generation job, strictly isolated by tenant."""
    # 1. Fetch job ensuring tenant boundary
    job = await job_repo.get_job(
        job_id=job_id,
        tenant_id=user.tenant_id,
        requesting_user_id=user.user_id,
        user_role=user.role,
        authorized_course_ids=user.authorized_course_ids,
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Trabajo No Encontrado",
                "status": 404,
                "detail": f"El trabajo de generación con ID {job_id} no existe o no pertenece a su institución.",
                "code": "JOB_NOT_FOUND",
            },
        )

    # 2. Count existing drafts
    drafts = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=user.tenant_id)

    return _map_job_record_to_response(job, drafts_count=len(drafts))


@router.get(
    "/jobs/{job_id}/drafts",
    status_code=status.HTTP_200_OK,
    response_model=list[QuestionDraftItem],
    summary="Listar borradores de preguntas generados por un trabajo",
)
async def list_drafts_by_job(
    job_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
) -> list[QuestionDraftItem]:
    """Retrieve question drafts safely quarantined for a given job and tenant."""
    # 1. Verify parent job exists and belongs to the requesting tenant
    job = await job_repo.get_job(
        job_id=job_id,
        tenant_id=user.tenant_id,
        requesting_user_id=user.user_id,
        user_role=user.role,
        authorized_course_ids=user.authorized_course_ids,
    )
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Trabajo No Encontrado",
                "status": 404,
                "detail": f"El trabajo de generación {job_id} no existe en su institución.",
                "code": "JOB_NOT_FOUND",
            },
        )

    # 2. Retrieve drafts for tenant
    drafts = await draft_repo.get_drafts_by_job(job_id=job_id, tenant_id=user.tenant_id)

    # 3. Serialize to QuestionDraftItem response models
    items: list[QuestionDraftItem] = []
    for d in drafts:
        options_list = [
            QuestionDraftOptionResponse(
                text=opt["text"],
                is_correct=opt["is_correct"],
                misconception_explanation=opt.get("misconception_explanation"),
            )
            for opt in d.options
        ]
        source_refs_list = [
            QuestionDraftSourceReferenceResponse(
                type=ref["type"],
                index=ref["index"],
                snippet=ref.get("snippet", ""),
            )
            for ref in d.source_references
        ]
        items.append(
            QuestionDraftItem(
                id=d.id,
                generation_job_id=d.generation_job_id,
                knowledge_component_id=d.knowledge_component_id,
                suggested_kc_name=d.suggested_kc_name,
                question_text=d.question_text,
                explanation=d.explanation,
                options=options_list,
                suggested_difficulty=d.suggested_difficulty,
                suggested_bloom_level=d.suggested_bloom_level,
                source_references=source_refs_list,
                status=d.status,
                approved_question_id=d.approved_question_id,
                created_at=d.created_at,
            )
        )

    return items
