"""Database connection pooling and lifecycle for PostgreSQL/asyncpg.

Configured for high resilience on Google Cloud Run and Supabase / Supavisor:
- Automatic detection of Session Mode (port 5432) vs Transaction Mode (port 6543).
- Enforces statement_cache_size=0 when Transaction Mode is active to prevent
  DuplicatePreparedStatementError on Supavisor connection multiplexing.
- Conservative pool sizing (min_size=1, max_size=5) to prevent connection pool
  exhaustion across multi-instance Cloud Run scaling.
- Transparent SSL negotiation ('require' for remote/Supabase endpoints, disabled for localhost).
- Strict credential masking in all log output (no secrets leaked).
"""

from __future__ import annotations

import asyncio
import logging
import urllib.parse
from typing import Any

import asyncpg

from app.core.config import settings

logger = logging.getLogger(__name__)

_POOL: asyncpg.Pool | None = None
_POOL_LOCK: asyncio.Lock | None = None


def _get_pool_lock() -> asyncio.Lock:
    """Lazy initialization of async lock to avoid event-loop binding issues at import time."""
    global _POOL_LOCK
    if _POOL_LOCK is None:
        _POOL_LOCK = asyncio.Lock()
    return _POOL_LOCK


def sanitize_database_url(url: str | None) -> str:
    """Mask credentials and sensitive tokens in database URL to guarantee leak-free logging.

    Preserves brackets for IPv6 hostnames and handles URLs with or without scheme,
    passwords, ports, or sensitive query parameters.
    """
    from app.core.secrets import mask_database_dsn

    return mask_database_dsn(url)


def normalize_database_url(url: str | None = None) -> str:
    """Normalize SQLAlchemy/asyncpg connection string formats to asyncpg DSN."""
    from app.core.secrets import get_database_dsn

    default_url = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
    db_url: str = url or get_database_dsn() or default_url
    if db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "postgresql://", 1)
    return db_url


def resolve_pool_configuration(
    dsn: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    statement_cache_size: int | None = None,
    ssl: Any = None,
    **kwargs: Any,
) -> tuple[str, dict[str, Any], str]:
    """Resolve DSN, asyncpg connect arguments, and pooler mode.

    Evaluates Session Mode (5432) first as required for persistent Cloud Run APIs.
    Transaction Mode (6543) is detected when explicitly configured or when port 6543 is specified.

    Returns:
        (clean_dsn, connect_kwargs, pooler_mode)
    """
    raw_dsn = normalize_database_url(dsn)
    parsed = urllib.parse.urlsplit(raw_dsn)

    # 1. Strip query string from DSN to prevent DSN parser collisions in asyncpg
    clean_dsn = urllib.parse.urlunsplit(
        (parsed.scheme, parsed.netloc, parsed.path, "", "")
    )
    query_params = urllib.parse.parse_qs(parsed.query)

    # 2. Determine pooler mode (session vs transaction)
    # Default Postgres/Supabase port is 5432 (Session Mode). Port 6543 indicates Supavisor Transaction Mode.
    configured_mode = getattr(settings, "DB_POOL_MODE", "auto").lower()
    effective_port = parsed.port or 5432
    if configured_mode in ("session", "transaction"):
        mode = configured_mode
    elif effective_port == 6543:
        mode = "transaction"
    else:
        # Evaluate Session Mode first per architecture guidelines
        mode = "session"

    # 3. Determine statement_cache_size
    # In Transaction Mode (6543), prepared statements cannot be cached because
    # Supavisor dispatches successive queries across different backend connections.
    final_statement_cache_size: int | None = 100
    if statement_cache_size is not None:
        final_statement_cache_size = statement_cache_size
    elif getattr(settings, "DB_STATEMENT_CACHE_SIZE", None) is not None:
        final_statement_cache_size = settings.DB_STATEMENT_CACHE_SIZE
    elif mode == "transaction":
        final_statement_cache_size = 0
    else:
        final_statement_cache_size = 100

    # 4. Determine SSL configuration
    final_ssl = ssl
    if final_ssl is None:
        ssl_mode_cfg = getattr(settings, "DB_SSL_MODE", "auto").lower()
        if ssl_mode_cfg == "require":
            final_ssl = "require"
        elif ssl_mode_cfg == "disable":
            final_ssl = None
        else:
            # Auto: inspect query param first, then check whether host is remote
            sslmode_param = query_params.get("sslmode", [None])[0]
            if sslmode_param == "disable":
                final_ssl = None
            elif sslmode_param in ("require", "verify-ca", "verify-full"):
                final_ssl = "require"
            else:
                is_local = parsed.hostname in ("127.0.0.1", "localhost", "0.0.0.0", "::1", None)
                final_ssl = None if is_local else "require"

    # 5. Determine pool min and max sizes
    resolved_min = min_size if min_size is not None else getattr(settings, "DB_POOL_MIN_SIZE", 1)
    resolved_max = max_size if max_size is not None else getattr(settings, "DB_POOL_MAX_SIZE", 5)

    # 6. Timeouts and serverless connection recycling
    command_timeout = kwargs.pop("command_timeout", getattr(settings, "DB_COMMAND_TIMEOUT", 30.0))
    connect_timeout = kwargs.pop("timeout", getattr(settings, "DB_CONNECT_TIMEOUT", 10.0))
    max_inactive_connection_lifetime = kwargs.pop(
        "max_inactive_connection_lifetime",
        getattr(settings, "DB_MAX_INACTIVE_CONNECTION_LIFETIME", 300.0),
    )
    max_queries = kwargs.pop(
        "max_queries",
        getattr(settings, "DB_MAX_QUERIES", 50000),
    )

    connect_kwargs: dict[str, Any] = {
        "min_size": resolved_min,
        "max_size": resolved_max,
        "statement_cache_size": final_statement_cache_size,
        "command_timeout": command_timeout,
        "timeout": connect_timeout,
        "max_inactive_connection_lifetime": max_inactive_connection_lifetime,
        "max_queries": max_queries,
        **kwargs,
    }
    if final_ssl is not None:
        connect_kwargs["ssl"] = final_ssl

    return clean_dsn, connect_kwargs, mode


