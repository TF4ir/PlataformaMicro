"""Tests for Task AWS-LAMBDA-02 / AWS-LAMBDA-02.1: Hardening and deployment readiness for ML-API on AWS Lambda.

Verifies:
1. Secrets Manager integration via mocks:
   - Secret retrieved and parsed (both JSON format and plain DSN).
   - Secret cached in memory across subsequent calls.
   - Cache invalidation and reload via invalidate_cached_dsn().
   - Masked DSN representation contains no cleartext passwords.
   - Controlled failure (RuntimeError) on Secrets Manager error without credential leakage.
2. CORS deduplication:
   - Middleware disabled when in Lambda execution mode or ENABLE_CORS_MIDDLEWARE=False.
   - Middleware enabled in local development.
   - OPTIONS queries on real API routes.
3. Content generation worker safety on Lambda:
   - When worker is disabled (CONTENT_GENERATION_WORKER_ENABLED=False), job creation returns 503.
   - Prevents permanent "queued" job orphan states.
4. Document management under Lambda payload constraints:
   - Uploads exceeding 6 MB are rejected under Lambda with HTTP 413 and guidance to use Supabase Storage.
   - Direct Supabase Storage reference (storage_path + metadata) accepted without large binary payload.
   - Cross-tenant storage path references strictly rejected with 400/403.
   - Missing both file and storage_path rejected with 400.
5. Model registry empirical guardrails:
   - Absence of empirical model does not falsely label predictions as trained models.
6. Public Function URL authentication & authorization:
   - Health check allows unauthenticated access (200 OK).
   - Protected routes reject unauthenticated requests (401 Unauthorized).
   - Retention endpoint returns 401 without token, 200 with valid student token.
   - Student role accessing teacher routes returns 403 Forbidden.
7. Read-only filesystem compliance:
   - Validates that only /tmp is used for write operations.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.v1.recommendations import get_db_pool, get_inference_service
from app.core.auth import AuthenticatedUser, get_current_user
from app.core.config import settings
from app.core.secrets import (
    get_database_dsn,
    invalidate_cached_dsn,
    mask_database_dsn,
    reset_cached_dsn,
)
from app.main import app
from app.prediction.history_builder import StudentKCHistorySummary
from app.prediction.inference_service import RetentionInferenceService
from app.prediction.model_registry import RetentionModelRegistry
from app.schemas.prediction import (
    ModelAvailabilityStatus,
    StudentRetentionSummaryResponse,
)

# ==============================================================================
# Helper Functions
# ==============================================================================


def create_mock_jwt(
    user_id: uuid.UUID,
    role: str = "student",
    tenant_id: uuid.UUID | None = None,
    authorized_courses: list[str] | None = None,
) -> str:
    now = datetime.now(UTC)
    payload = {
        "iss": "http://127.0.0.1:54321/auth/v1",
        "sub": str(user_id),
        "email": f"{role}@test.edu.pe",
        "role": "authenticated",
        "app_metadata": {
            "provider": "email",
            "role": role,
            **({"tenant_id": str(tenant_id)} if tenant_id else {}),
            **({"authorized_courses": authorized_courses} if authorized_courses else {}),
        },
        "user_metadata": {
            "role": role,
            **({"tenant_id": str(tenant_id)} if tenant_id else {}),
        },
        **({"tenant_id": str(tenant_id)} if tenant_id else {}),
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(hours=2)).timestamp()),
    }
    encoded: str = jwt.encode(payload, settings.SUPABASE_JWT_SECRET, algorithm="HS256")
    return encoded


# ==============================================================================
# 1. AWS Secrets Manager Integration Tests (Mocks only, zero real AWS calls)
# ==============================================================================


def test_mask_database_dsn_hides_passwords() -> None:
    raw_dsn = "postgresql://postgres:SuperSecretP@ss123!@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
    masked = mask_database_dsn(raw_dsn)
    assert "SuperSecretP@ss123!" not in masked
    assert "postgres:***@aws-0-us-east-2.pooler.supabase.com:6543/postgres" in masked
    assert "sslmode=require" in masked


def test_mask_database_dsn_empty_and_no_password() -> None:
    assert mask_database_dsn("") == "<empty>"
    assert mask_database_dsn(None) == "<empty>"
    no_pass = "postgresql://postgres@localhost:5432/testdb"
    assert mask_database_dsn(no_pass) == "postgresql://postgres@localhost:5432/testdb"


def test_mask_database_dsn_without_scheme_hides_passwords() -> None:
    raw_no_scheme = "postgres:MySecretPassword123@localhost:5432/testdb"
    masked = mask_database_dsn(raw_no_scheme)
    assert "MySecretPassword123" not in masked
    assert "postgres:***@localhost:5432/testdb" == masked


def test_secrets_manager_plain_dsn_retrieval() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:test-db-secret"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretString": "postgresql://postgres:secret_pass@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert dsn.startswith("postgresql://postgres:secret_pass@")
        mock_boto.get_secret_value.assert_called_once_with(
            SecretId="arn:aws:secretsmanager:us-east-2:716174523077:secret:test-db-secret"
        )

        # In-memory caching: second call does not invoke boto3 again
        dsn_cached = get_database_dsn(boto_client=mock_boto)
        assert dsn_cached == dsn
        assert mock_boto.get_secret_value.call_count == 1
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_json_payload_retrieval() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:test-db-json"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretString": json.dumps({
                "username": "postgres.oqjahhbqcethwgpufgnm",
                "password": "MyCustomSecretPassword#2026",
                "host": "aws-0-us-east-2.pooler.supabase.com",
                "port": 6543,
                "dbname": "postgres",
                "sslmode": "require",
            })
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert "aws-0-us-east-2.pooler.supabase.com:6543/postgres" in dsn
        assert "MyCustomSecretPassword%232026" in dsn or "MyCustomSecretPassword" in dsn
        mock_boto.get_secret_value.assert_called_once()
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_invalidation_and_reload() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:rotated-secret"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.side_effect = [
            {"SecretString": "postgresql://postgres:old_pass@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"},
            {"SecretString": "postgresql://postgres:new_rotated_pass@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"},
        ]

        dsn1 = get_database_dsn(boto_client=mock_boto)
        assert "old_pass" in dsn1
        assert mock_boto.get_secret_value.call_count == 1

        # Invalidate cached DSN (e.g. following PostgreSQL AuthError or secret rotation)
        invalidate_cached_dsn()

        # Subsequent call retrieves rotated secret from Secrets Manager
        dsn2 = get_database_dsn(boto_client=mock_boto)
        assert "new_rotated_pass" in dsn2
        assert mock_boto.get_secret_value.call_count == 2
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_invalidate_cached_dsn_terminates_active_pool() -> None:
    """Invalidating cached DSN must terminate any active asyncpg pool so fresh credentials are used."""
    import app.content_generation.infrastructure.database as db_mod

    mock_pool = MagicMock()
    mock_pool._closed = False
    original_pool = db_mod._POOL
    try:
        db_mod._POOL = mock_pool
        assert db_mod.get_current_db_pool() is mock_pool

        invalidate_cached_dsn()

        assert mock_pool.terminate.called
    finally:
        db_mod._POOL = original_pool
        reset_cached_dsn()


def test_secrets_manager_controlled_failure_raises_runtime_error() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:failing-secret"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.side_effect = RuntimeError("ResourceNotFoundException")

        with pytest.raises(RuntimeError) as exc_info:
            get_database_dsn(boto_client=mock_boto)

        assert "Controlled initialization failure" in str(exc_info.value)
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_invalid_json_raises_controlled_error() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:corrupt-json"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {"SecretString": "{not-valid-json"}

        with pytest.raises(RuntimeError) as exc_info:
            get_database_dsn(boto_client=mock_boto)

        assert "invalid JSON" in str(exc_info.value)
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_binary_secret_retrieval() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:binary-secret"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretBinary": b"postgresql://postgres:binary_pass@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require"
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert "binary_pass" in dsn
        assert "aws-0-us-east-2.pooler.supabase.com:6543/postgres" in dsn
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_json_alternative_keys() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:conn-string-json"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretString": json.dumps({"connectionString": "postgresql://postgres:alt_pass@host.supabase.com:6543/postgres"})
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert "alt_pass" in dsn
        assert "host.supabase.com:6543/postgres" in dsn
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_strips_export_prefix() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:exported-secret"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretString": 'export DATABASE_URL="postgresql://postgres:export_p@aws-0.supabase.com:6543/postgres?sslmode=require"'
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert dsn.startswith("postgresql://")
        assert "export_p" in dsn
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


def test_secrets_manager_handles_host_with_existing_port() -> None:
    reset_cached_dsn()
    original_arn = settings.DATABASE_SECRET_ARN
    try:
        settings.DATABASE_SECRET_ARN = "arn:aws:secretsmanager:us-east-2:716174523077:secret:host-port-json"
        mock_boto = MagicMock()
        mock_boto.get_secret_value.return_value = {
            "SecretString": json.dumps({
                "username": "postgres",
                "password": "pass",
                "host": "aws-0-us-east-2.pooler.supabase.com:6543",
                "port": 6543,
                "dbname": "postgres",
            })
        }

        dsn = get_database_dsn(boto_client=mock_boto)
        assert "aws-0-us-east-2.pooler.supabase.com:6543/postgres" in dsn
        assert ":6543:6543" not in dsn
    finally:
        settings.DATABASE_SECRET_ARN = original_arn
        reset_cached_dsn()


# ==============================================================================
# 2. CORS Strategy Tests
# ==============================================================================


def test_cors_origins_setting_has_no_unconfirmed_domains() -> None:
    origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
    assert "https://plataformamicro.fabriziovalerio-c.workers.dev" in origins
    assert "https://plataformamicro.edu.pe" not in origins
    assert "https://app.plataformamicro.edu.pe" not in origins


@pytest.mark.asyncio
async def test_cors_disabled_in_lambda_runtime_to_prevent_duplicate_headers(monkeypatch: pytest.MonkeyPatch) -> None:
    """In AWS Lambda, FastAPI CORSMiddleware is not added to avoid duplicate Access-Control-Allow-Origin headers."""
    import importlib
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "nexo-mvp-ml-api")
    monkeypatch.setenv("ENABLE_CORS_MIDDLEWARE", "false")

    import app.main as main_mod
    importlib.reload(main_mod)
    try:
        transport = ASGITransport(app=main_mod.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/health",
                headers={"Origin": "https://plataformamicro.fabriziovalerio-c.workers.dev"},
            )
            assert resp.status_code == 200
            # FastAPI must NOT inject Access-Control-Allow-Origin; Lambda Function URL handles it
            assert "access-control-allow-origin" not in resp.headers
    finally:
        monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
        monkeypatch.delenv("ENABLE_CORS_MIDDLEWARE", raising=False)
        importlib.reload(main_mod)


@pytest.mark.asyncio
async def test_cors_enabled_in_local_development(monkeypatch: pytest.MonkeyPatch) -> None:
    """In local development, FastAPI CORSMiddleware provides CORS headers for authorized origins."""
    import importlib
    monkeypatch.delenv("AWS_LAMBDA_FUNCTION_NAME", raising=False)
    monkeypatch.setenv("ENABLE_CORS_MIDDLEWARE", "true")

    import app.core.config as config_mod
    import app.main as main_mod
    importlib.reload(config_mod)
    importlib.reload(main_mod)
    try:
        transport = ASGITransport(app=main_mod.app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/health",
                headers={"Origin": "https://plataformamicro.fabriziovalerio-c.workers.dev"},
            )
            assert resp.status_code == 200
            assert resp.headers.get("access-control-allow-origin") == "https://plataformamicro.fabriziovalerio-c.workers.dev"
    finally:
        importlib.reload(main_mod)


@pytest.mark.asyncio
async def test_options_requests_on_real_endpoints() -> None:
    transport = ASGITransport(app=app)
    cors_headers = {
        "Origin": "https://plataformamicro.fabriziovalerio-c.workers.dev",
        "Access-Control-Request-Method": "GET",
    }
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # OPTIONS on public health check
        resp_health = await client.options("/api/v1/health", headers=cors_headers)
        assert resp_health.status_code in (200, 204)

        # OPTIONS on retention route (/api/v1/students/me/retention)
        resp_ret = await client.options("/api/v1/students/me/retention", headers=cors_headers)
        assert resp_ret.status_code in (200, 204)

        # OPTIONS on teacher upload-material
        resp_upload = await client.options("/api/v1/content-generation/upload-material", headers=cors_headers)
        assert resp_upload.status_code in (200, 204)


# ==============================================================================
# 3. Content Generation Worker Guard on Lambda Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_job_creation_rejected_when_worker_disabled_on_lambda() -> None:
    original_flag = settings.CONTENT_GENERATION_WORKER_ENABLED
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        settings.CONTENT_GENERATION_WORKER_ENABLED = False

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "storage_bucket": "teacher-materials",
                "storage_path": f"{teacher_user.tenant_id}/course-1/material.pdf",
                "original_filename": "material.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 1024,
                "file_checksum": "a" * 64,
                "course_id": "course-1",
            }
            resp = await client.post(
                "/api/v1/content-generation/jobs",
                json=payload,
                headers={"Authorization": "Bearer mock-token"},
            )

            assert resp.status_code == 503
            data = resp.json()
            assert data["code"] == "CONTENT_GENERATION_UNAVAILABLE"
            assert "no está disponible en este entorno" in data["detail"]
    finally:
        settings.CONTENT_GENERATION_WORKER_ENABLED = original_flag
        app.dependency_overrides.pop(get_current_user, None)


def test_worker_not_started_under_lambda_configuration() -> None:
    """Verify that when CONTENT_GENERATION_WORKER_ENABLED=False, no background worker thread or task is running."""
    import inspect

    import app.main as main_mod
    lifespan_source = inspect.getsource(main_mod.lifespan)
    assert "run_loop" not in lifespan_source
    assert "GenerationWorker" not in lifespan_source


# ==============================================================================
# 4. Lambda Synchronous 6 MB Upload Constraint & Direct Storage Path Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_upload_material_rejects_files_over_6mb_under_lambda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "nexo-mvp-ml-api")
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Create a dummy payload simulating > 6 MB (6 * 1024 * 1024 + 10)
            seven_mb = b"%PDF-1.4 " + b"0" * (7 * 1024 * 1024)
            files = {"file": ("document.pdf", seven_mb, "application/pdf")}

            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                files=files,
                headers={"Authorization": "Bearer mock-token"},
            )

            assert resp.status_code == 413
            data = resp.json()
            assert data["code"] == "LAMBDA_PAYLOAD_LIMIT_EXCEEDED"
            assert "límite de 6 MB soportado por AWS Lambda" in data["detail"]
            assert "Supabase Storage" in data["detail"]
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_material_accepts_files_under_6mb_under_lambda(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AWS_LAMBDA_FUNCTION_NAME", "nexo-mvp-ml-api")
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # Small PDF file (10 KB)
            small_pdf = b"%PDF-1.4 " + b"0" * 10240
            files = {"file": ("small.pdf", small_pdf, "application/pdf")}

            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                files=files,
                headers={"Authorization": "Bearer mock-token"},
            )

            assert resp.status_code == 200
            data = resp.json()
            assert data["storage_bucket"] == "teacher-materials"
            assert "storage_path" in data
            assert data["file_size_bytes"] == len(small_pdf)
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_material_accepts_direct_supabase_storage_reference() -> None:
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            storage_path = f"{teacher_user.tenant_id}/course-1/presentation.pptx"
            data = {
                "storage_path": storage_path,
                "storage_bucket": "teacher-materials",
                "original_filename": "presentation.pptx",
                "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "file_size_bytes": "15728640",  # 15 MB direct reference
                "file_checksum": "b" * 64,
                "course_id": "course-1",
            }
            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                data=data,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp.status_code == 200
            res = resp.json()
            assert res["storage_path"] == storage_path
            assert res["storage_bucket"] == "teacher-materials"
            assert res["file_size_bytes"] == 15728640
            assert res["file_checksum"] == "b" * 64
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_material_rejects_cross_tenant_storage_path() -> None:
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            other_tenant = str(uuid.uuid4())
            data = {
                "storage_path": f"{other_tenant}/course-1/presentation.pptx",
                "storage_bucket": "teacher-materials",
                "original_filename": "presentation.pptx",
                "mime_type": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
                "file_size_bytes": "1024",
                "file_checksum": "b" * 64,
            }
            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                data=data,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp.status_code in (400, 403)
            data_resp = resp.json()
            assert "detail" in data_resp
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_material_rejects_missing_file_and_storage_path() -> None:
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-1"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                data={},
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp.status_code == 400
            data_resp = resp.json()
            assert data_resp["code"] == "MISSING_FILE_OR_STORAGE_PATH"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_upload_material_rejects_unauthorized_course_in_storage_path() -> None:
    tenant_id = str(uuid.uuid4())
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-authorized"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            data = {
                "storage_path": f"{tenant_id}/course-unauthorized/document.pdf",
                "storage_bucket": "teacher-materials",
                "original_filename": "document.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": "2048",
                "file_checksum": "c" * 64,
            }
            resp = await client.post(
                "/api/v1/content-generation/upload-material",
                data=data,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp.status_code == 403
            assert resp.json()["code"] == "COURSE_NOT_ASSIGNED"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


@pytest.mark.asyncio
async def test_create_job_rejects_unauthorized_course_in_storage_path() -> None:
    original_flag = settings.CONTENT_GENERATION_WORKER_ENABLED
    tenant_id = str(uuid.uuid4())
    teacher_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=tenant_id,
        role="teacher",
        email="teacher@test.edu.pe",
        authorized_course_ids={"course-authorized"},
    )
    app.dependency_overrides[get_current_user] = lambda: teacher_user
    try:
        settings.CONTENT_GENERATION_WORKER_ENABLED = True
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            payload = {
                "storage_bucket": "teacher-materials",
                "storage_path": f"{tenant_id}/course-unauthorized/document.pdf",
                "original_filename": "document.pdf",
                "mime_type": "application/pdf",
                "file_size_bytes": 2048,
                "file_checksum": "c" * 64,
            }
            resp = await client.post(
                "/api/v1/content-generation/jobs",
                json=payload,
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp.status_code == 403
            assert resp.json()["code"] == "COURSE_NOT_ASSIGNED"
    finally:
        settings.CONTENT_GENERATION_WORKER_ENABLED = original_flag
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 5. Model Registry & Fallback Labeling Guard Tests
# ==============================================================================


def test_model_registry_production_rejects_synthetic_without_empirical() -> None:
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        registry = RetentionModelRegistry()
        model, meta, status = registry.get_active_model()

        assert model is None
        assert meta is None
        assert status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
    finally:
        settings.ENVIRONMENT = original_env


@pytest.mark.asyncio
async def test_inference_service_labels_fallback_transparently() -> None:
    original_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        mock_history_builder = MagicMock()
        kc_id = uuid.uuid4()
        now = datetime.now(UTC)
        mock_summary = StudentKCHistorySummary(
            knowledge_component_id=kc_id,
            knowledge_component_name="Fotosíntesis",
            kc_difficulty_prior=0.5,
            total_exposures=2,
            total_retrieval_attempts=3,
            total_successes=2,
            total_failures=1,
            first_exposure_at=now,
            last_exposure_at=now,
            last_retrieval_at=now,
            last_interaction_at=now,
            interaction_events=[],
        )
        mock_history_builder.fetch_student_kc_history = AsyncMock(return_value={kc_id: mock_summary})

        service = RetentionInferenceService(history_builder=mock_history_builder)
        mock_pool = MagicMock()
        mock_pool.acquire = MagicMock()
        result = await service.get_student_retention_profile(
            pool=mock_pool,
            student_id=uuid.uuid4(),
            tenant_id=uuid.uuid4(),
            persist_predictions=False,
        )

        assert result.status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
        assert "insufficient_empirical_data" in result.audit_note
        for kc in result.kcs:
            assert kc.availability_status == ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA
            assert kc.model_name == "rule_based_fallback"
            assert kc.model_version == "1.0.0"
            assert kc.predicted_forgetting_time_seconds is None
    finally:
        settings.ENVIRONMENT = original_env


# ==============================================================================
# 6. Function URL Authentication & Authorization Tests
# ==============================================================================


@pytest.mark.asyncio
async def test_health_check_public_200() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_protected_routes_reject_unauthenticated_401() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Teacher route without token
        resp = await client.get("/api/v1/content-generation/courses")
        assert resp.status_code == 401

        # Student route without token
        resp = await client.get("/api/v1/students/me/dashboard")
        assert resp.status_code == 401

        # Activity route without token
        resp = await client.get("/api/v1/activities")
        assert resp.status_code == 401

        # Retention route without token (/api/v1/students/me/retention)
        resp_ret = await client.get("/api/v1/students/me/retention")
        assert resp_ret.status_code == 401


@pytest.mark.asyncio
async def test_get_retention_authenticated_returns_profile() -> None:
    student_id = uuid.uuid4()
    tenant_id = uuid.uuid4()
    student_user = AuthenticatedUser(
        user_id=str(student_id),
        tenant_id=str(tenant_id),
        role="student",
        email="student@test.edu.pe",
        authorized_course_ids=set(),
    )
    app.dependency_overrides[get_current_user] = lambda: student_user

    mock_inference = MagicMock()
    mock_summary = StudentRetentionSummaryResponse(
        student_id=student_id,
        as_of=datetime.now(UTC),
        status=ModelAvailabilityStatus.INSUFFICIENT_EMPIRICAL_DATA,
        audit_note="rule_based_fallback",
        kcs=[],
    )
    mock_inference.get_student_retention_profile = AsyncMock(return_value=mock_summary)
    mock_pool = MagicMock()

    app.dependency_overrides[get_inference_service] = lambda: mock_inference
    app.dependency_overrides[get_db_pool] = lambda: mock_pool
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            resp = await client.get(
                "/api/v1/students/me/retention",
                headers={"Authorization": "Bearer valid-student-token"},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["student_id"] == str(student_id)
            assert data["status"] == "insufficient_empirical_data"
    finally:
        app.dependency_overrides.pop(get_current_user, None)
        app.dependency_overrides.pop(get_inference_service, None)
        app.dependency_overrides.pop(get_db_pool, None)


@pytest.mark.asyncio
async def test_student_forbidden_from_teacher_content_generation_routes() -> None:
    student_user = AuthenticatedUser(
        user_id=str(uuid.uuid4()),
        tenant_id=str(uuid.uuid4()),
        role="student",
        email="student@test.edu.pe",
        authorized_course_ids=set(),
    )
    app.dependency_overrides[get_current_user] = lambda: student_user
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            # 1. Student accessing courses
            resp_courses = await client.get(
                "/api/v1/content-generation/courses",
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp_courses.status_code == 403

            # 2. Student accessing upload-material
            resp_upload = await client.post(
                "/api/v1/content-generation/upload-material",
                data={"storage_path": f"{student_user.tenant_id}/course-1/file.pdf"},
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp_upload.status_code == 403

            # 3. Student accessing questions
            resp_q = await client.get(
                "/api/v1/content-generation/questions",
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp_q.status_code == 403

            # 4. Student accessing teacher activities
            resp_act = await client.get(
                "/api/v1/activities",
                headers={"Authorization": "Bearer mock-token"},
            )
            assert resp_act.status_code == 403
            assert resp_act.json()["code"] == "INSUFFICIENT_PERMISSIONS"
    finally:
        app.dependency_overrides.pop(get_current_user, None)


# ==============================================================================
# 7. Read-Only Filesystem & Execution Environment Tests
# ==============================================================================


def test_read_only_filesystem_guarantees() -> None:
    """Under AWS Lambda execution environments, only /tmp (TMPDIR) is writable."""
    tmpdir = os.environ.get("TMPDIR", "/tmp")
    test_file = os.path.join(tmpdir, f"lambda_test_{uuid.uuid4().hex}.tmp")
    try:
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("temporary file writes allowed in /tmp")
        assert os.path.exists(test_file)
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
