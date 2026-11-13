"""REST API endpoints for curriculum content generation, draft quarantine, and teacher question editor.

Implements ADR-0004 & Milestone M3:
- POST /api/v1/content-generation/jobs (HTTP 202 Accepted)
- GET /api/v1/content-generation/jobs (HTTP 200 OK)
- GET /api/v1/content-generation/jobs/{job_id} (HTTP 200 OK)
- GET /api/v1/content-generation/jobs/{job_id}/drafts (HTTP 200 OK)
- PATCH /api/v1/content-generation/drafts/{draft_id} (HTTP 200 OK)
- POST /api/v1/content-generation/drafts/{draft_id}/approve (HTTP 200 OK)
- POST /api/v1/content-generation/jobs/{job_id}/approve (HTTP 200 OK)
- POST /api/v1/content-generation/drafts/{draft_id}/reject (HTTP 200 OK)
- GET /api/v1/content-generation/courses (HTTP 200 OK)
- GET /api/v1/content-generation/courses/{course_id}/knowledge-components (HTTP 200 OK)
- GET /api/v1/content-generation/questions (HTTP 200 OK)
- POST /api/v1/content-generation/upload-material (HTTP 200 OK)

Enforces:
- Multi-tenant isolation by institutional boundary.
- Teacher and admin role-based authorization.
- Parametrized PostgreSQL persistence and draft quarantine.
- RFC 7807 Problem Details on domain errors.
- Strict optimistic concurrency and transactional publication into canonical questions.
"""

import hashlib
import logging
import os
import re
import unicodedata
import uuid
from datetime import datetime
from typing import Annotated, Any

