"""Repositories package for content generation."""

from app.content_generation.repositories.draft_repository import (
    DraftRepositoryProtocol,
    InMemoryDraftRepository,
)
from app.content_generation.repositories.job_repository import (
    ContentGenerationJobRecord,
    InMemoryJobRepository,
    JobRepositoryProtocol,
)
from app.content_generation.repositories.storage_client import (
    InMemoryStorageClient,
    StorageClientProtocol,
    SupabaseStorageClient,
)

__all__ = [
    "ContentGenerationJobRecord",
    "DraftRepositoryProtocol",
    "InMemoryDraftRepository",
    "InMemoryJobRepository",
    "InMemoryStorageClient",
    "JobRepositoryProtocol",
    "StorageClientProtocol",
    "SupabaseStorageClient",
]
