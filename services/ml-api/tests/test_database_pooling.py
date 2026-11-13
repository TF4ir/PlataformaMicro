"""Comprehensive tests for PostgreSQL connection pooling and Supavisor resilience.

Verifies:
- Masking of secrets in logging and URL normalization (leak-free).
- Auto-detection and explicit configuration of Session Mode (port 5432) vs Transaction Mode (port 6543).
- Enforcement of statement_cache_size=0 in Transaction Mode.
- SSL negotiation for local vs remote hosts.
- Pool lifecycle: initialization, query execution, and graceful closure.
- Error handling without leaking credentials in exception or logs.
"""

import logging
from unittest.mock import patch

import asyncpg
import pytest

from app.content_generation.infrastructure.database import (
    close_db_pool,
    get_db_pool,
    resolve_pool_configuration,
    sanitize_database_url,
)
from app.core.config import settings

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"


class TestDatabaseUrlSanitization:
    """Verifies that secrets are never leaked in logs or string representations."""

    def test_masks_password_in_standard_url(self) -> None:
        raw = "postgresql://postgres:mysecretpassword123@db.supabase.co:5432/postgres"
        sanitized = sanitize_database_url(raw)
        assert "mysecretpassword123" not in sanitized
        assert "postgres:***@db.supabase.co:5432" in sanitized

    def test_masks_password_with_special_characters(self) -> None:
        raw = "postgresql://admin:p%40ssw%3Ard!@aws-0-sa-east-1.pooler.supabase.com:6543/postgres?sslmode=require"
        sanitized = sanitize_database_url(raw)
        assert "p%40ssw%3Ard!" not in sanitized
        assert ":***@" in sanitized
        assert "sslmode=require" in sanitized

    def test_handles_url_without_password(self) -> None:
        raw = "postgresql://postgres@localhost:5432/mydb"
        sanitized = sanitize_database_url(raw)
        assert sanitized == raw

    def test_handles_empty_or_none(self) -> None:
        assert sanitize_database_url(None) == "<empty>"
        assert sanitize_database_url("") == "<empty>"

    def test_masks_ipv6_url_preserving_brackets(self) -> None:
        raw = "postgresql://myuser:secretpassword@[::1]:5432/plataforma"
        sanitized = sanitize_database_url(raw)
        assert "secretpassword" not in sanitized
        assert "myuser:***@[::1]:5432" in sanitized

    def test_masks_sensitive_query_parameters(self) -> None:
        raw = "postgresql://myuser:pass@localhost:5432/db?token=supersecrettoken&other=val"
        sanitized = sanitize_database_url(raw)
        assert "supersecrettoken" not in sanitized
        assert "token=***" in sanitized
        assert "other=val" in sanitized