import asyncpg
from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from app.content_generation.dependencies import (
    get_database_pool,
    get_draft_repository,
    get_job_repository,
    get_publication_service,
    get_storage_client,
)
from app.content_generation.exceptions import (
    ConcurrencyConflictError,
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
from app.content_generation.repositories.storage_client import (
    InMemoryStorageClient,
    StorageClientProtocol,
)
from app.content_generation.schemas.generated_questions import (
    HTML_TAG_PATTERN,
    BloomTaxonomy,
    QuestionDraftRecord,
)
from app.content_generation.services.document_validation import (
    MAX_FILE_SIZE_BYTES,
    PDF_MAGIC_BYTES,
    ZIP_MAGIC_BYTES,
    validate_storage_authorization,
)
from app.content_generation.services.publication_service import (
    DraftPublicationService,
)
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/content-generation", tags=["Generación de Contenido Docente"])


# ==============================================================================
# Request and Response Pydantic v2 Schemas
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
    updated_at: datetime | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    rejection_reason: str | None = None
    # Presentation aliases for frontend editor integration
    draft_id: str | None = None
    question_type: str = "single_choice"
    difficulty: float = 0.500
    bloom_taxonomy: str = "understand"
    correct_option: str | None = None


class UpdateQuestionDraftOption(BaseModel):
    """An option provided during teacher draft editing."""

    model_config = ConfigDict(extra="forbid")

    text: str = Field(..., min_length=1)
    is_correct: bool
    misconception_explanation: str | None = None


class UpdateQuestionDraftRequest(BaseModel):
    """Teacher edits to a question draft prior to approval."""

    model_config = ConfigDict(extra="forbid")

    question_text: str | None = Field(default=None, min_length=1)
    options: list[UpdateQuestionDraftOption] | None = Field(default=None, min_length=2, max_length=6)
    explanation: str | None = Field(default=None, min_length=1)
    suggested_difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    difficulty: float | None = Field(default=None, ge=0.0, le=1.0)
    suggested_bloom_level: str | None = None
    bloom_taxonomy: str | None = None
    knowledge_component_id: str | None = None
    expected_updated_at: datetime | None = None


class ApproveDraftRequest(BaseModel):
    """Optional payload when individually approving a draft."""

    model_config = ConfigDict(extra="forbid")

    knowledge_component_id: str | None = Field(
        default=None, description="UUID del Knowledge Component institucional a asociar"
    )


class ApproveDraftResponse(BaseModel):
    """Result of draft approval and canonical publication."""

    model_config = ConfigDict(extra="forbid")

    draft_id: str
    approved_question_id: str
    canonical_question_id: str | None = None
    status: str = "approved"
    message: str = "Borrador aprobado y publicado exitosamente en el banco canónico."


class BatchApproveDraftsRequest(BaseModel):
    """Request to batch approve question drafts for a job."""

    model_config = ConfigDict(extra="forbid")

    draft_ids: list[str] = Field(..., min_length=1)
    default_knowledge_component_id: str | None = Field(
        default=None,
        description="ID del componente de conocimiento por defecto para los borradores que no lo tengan asignado",
    )


class BatchApproveDraftsResponse(BaseModel):
    """Result of batch draft approval."""

    model_config = ConfigDict(extra="forbid")

    approved_count: int
    published_question_ids: list[str]


class RejectDraftRequest(BaseModel):
    """Payload when discarding a question draft."""

    model_config = ConfigDict(extra="forbid")

    rejection_reason: str | None = Field(default=None, max_length=500)
    reason: str | None = Field(default=None, max_length=500)

    def get_reason(self) -> str | None:
        return self.rejection_reason or self.reason


class KnowledgeComponentItem(BaseModel):
    """Institutional Knowledge Component available for question mapping."""

    model_config = ConfigDict(extra="forbid")

    id: str
    name: str
    description: str | None = None
    unit_id: str | None = None
    unit_title: str | None = None
    difficulty_prior: float = 0.500


class CourseItem(BaseModel):
    """Academic course entity assigned to a teacher."""

    model_config = ConfigDict(extra="forbid")

    id: str
    code: str
    name: str
    description: str | None = None
    is_active: bool = True


class CanonicalOptionItem(BaseModel):
    """Option belonging to a canonical published question."""

    model_config = ConfigDict(extra="forbid")

    id: str
    option_text: str
    is_correct: bool
    order_index: int


class CanonicalQuestionItem(BaseModel):
    """Published canonical question from the questions table."""

    model_config = ConfigDict(extra="forbid")

    id: str
    tenant_id: str
    knowledge_component_id: str
    knowledge_component_name: str | None = None
    question_text: str
    question_type: str
    explanation: str
    difficulty: float
    is_active: bool
    created_by: str
    created_at: datetime
    options: list[CanonicalOptionItem]
    source_draft_id: str | None = None


class UploadMaterialResponse(BaseModel):
    """Metadata of an uploaded curriculum document."""

    model_config = ConfigDict(extra="forbid")

    storage_path: str
    storage_bucket: str = "teacher-materials"
    original_filename: str
    mime_type: str
    file_size_bytes: int
    file_checksum: str


# ==============================================================================
# Helper Mappers
# ==============================================================================


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


def _map_draft_record_to_item(d: QuestionDraftRecord) -> QuestionDraftItem:
    """Helper to serialize QuestionDraftRecord into QuestionDraftItem API response."""
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
    correct_opt = next((opt["text"] for opt in d.options if opt.get("is_correct")), None)

    return QuestionDraftItem(
        id=d.id,
        draft_id=d.id,
        generation_job_id=d.generation_job_id,
        knowledge_component_id=d.knowledge_component_id,
        suggested_kc_name=d.suggested_kc_name,
        question_text=d.question_text,
        explanation=d.explanation,
        options=options_list,
        suggested_difficulty=d.suggested_difficulty,
        difficulty=d.suggested_difficulty,
        suggested_bloom_level=d.suggested_bloom_level,
        bloom_taxonomy=d.suggested_bloom_level,
        source_references=source_refs_list,
        status=d.status,
        approved_question_id=d.approved_question_id,
        created_at=d.created_at,
        updated_at=d.updated_at,
        reviewed_by=d.reviewed_by,
        reviewed_at=d.reviewed_at,
        rejection_reason=d.rejection_reason,
        question_type=d.question_type or "single_choice",
        correct_option=correct_opt,
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
    if not settings.CONTENT_GENERATION_WORKER_ENABLED:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/content-generation-unavailable",
                "title": "CONTENT_GENERATION_UNAVAILABLE",
                "status": 503,
                "detail": (
                    "El procesamiento asíncrono de materiales curriculares no está disponible en este "
                    "entorno de ejecución (AWS Lambda sin worker activo en segundo plano). Los trabajos "
                    "no se encolan para evitar bloqueos permanentes."
                ),
                "code": "CONTENT_GENERATION_UNAVAILABLE",
            },
        )

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

    effective_course_id = request.course_id
    if not effective_course_id:
        cleaned_path_segs = request.storage_path.strip().replace("\\", "/").strip("/").split("/")
        if len(cleaned_path_segs) >= 3 and cleaned_path_segs[1] != "general":
            effective_course_id = cleaned_path_segs[1]

    if (
        user.role == "teacher"
        and effective_course_id
        and effective_course_id not in user.authorized_course_ids
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
    "/jobs",
    status_code=status.HTTP_200_OK,
    response_model=list[GenerationJobResponse],
    summary="Listar trabajos de generación de preguntas pertenecientes al docente",
)
async def list_generation_jobs(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
    course_id: str | None = Query(default=None, description="Filtrar por curso"),
    status_filter: str | None = Query(default=None, alias="status", description="Filtrar por estado del trabajo"),
    limit: int = Query(default=50, ge=1, le=100, description="Límite de resultados"),
    offset: int = Query(default=0, ge=0, description="Desplazamiento para paginación"),
) -> list[GenerationJobResponse]:
    """Retrieve content generation jobs for the authenticated teacher, strictly isolated by tenant."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar trabajos.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if user.role == "teacher" and course_id and course_id not in user.authorized_course_ids:
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

    jobs, _ = await job_repo.list_jobs(
        tenant_id=user.tenant_id,
        requesting_user_id=user.user_id,
        user_role=user.role,
        authorized_course_ids=user.authorized_course_ids,
        course_id=course_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    items: list[GenerationJobResponse] = []
    for j in jobs:
        drafts = await draft_repo.get_drafts_by_job(job_id=j.id, tenant_id=user.tenant_id)
        items.append(_map_job_record_to_response(j, drafts_count=len(drafts)))
    return items


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
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar este trabajo.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

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
    status_filter: str | None = Query(default=None, alias="status", description="Filtrar por estado del borrador"),
    limit: int | None = Query(default=None, ge=1, le=100, description="Límite de resultados"),
    offset: int | None = Query(default=None, ge=0, description="Desplazamiento para paginación"),
) -> list[QuestionDraftItem]:
    """Retrieve question drafts safely quarantined for a given job and tenant."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar borradores.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

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

    drafts = await draft_repo.get_drafts_by_job(
        job_id=job_id,
        tenant_id=user.tenant_id,
        status=status_filter,
        limit=limit,
        offset=offset,
    )

    return [_map_draft_record_to_item(d) for d in drafts]