def get_current_db_pool() -> asyncpg.Pool | None:
    """Return currently active asyncpg Pool if initialized and not closed, else None."""
    if _POOL is None or getattr(_POOL, "_closed", True):
        return None
    return _POOL


async def get_db_pool(
    dsn: str | None = None,
    min_size: int | None = None,
    max_size: int | None = None,
    statement_cache_size: int | None = None,
    ssl: Any = None,
    **kwargs: Any,
) -> asyncpg.Pool:
    """Retrieve or initialize the singleton asyncpg Connection Pool.

    Applies environment-safe connection pooling, transaction-mode statement cache
    handling, masked credential logging, and double-checked concurrency locking.
    """
    global _POOL
    if _POOL is None or getattr(_POOL, "_closed", True):
        async with _get_pool_lock():
            if _POOL is None or getattr(_POOL, "_closed", True):
                clean_dsn, connect_kwargs, mode = resolve_pool_configuration(
                    dsn=dsn,
                    min_size=min_size,
                    max_size=max_size,
                    statement_cache_size=statement_cache_size,
                    ssl=ssl,
                    **kwargs,
                )

                sanitized_url = sanitize_database_url(clean_dsn)
                logger.info(
                    "Initializing asyncpg PostgreSQL pool (%s mode) to %s (min=%d, max=%d, statement_cache_size=%s, ssl=%s)",
                    mode,
                    sanitized_url,
                    connect_kwargs.get("min_size"),
                    connect_kwargs.get("max_size"),
                    connect_kwargs.get("statement_cache_size"),
                    "ssl" in connect_kwargs,
                )

                try:
                    _POOL = await asyncpg.create_pool(
                        dsn=clean_dsn,
                        **connect_kwargs,
                    )
                    logger.info("Initialized asyncpg PostgreSQL connection pool successfully.")
                except Exception as exc:
                    logger.error(
                        "Failed to initialize asyncpg pool for %s: %s",
                        sanitized_url,
                        exc,
                    )
                    if isinstance(
                        exc,
                        (
                            asyncpg.InvalidPasswordError,
                            asyncpg.InvalidAuthorizationSpecificationError,
                        ),
                    ):
                        from app.core.secrets import invalidate_cached_dsn

                        invalidate_cached_dsn()
                    raise
    return _POOL


async def close_db_pool() -> None:
    """Close the asyncpg connection pool gracefully."""
    global _POOL
    if _POOL is not None:
        try:
            pool_loop = getattr(_POOL, "_loop", None)
            if pool_loop is not None and pool_loop.is_closed():
                _POOL.terminate()
            elif not getattr(_POOL, "_closed", True):
                await _POOL.close()
        except (OSError, asyncpg.PostgresError, RuntimeError) as e:
            logger.warning("Error closing database pool: %s", e)
        finally:
            _POOL = None
        logger.info("Closed asyncpg PostgreSQL connection pool.")


async def invalidate_db_pool_and_cached_dsn() -> None:
    """Invalidate cached database DSN and cleanly terminate the database pool.

    Enables immediate recovery and re-authentication when database credentials rotate.
    """
    from app.core.secrets import invalidate_cached_dsn

    await close_db_pool()
    invalidate_cached_dsn()
