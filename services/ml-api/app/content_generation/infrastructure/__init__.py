"""Infrastructure adapters and persistence mechanisms for content generation."""

from app.content_generation.infrastructure.database import (
    close_db_pool,
    get_db_pool,
    invalidate_db_pool_and_cached_dsn,
    normalize_database_url,
)
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

__all__ = [
    "GenerationUnitOfWorkProtocol",
    "InMemoryUnitOfWork",
    "PostgresDraftRepository",
    "PostgresJobRepository",
    "PostgresUnitOfWork",
    "close_db_pool",
    "get_db_pool",
    "invalidate_db_pool_and_cached_dsn",
    "normalize_database_url",
]