@router.patch(
    "/drafts/{draft_id}",
    status_code=status.HTTP_200_OK,
    response_model=QuestionDraftItem,
    summary="Editar borrador de pregunta antes de su publicación",
)
async def update_question_draft(
    draft_id: str,
    request: UpdateQuestionDraftRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
) -> QuestionDraftItem:
    """Updates question draft content, validating structural rules and optimistic concurrency."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para editar borradores.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    # 1. Fetch draft checking tenant boundary
    draft = await draft_repo.get_draft_by_id(draft_id=draft_id, tenant_id=user.tenant_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Borrador No Encontrado",
                "status": 404,
                "detail": f"El borrador de pregunta {draft_id} no existe en su institución.",
                "code": "DRAFT_NOT_FOUND",
            },
        )

    # 2. Check parent job and teacher course authorization
    job = await job_repo.get_job(
        job_id=draft.generation_job_id,
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
                "detail": "El trabajo asociado al borrador no fue encontrado o no está autorizado.",
                "code": "JOB_NOT_FOUND",
            },
        )

    # 3. Check status is editable (draft or edited only; approved and rejected are terminal)
    if draft.status in ("approved", "rejected"):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": "Borrador Ya Procesado",
                "status": 409,
                "detail": f"No se pueden modificar borradores en estado terminal '{draft.status}'.",
                "code": "DRAFT_ALREADY_REVIEWED",
            },
        )

    # 4. Content Validations:
    # 4a. Validate question_text if present
    if request.question_text is not None:
        stripped_q = request.question_text.strip()
        if not stripped_q:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/empty-question-text",
                    "title": "EMPTY_QUESTION_TEXT",
                    "status": 422,
                    "detail": "El enunciado de la pregunta no puede estar vacío.",
                    "code": "EMPTY_QUESTION_TEXT",
                },
            )
        if HTML_TAG_PATTERN.search(stripped_q):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unprocessed-html",
                    "title": "UNPROCESSED_HTML_DETECTED",
                    "status": 422,
                    "detail": "El enunciado no puede contener etiquetas HTML sin procesar.",
                    "code": "UNPROCESSED_HTML_DETECTED",
                },
            )

    # 4b. Validate explanation if present
    if request.explanation is not None:
        stripped_exp = request.explanation.strip()
        if not stripped_exp:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/empty-explanation",
                    "title": "EMPTY_EXPLANATION",
                    "status": 422,
                    "detail": "La explicación formativa no puede estar vacía.",
                    "code": "EMPTY_EXPLANATION",
                },
            )
        if HTML_TAG_PATTERN.search(stripped_exp):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unprocessed-html",
                    "title": "UNPROCESSED_HTML_DETECTED",
                    "status": 422,
                    "detail": "La explicación no puede contener etiquetas HTML sin procesar.",
                    "code": "UNPROCESSED_HTML_DETECTED",
                },
            )

    # 4c. Validate options if present
    options_data: list[dict[str, Any]] | None = None
    if request.options is not None:
        options_count = len(request.options)
        if not (2 <= options_count <= 6):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-options-count",
                    "title": "INVALID_OPTIONS_COUNT",
                    "status": 422,
                    "detail": f"Se requieren entre 2 y 6 alternativas (recibidas: {options_count}).",
                    "code": "INVALID_OPTIONS_COUNT",
                },
            )

        correct_count = sum(1 for opt in request.options if opt.is_correct)
        if correct_count != 1:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-correct-options-count",
                    "title": "INVALID_CORRECT_OPTIONS_COUNT",
                    "status": 422,
                    "detail": f"Debe existir exactamente 1 alternativa correcta (recibidas: {correct_count}).",
                    "code": "INVALID_CORRECT_OPTIONS_COUNT",
                },
            )

        seen_normalized: set[str] = set()
        options_data = []
        for opt in request.options:
            raw_text = opt.text.strip()
            if not raw_text:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "type": "https://api.plataformamicro.edu.pe/errors/empty-option-text",
                        "title": "EMPTY_OPTION_TEXT",
                        "status": 422,
                        "detail": "El texto de la alternativa no puede estar vacío.",
                        "code": "EMPTY_OPTION_TEXT",
                    },
                )
            if HTML_TAG_PATTERN.search(raw_text):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "type": "https://api.plataformamicro.edu.pe/errors/unprocessed-html",
                        "title": "UNPROCESSED_HTML_DETECTED",
                        "status": 422,
                        "detail": "El texto de la alternativa contiene etiquetas HTML sin procesar.",
                        "code": "UNPROCESSED_HTML_DETECTED",
                    },
                )
            normalized = re.sub(
                r"\s+", " ", unicodedata.normalize("NFKC", raw_text).strip().lower()
            )
            if normalized in seen_normalized:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={
                        "type": "https://api.plataformamicro.edu.pe/errors/duplicate-options",
                        "title": "DUPLICATE_OPTIONS",
                        "status": 422,
                        "detail": f"Alternativa duplicada detectada: '{raw_text}'.",
                        "code": "DUPLICATE_OPTIONS",
                    },
                )
            seen_normalized.add(normalized)
            options_data.append({
                "text": raw_text,
                "is_correct": opt.is_correct,
                "misconception_explanation": opt.misconception_explanation,
            })

    # 4d. Validate bloom taxonomy if present
    bloom_val = request.bloom_taxonomy or request.suggested_bloom_level
    if bloom_val is not None:
        valid_blooms = {b.value for b in BloomTaxonomy}
        if bloom_val.lower() not in valid_blooms:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-bloom",
                    "title": "INVALID_BLOOM_TAXONOMY",
                    "status": 422,
                    "detail": f"Nivel de Bloom '{bloom_val}' no válido. Valores admitidos: {sorted(valid_blooms)}",
                    "code": "INVALID_BLOOM_TAXONOMY",
                },
            )
        bloom_val = bloom_val.lower()

    # 4e. Validate difficulty if present
    diff_val = request.difficulty if request.difficulty is not None else request.suggested_difficulty
    if diff_val is not None and not (0.0 <= diff_val <= 1.0):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/invalid-difficulty",
                "title": "INVALID_DIFFICULTY",
                "status": 422,
                "detail": "La dificultad debe ser un valor numérico entre 0.0 y 1.0.",
                "code": "INVALID_DIFFICULTY",
            },
        )

    # 4f. Validate Knowledge Component if present
    if request.knowledge_component_id and pool is not None:
        try:
            kcid = uuid.UUID(request.knowledge_component_id)
            async with pool.acquire() as conn:
                kc_exists = await conn.fetchval(
                    "SELECT 1 FROM knowledge_components WHERE id = $1::uuid AND tenant_id = $2::uuid AND is_active = true;",
                    kcid,
                    uuid.UUID(user.tenant_id),
                )
            if not kc_exists:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={
                        "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                        "title": "KNOWLEDGE_COMPONENT_NOT_FOUND",
                        "status": 404,
                        "detail": f"El Knowledge Component '{request.knowledge_component_id}' no existe en su institución.",
                        "code": "KNOWLEDGE_COMPONENT_NOT_FOUND",
                    },
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-uuid",
                    "title": "INVALID_KC_UUID",
                    "status": 422,
                    "detail": "El formato del Knowledge Component ID es inválido.",
                    "code": "INVALID_KC_UUID",
                },
            ) from e

    # 5. Persist update in draft repository with optimistic concurrency check
    try:
        updated_draft = await draft_repo.update_draft(
            draft_id=draft_id,
            tenant_id=user.tenant_id,
            reviewed_by=user.user_id,
            question_text=request.question_text.strip() if request.question_text else None,
            options=options_data,
            explanation=request.explanation.strip() if request.explanation else None,
            difficulty=diff_val,
            bloom_taxonomy=bloom_val,
            knowledge_component_id=request.knowledge_component_id,
            expected_updated_at=request.expected_updated_at,
        )
    except ConcurrencyConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": "CONCURRENCY_CONFLICT",
                "status": 409,
                "detail": e.message_safe,
                "code": "CONCURRENCY_CONFLICT",
            },
        ) from e
    except InvalidJobStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": e.code,
                "status": 409,
                "detail": e.message_safe,
                "code": e.code,
            },
        ) from e

    return _map_draft_record_to_item(updated_draft)


@router.post(
    "/drafts/{draft_id}/approve",
    status_code=status.HTTP_200_OK,
    response_model=ApproveDraftResponse,
    summary="Aprobar individualmente un borrador de pregunta y publicarlo al banco canónico",
)
async def approve_question_draft(
    draft_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
    publication_service: Annotated[DraftPublicationService, Depends(get_publication_service)],
    request: ApproveDraftRequest | None = None,
) -> ApproveDraftResponse:
    """Publishes approved draft into questions and question_options within an atomic ACID transaction."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para aprobar borradores.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    # 1. Fetch draft to verify existence and tenant isolation
    draft = await draft_repo.get_draft_by_id(draft_id=draft_id, tenant_id=user.tenant_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Borrador No Encontrado",
                "status": 404,
                "detail": f"El borrador de pregunta {draft_id} no existe en su institución.",
                "code": "DRAFT_NOT_FOUND",
            },
        )

    # 2. Verify parent job course authorization for teachers
    job = await job_repo.get_job(
        job_id=draft.generation_job_id,
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
                "detail": "El trabajo asociado al borrador no fue encontrado o no está autorizado.",
                "code": "JOB_NOT_FOUND",
            },
        )

    # 3. Perform atomic ACID publication
    kc_id_to_assign = request.knowledge_component_id if request else None
    try:
        updated_draft, canonical_question_id = await publication_service.approve_draft(
            draft_id=draft_id,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            knowledge_component_id=kc_id_to_assign,
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
                "details": e.details,
            },
        ) from e

    return ApproveDraftResponse(
        draft_id=updated_draft.id,
        approved_question_id=canonical_question_id,
        canonical_question_id=canonical_question_id,
        status="approved",
        message="Borrador aprobado y publicado exitosamente en el banco canónico.",
    )


