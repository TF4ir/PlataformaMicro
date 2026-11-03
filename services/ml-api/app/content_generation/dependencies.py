"""FastAPI dependency providers for content generation services and repositories."""

from typing import Annotated

import asyncpg
from fastapi import Depends

from app.content_generation.infrastructure.database import get_db_pool
from app.content_generation.infrastructure.postgres_draft_repository import (
    PostgresDraftRepository,
)
from app.content_generation.infrastructure.postgres_job_repository import (
    PostgresJobRepository,
)
from app.content_generation.infrastructure.unit_of_work import (
    GenerationUnitOfWorkProtocol,
    InMemoryUnitOfWork,
    PostgresUnitOfWork,
)
from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
    InMemoryDraftRepository,
)
from app.content_generation.repositories.job_repository import (
    InMemoryJobRepository,
    JobRepositoryProtocol,
)
from app.content_generation.repositories.storage_client import (
    InMemoryStorageClient,
    StorageClientProtocol,
    SupabaseStorageClient,
)
from app.content_generation.services.draft_validation_service import (
    DraftValidationService,
)
from app.content_generation.services.extraction_service import (
    DocumentExtractionService,
)
from app.content_generation.services.generation_orchestrator import (
    GenerationOrchestrator,
)
from app.content_generation.services.question_generation_service import (
    QuestionGenerationService,
)
from app.core.config import settings

# In-memory singletons for test/memory runtime execution
_IN_MEMORY_JOB_REPO = InMemoryJobRepository()
_IN_MEMORY_DRAFT_REPO = InMemoryDraftRepository()
_IN_MEMORY_STORAGE_CLIENT = InMemoryStorageClient()


def get_in_memory_job_repository() -> InMemoryJobRepository:
    """Return in-memory job repository for testing."""
    return _IN_MEMORY_JOB_REPO


def get_in_memory_draft_repository() -> InMemoryDraftRepository:
    """Return in-memory draft repository for testing."""
    return _IN_MEMORY_DRAFT_REPO


def get_in_memory_storage_client() -> InMemoryStorageClient:
    """Return in-memory storage client for testing."""
    return _IN_MEMORY_STORAGE_CLIENT


async def get_database_pool() -> asyncpg.Pool | None:
    """Dependency providing the shared asyncpg connection pool if in postgres mode."""
    if settings.REPOSITORY_BACKEND == "memory":
        return None
    return await get_db_pool(dsn=settings.DATABASE_URL)


async def get_job_repository(
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
) -> JobRepositoryProtocol:
    """Dependency providing the active JobRepositoryProtocol adapter."""
    if settings.REPOSITORY_BACKEND == "memory" or pool is None:
        return get_in_memory_job_repository()
    return PostgresJobRepository(pool)


async def get_draft_repository(
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
) -> DraftRepositoryProtocol:
    """Dependency providing the active DraftRepositoryProtocol adapter."""
    if settings.REPOSITORY_BACKEND == "memory" or pool is None:
        return get_in_memory_draft_repository()
    return PostgresDraftRepository(pool)


async def get_unit_of_work(
    pool: Annotated[asyncpg.Pool | None, Depends(get_database_pool)],
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
) -> GenerationUnitOfWorkProtocol:
    """Dependency providing the transactional Unit of Work."""
    if isinstance(job_repo, InMemoryJobRepository) and isinstance(draft_repo, InMemoryDraftRepository):
        return InMemoryUnitOfWork(job_repository=job_repo, draft_repository=draft_repo)
    if pool is not None and isinstance(draft_repo, PostgresDraftRepository):
        return PostgresUnitOfWork(pool, draft_repository=draft_repo)
    if pool is not None:
        return PostgresUnitOfWork(pool)
    return InMemoryUnitOfWork(
        job_repository=get_in_memory_job_repository(),
        draft_repository=get_in_memory_draft_repository(),
    )


def get_storage_client() -> StorageClientProtocol:
    """Dependency providing the authorized StorageClientProtocol adapter."""
    if settings.REPOSITORY_BACKEND == "memory":
        return get_in_memory_storage_client()
    return SupabaseStorageClient(
        supabase_url=settings.SUPABASE_URL,
        service_role_key=settings.SUPABASE_SERVICE_ROLE_KEY,
    )


async def get_generation_orchestrator(
    job_repo: Annotated[JobRepositoryProtocol, Depends(get_job_repository)],
    draft_repo: Annotated[DraftRepositoryProtocol, Depends(get_draft_repository)],
    storage_client: Annotated[StorageClientProtocol, Depends(get_storage_client)],
    uow: Annotated[GenerationUnitOfWorkProtocol, Depends(get_unit_of_work)],
) -> GenerationOrchestrator:
    """Dependency providing the configured GenerationOrchestrator."""
    extraction_service = DocumentExtractionService(
        job_repository=job_repo,
        storage_client=storage_client,
    )
    validation_service = DraftValidationService()
    generation_service = QuestionGenerationService(validation_service=validation_service)
    return GenerationOrchestrator(
        job_repository=job_repo,
        extraction_service=extraction_service,
        generation_service=generation_service,
        draft_repository=draft_repo,
        unit_of_work=uow,
    )
