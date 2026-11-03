"""Database connection pooling and lifecycle for PostgreSQL/asyncpg."""

import logging
import os
from typing import Any

import asyncpg

logger = logging.getLogger(__name__)

_POOL: asyncpg.Pool | None = None


def normalize_database_url(url: str | None = None) -> str:
    """Normalize SQLAlchemy/standard Postgres URL to asyncpg format."""
    default_url = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
    db_url: str = url or os.getenv("DATABASE_URL") or default_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return db_url


async def get_db_pool(
    dsn: str | None = None,
    min_size: int = 2,
    max_size: int = 10,
    **kwargs: Any,
) -> asyncpg.Pool:
    """Retrieve or initialize the singleton asyncpg Connection Pool."""
    global _POOL
    if _POOL is None or getattr(_POOL, "_closed", True):
        target_dsn = normalize_database_url(dsn)
        _POOL = await asyncpg.create_pool(
            dsn=target_dsn,
            min_size=min_size,
            max_size=max_size,
            **kwargs,
        )
        logger.info("Initialized asyncpg PostgreSQL connection pool.")
    return _POOL


async def close_db_pool() -> None:
    """Close the asyncpg connection pool gracefully."""
    global _POOL
    if _POOL is not None:
        try:
            if not getattr(_POOL, "_closed", True):
                await _POOL.close()
        except (OSError, asyncpg.PostgresError) as e:
            logger.warning("Error closing database pool: %s", e)
        finally:
            _POOL = None
        logger.info("Closed asyncpg PostgreSQL connection pool.")