@router.post(
    "/jobs/{job_id}/approve",
    status_code=status.HTTP_200_OK,
    response_model=BatchApproveDraftsResponse,
    summary="Aprobar y publicar transaccionalmente un lote de borradores al banco canónico",
)
async def batch_approve_drafts(
    job_id: str,
    request: BatchApproveDraftsRequest,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    publication_service: Annotated[DraftPublicationService, Depends(get_publication_service)],
) -> BatchApproveDraftsResponse:
    """Batch approve multiple drafts belonging to a job, returning canonical question IDs."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para aprobar borradores.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

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
                "detail": f"El trabajo {job_id} no existe en su institución.",
                "code": "JOB_NOT_FOUND",
            },
        )

    try:
        count, pub_ids = await publication_service.approve_drafts_batch(
            job_id=job_id,
            draft_ids=request.draft_ids,
            tenant_id=user.tenant_id,
            user_id=user.user_id,
            default_kc_id=request.default_knowledge_component_id,
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
                "details": e.details,
            },
        ) from e

    return BatchApproveDraftsResponse(
        approved_count=count,
        published_question_ids=pub_ids,
    )


@router.post(
    "/drafts/{draft_id}/reject",
    status_code=status.HTTP_200_OK,
    response_model=QuestionDraftItem,
    summary="Rechazar un borrador de pregunta generado por IA",
)
async def reject_question_draft(
    draft_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
    request: RejectDraftRequest | None = None,
) -> QuestionDraftItem:
    """Discards a question draft, preventing its publication and retaining audit metadata."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para descartar borradores.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    draft = await draft_repo.get_draft_by_id(draft_id=draft_id, tenant_id=user.tenant_id)
    if not draft:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/not-found",
                "title": "Borrador No Encontrado",
                "status": 404,
                "detail": f"El borrador de pregunta {draft_id} no existe en su institución.",
                "code": "DRAFT_NOT_FOUND",
            },
        )

    job = await job_repo.get_job(
        job_id=draft.generation_job_id,
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
                "detail": "El trabajo asociado al borrador no fue encontrado o no está autorizado.",
                "code": "JOB_NOT_FOUND",
            },
        )

    try:
        rejected_draft = await draft_repo.reject_draft(
            draft_id=draft_id,
            tenant_id=user.tenant_id,
            reviewed_by=user.user_id,
            rejection_reason=request.get_reason() if request else None,
        )
    except InvalidJobStateTransitionError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/conflict",
                "title": e.code,
                "status": 409,
                "detail": e.message_safe,
                "code": e.code,
            },
        ) from e

    return _map_draft_record_to_item(rejected_draft)