class TestPoolConfigurationResolution:
    """Verifies automatic detection of Session vs Transaction modes and parameter resolution."""

    def test_local_postgres_session_mode(self) -> None:
        _clean_dsn, kwargs, mode = resolve_pool_configuration(
            dsn="postgresql://postgres:pass@127.0.0.1:5432/test"
        )
        assert mode == "session"
        assert kwargs["statement_cache_size"] == 100
        assert "ssl" not in kwargs
        assert kwargs["min_size"] == settings.DB_POOL_MIN_SIZE
        assert kwargs["max_size"] == settings.DB_POOL_MAX_SIZE

    def test_supabase_transaction_mode_port_6543(self) -> None:
        _clean_dsn, kwargs, mode = resolve_pool_configuration(
            dsn="postgresql://postgres:pass@aws-0-us-east-1.pooler.supabase.com:6543/postgres"
        )
        assert mode == "transaction"
        # statement_cache_size MUST be 0 in transaction mode to prevent DuplicatePreparedStatementError
        assert kwargs["statement_cache_size"] == 0
        assert kwargs["ssl"] == "require"

    def test_supabase_session_mode_port_5432(self) -> None:
        _clean_dsn, kwargs, mode = resolve_pool_configuration(
            dsn="postgresql://postgres:pass@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
        )
        assert mode == "session"
        assert kwargs["statement_cache_size"] == 100
        assert kwargs["ssl"] == "require"

    def test_pooler_url_without_port_defaults_to_session_mode(self) -> None:
        """When port is omitted, PostgreSQL standard port 5432 (Session Mode) must be evaluated first."""
        _clean_dsn, kwargs, mode = resolve_pool_configuration(
            dsn="postgresql://postgres:pass@aws-0-us-east-1.pooler.supabase.com/postgres"
        )
        assert mode == "session"
        assert kwargs["statement_cache_size"] == 100
        assert kwargs["ssl"] == "require"

    def test_sslmode_query_param_stripped_and_applied(self) -> None:
        url_with_query = "postgresql://postgres:pass@localhost:5432/test?sslmode=require"
        clean_dsn, kwargs, _mode = resolve_pool_configuration(dsn=url_with_query)
        assert "?" not in clean_dsn
        assert kwargs["ssl"] == "require"

    def test_sslmode_disable_on_remote_host_is_honored(self) -> None:
        url_with_query = "postgresql://postgres:pass@remote.db.com:5432/test?sslmode=disable"
        _clean_dsn, kwargs, _mode = resolve_pool_configuration(dsn=url_with_query)
        assert "ssl" not in kwargs

    def test_explicit_mode_and_cache_overrides(self) -> None:
        with patch.object(settings, "DB_POOL_MODE", "transaction"):
            _clean_dsn, kwargs, mode = resolve_pool_configuration(
                dsn="postgresql://postgres:pass@127.0.0.1:5432/test",
                statement_cache_size=42,
            )
            assert mode == "transaction"
            assert kwargs["statement_cache_size"] == 42


class TestDatabasePoolLifecycle:
    """Live database tests against PostgreSQL verifying pool creation, statements, and teardown."""

    @pytest.mark.asyncio
    async def test_pool_lifecycle_and_session_mode(self) -> None:
        await close_db_pool()
        pool = await get_db_pool(
            dsn=TEST_DB_URL,
            min_size=1,
            max_size=3,
            statement_cache_size=100,
        )
        try:
            assert pool is not None
            async with pool.acquire() as conn:
                val = await conn.fetchval("SELECT 100 + 42")
                assert val == 142
                # Verify prepared statement works multiple times
                val2 = await conn.fetchval("SELECT 100 + 42")
                assert val2 == 142
        finally:
            await close_db_pool()

    @pytest.mark.asyncio
    async def test_pool_transaction_mode_statement_cache_zero(self) -> None:
        """Verifies statement_cache_size=0 operates cleanly with asyncpg."""
        await close_db_pool()
        pool = await get_db_pool(
            dsn=TEST_DB_URL,
            min_size=1,
            max_size=3,
            statement_cache_size=0,
        )
        try:
            assert pool is not None
            async with pool.acquire() as conn:
                # In statement_cache_size=0, queries are executed without named prepared statements
                val = await conn.fetchval("SELECT 7 * 6")
                assert val == 42
                val2 = await conn.fetchval("SELECT 7 * 6")
                assert val2 == 42
        finally:
            await close_db_pool()

    @pytest.mark.asyncio
    async def test_connection_error_handling_and_no_secret_in_logs(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        await close_db_pool()
        secret_pass = "SuperSecretDbPasswordNeverLeak"
        bad_dsn = f"postgresql://appuser:{secret_pass}@127.0.0.1:59999/nonexistent"

        with caplog.at_level(logging.INFO), pytest.raises(
            (OSError, asyncpg.PostgresError, asyncpg.CannotConnectNowError)
        ):
            await get_db_pool(dsn=bad_dsn, command_timeout=1.0)

        # Check logs: the secret password MUST NEVER appear in any log record
        for record in caplog.records:
            assert secret_pass not in record.message
            assert secret_pass not in str(record.args)