@router.get(
    "/courses",
    status_code=status.HTTP_200_OK,
    response_model=list[CourseItem],
    summary="Listar cursos asignados al docente autenticado",
)
async def list_teacher_courses(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
) -> list[CourseItem]:
    """Retrieve courses assigned to the teacher within the institutional tenant."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar cursos docentes.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if pool is None:
        # In-memory mock response for tests
        return [
            CourseItem(
                id="c0000000-0000-0000-0000-000000000001",
                code="CIEN-5SEC",
                name="Ciencias",
                description="Biología, química y ambiente para 5.° de secundaria",
                is_active=True,
            )
        ]

    try:
        tid = uuid.UUID(user.tenant_id)
        uid = uuid.UUID(user.user_id)
    except ValueError:
        return []

    auth_course_uuids: list[uuid.UUID] = []
    for c in user.authorized_course_ids:
        try:
            auth_course_uuids.append(uuid.UUID(str(c)))
        except ValueError:
            pass

    query = """
    SELECT DISTINCT c.id, c.code, c.name, c.description, c.is_active
    FROM courses c
    LEFT JOIN sections s ON s.course_id = c.id
    WHERE c.tenant_id = $1::uuid
      AND (
          $2::text IN ('admin', 'super_admin')
          OR s.teacher_id = $3::uuid
          OR c.id = ANY($4::uuid[])
      )
    ORDER BY c.name ASC;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, tid, user.role, uid, auth_course_uuids)

    return [
        CourseItem(
            id=str(r["id"]),
            code=str(r["code"]),
            name=str(r["name"]),
            description=r["description"],
            is_active=bool(r["is_active"]),
        )
        for r in rows
    ]


@router.get(
    "/courses/{course_id}/knowledge-components",
    status_code=status.HTTP_200_OK,
    response_model=list[KnowledgeComponentItem],
    summary="Listar componentes de conocimiento disponibles para un curso",
)
async def list_course_knowledge_components(
    course_id: str,
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
) -> list[KnowledgeComponentItem]:
    """Retrieve knowledge components associated with the units of a course."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar componentes de conocimiento.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if user.role == "teacher" and course_id not in user.authorized_course_ids:
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

    if pool is None:
        return [
            KnowledgeComponentItem(
                id="f0000000-0000-0000-0000-000000000001",
                name="Fotosíntesis",
                description="Conversión de energía solar en energía química celular",
                unit_id="b0000000-0000-0000-0000-000000000002",
                unit_title="Nutrición y metabolismo",
                difficulty_prior=0.480,
            )
        ]

    try:
        cid = uuid.UUID(course_id)
        tid = uuid.UUID(user.tenant_id)
    except ValueError:
        return []

    query = """
    SELECT kc.id, kc.name, kc.description, kc.difficulty_prior, u.id AS unit_id, u.title AS unit_title
    FROM knowledge_components kc
    JOIN units u ON u.id = kc.unit_id
    WHERE u.course_id = $1::uuid
      AND kc.tenant_id = $2::uuid
      AND kc.is_active = true
    ORDER BY u.order_index ASC, kc.name ASC;
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(query, cid, tid)

    return [
        KnowledgeComponentItem(
            id=str(r["id"]),
            name=str(r["name"]),
            description=r["description"],
            unit_id=str(r["unit_id"]) if r["unit_id"] else None,
            unit_title=r["unit_title"],
            difficulty_prior=float(r["difficulty_prior"]) if r["difficulty_prior"] is not None else 0.500,
        )
        for r in rows
    ]


@router.get(
    "/questions",
    status_code=status.HTTP_200_OK,
    response_model=list[CanonicalQuestionItem],
    summary="Consultar preguntas canónicas publicadas en el banco institucional",
)
async def list_canonical_questions(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
    course_id: str | None = Query(default=None, description="Filtrar por curso"),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> list[CanonicalQuestionItem]:
    """Retrieve canonical published questions for teacher review and question bank management."""
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para consultar el banco de preguntas.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if user.role == "teacher" and course_id and course_id not in user.authorized_course_ids:
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

    if pool is None:
        return []

    try:
        tid = uuid.UUID(user.tenant_id)
    except ValueError:
        return []

    conditions = ["q.tenant_id = $1::uuid", "q.is_active = true"]
    params: list[object] = [tid]
    idx = 2

    if course_id:
        try:
            cid = uuid.UUID(course_id)
            conditions.append(
                f"EXISTS (SELECT 1 FROM units u WHERE u.id = kc.unit_id AND u.course_id = ${idx}::uuid)"
            )
            params.append(cid)
            idx += 1
        except ValueError:
            return []
    elif user.role == "teacher":
        auth_uuids = [uuid.UUID(str(c)) for c in user.authorized_course_ids]
        conditions.append(
            f"EXISTS (SELECT 1 FROM units u WHERE u.id = kc.unit_id AND u.course_id = ANY(${idx}::uuid[]))"
        )
        params.append(auth_uuids)
        idx += 1

    where_clause = " AND ".join(conditions)
    query = f"""
    SELECT q.id, q.tenant_id, q.knowledge_component_id, q.question_text,
           q.question_type, q.explanation, q.difficulty, q.is_active,
           q.created_by, q.created_at, q.source_draft_id,
           kc.name AS kc_name
    FROM questions q
    JOIN knowledge_components kc ON kc.id = q.knowledge_component_id
    WHERE {where_clause}
    ORDER BY q.created_at DESC
    LIMIT ${idx} OFFSET ${idx + 1};
    """
    params.extend([limit, offset])

    async with pool.acquire() as conn:
        q_rows = await conn.fetch(query, *params)
        if not q_rows:
            return []

        q_ids = [r["id"] for r in q_rows]
        opt_rows = await conn.fetch(
            """
            SELECT id, question_id, option_text, is_correct, order_index
            FROM question_options
            WHERE question_id = ANY($1::uuid[])
            ORDER BY order_index ASC;
            """,
            q_ids,
        )

    options_by_q: dict[str, list[CanonicalOptionItem]] = {}
    for opt in opt_rows:
        qid_str = str(opt["question_id"])
        if qid_str not in options_by_q:
            options_by_q[qid_str] = []
        options_by_q[qid_str].append(
            CanonicalOptionItem(
                id=str(opt["id"]),
                option_text=str(opt["option_text"]),
                is_correct=bool(opt["is_correct"]),
                order_index=int(opt["order_index"]),
            )
        )

    return [
        CanonicalQuestionItem(
            id=str(r["id"]),
            tenant_id=str(r["tenant_id"]),
            knowledge_component_id=str(r["knowledge_component_id"]),
            knowledge_component_name=r["kc_name"],
            question_text=str(r["question_text"]),
            question_type=str(r["question_type"]),
            explanation=str(r["explanation"]),
            difficulty=float(r["difficulty"]) if r["difficulty"] is not None else 0.500,
            is_active=bool(r["is_active"]),
            created_by=str(r["created_by"]),
            created_at=r["created_at"],
            source_draft_id=str(r["source_draft_id"]) if r["source_draft_id"] else None,
            options=options_by_q.get(str(r["id"]), []),
        )
        for r in q_rows
    ]


@router.post(
    "/upload-material",
    status_code=status.HTTP_200_OK,
    response_model=UploadMaterialResponse,
    summary="Cargar material curricular docente en almacenamiento privado",
)
async def upload_material(
    user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    storage_client: Annotated[StorageClientProtocol, Depends(get_storage_client)],
    file: Annotated[UploadFile | None, File()] = None,
    course_id: Annotated[str | None, Form()] = None,
    storage_path: Annotated[str | None, Form()] = None,
    original_filename: Annotated[str | None, Form()] = None,
    mime_type: Annotated[str | None, Form()] = None,
    file_size_bytes: Annotated[int | None, Form()] = None,
    file_checksum: Annotated[str | None, Form()] = None,
    storage_bucket: Annotated[str, Form()] = "teacher-materials",
) -> UploadMaterialResponse:
    """Validates and uploads a curriculum document (PDF/PPTX) into private storage,

    or accepts an already uploaded Supabase Storage reference (storage_path + metadata)
    to avoid large binary payloads traversing AWS Lambda.
    """
    if user.role not in ("teacher", "admin", "super_admin"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                "title": "Acceso Prohibido",
                "status": 403,
                "detail": f"El rol '{user.role}' no cuenta con permisos para cargar materiales.",
                "code": "INSUFFICIENT_PERMISSIONS",
            },
        )

    if user.role == "teacher" and course_id and course_id not in user.authorized_course_ids:
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

    # Path A: Direct binary file upload through endpoint
    if file is not None:
        content = await file.read()
        file_size = len(content)

        if file_size == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-file",
                    "title": "INVALID_FILE_SIGNATURE",
                    "status": 400,
                    "detail": "El archivo recibido está vacío (0 bytes).",
                    "code": "INVALID_FILE_SIGNATURE",
                },
            )

        # AWS Lambda Function URL synchronous payload limit enforcement (6 MB)
        is_lambda = bool(
            os.getenv("AWS_LAMBDA_FUNCTION_NAME")
            or os.getenv("AWS_EXECUTION_ENV")
            or os.getenv("LAMBDA_TASK_ROOT")
            or not settings.ENABLE_CORS_MIDDLEWARE
        )
        if is_lambda and file_size > 6 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/lambda-payload-limit",
                    "title": "LAMBDA_PAYLOAD_LIMIT_EXCEEDED",
                    "status": 413,
                    "detail": (
                        f"El archivo ({file_size} bytes) excede el límite de 6 MB soportado por AWS Lambda "
                        "en modo síncrono/buffered. Para documentos de hasta 30 MB, cárguelos directamente "
                        "al bucket privado de Supabase Storage ('teacher-materials') y envíe la referencia "
                        "'storage_path' al servicio."
                    ),
                    "code": "LAMBDA_PAYLOAD_LIMIT_EXCEEDED",
                },
            )

        if file_size > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/file-too-large",
                    "title": "FILE_TOO_LARGE",
                    "status": 413,
                    "detail": f"El archivo supera el límite de 30 MB (tamaño: {file_size} bytes).",
                    "code": "FILE_TOO_LARGE",
                },
            )

        # Determine MIME type
        filename = file.filename or "uploaded_document"
        detected_mime = file.content_type or ""
        if filename.lower().endswith(".pdf") or content.startswith(PDF_MAGIC_BYTES):
            detected_mime = "application/pdf"
        elif filename.lower().endswith(".pptx") or content.startswith(ZIP_MAGIC_BYTES):
            detected_mime = "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        else:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unsupported-media-type",
                    "title": "UNSUPPORTED_MIME_TYPE",
                    "status": 415,
                    "detail": "Solo se admiten documentos en formato PDF y presentaciones PPTX.",
                    "code": "UNSUPPORTED_MIME_TYPE",
                },
            )

        checksum = hashlib.sha256(content).hexdigest()
        clean_filename = re.sub(r"[^a-zA-Z0-9._-]", "_", filename)
        storage_folder = course_id if course_id else "general"
        computed_path = f"{user.tenant_id}/{storage_folder}/{clean_filename}"

        # If storage client is in-memory, store directly into simulated store
        if isinstance(storage_client, InMemoryStorageClient):
            storage_client.upload_file("teacher-materials", computed_path, content)

        return UploadMaterialResponse(
            storage_path=computed_path,
            storage_bucket="teacher-materials",
            original_filename=filename,
            mime_type=detected_mime,
            file_size_bytes=file_size,
            file_checksum=checksum,
        )

    # Path B: Direct Supabase Storage reference (file already uploaded to Supabase Storage by frontend)
    if storage_path is not None:
        if storage_bucket != "teacher-materials":
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

        try:
            validate_storage_authorization(
                storage_path=storage_path,
                tenant_id=user.tenant_id,
                storage_bucket=storage_bucket,
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

        # Validate course scope if path targets a specific course folder
        effective_path_course = course_id
        if not effective_path_course:
            cleaned_path_segs = storage_path.strip().replace("\\", "/").strip("/").split("/")
            if len(cleaned_path_segs) >= 3 and cleaned_path_segs[1] != "general":
                effective_path_course = cleaned_path_segs[1]

        if (
            user.role == "teacher"
            and effective_path_course
            and effective_path_course not in user.authorized_course_ids
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                    "title": "Curso No Asignado",
                    "status": 403,
                    "detail": "El docente no tiene asignado el curso indicado en la ruta de almacenamiento.",
                    "code": "COURSE_NOT_ASSIGNED",
                },
            )

        allowed_mimes = (
            "application/pdf",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
        if not mime_type or mime_type not in allowed_mimes:
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

        if not file_size_bytes or file_size_bytes <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-file",
                    "title": "Tamaño de Archivo Inválido",
                    "status": 400,
                    "detail": "El tamaño del archivo debe ser mayor a 0 bytes.",
                    "code": "INVALID_FILE_SIZE",
                },
            )

        if file_size_bytes > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/file-too-large",
                    "title": "FILE_TOO_LARGE",
                    "status": 413,
                    "detail": f"El archivo supera el límite de 30 MB (tamaño: {file_size_bytes} bytes).",
                    "code": "FILE_TOO_LARGE",
                },
            )

        if not file_checksum or len(file_checksum) < 32:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/invalid-file",
                    "title": "Checksum Requerido",
                    "status": 400,
                    "detail": "Se requiere un hash SHA-256 válido para el archivo cargado.",
                    "code": "INVALID_CHECKSUM",
                },
            )

        resolved_filename = original_filename or storage_path.split("/")[-1]
        return UploadMaterialResponse(
            storage_path=storage_path,
            storage_bucket=storage_bucket,
            original_filename=resolved_filename,
            mime_type=mime_type,
            file_size_bytes=file_size_bytes,
            file_checksum=file_checksum,
        )

    # Path C: Neither file nor storage_path provided
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail={
            "type": "https://api.plataformamicro.edu.pe/errors/invalid-file",
            "title": "MISSING_FILE_OR_STORAGE_PATH",
            "status": 400,
            "detail": "Debe proporcionar un archivo para carga directa o una referencia 'storage_path' válida en Supabase Storage.",
            "code": "MISSING_FILE_OR_STORAGE_PATH",
        },
    )
