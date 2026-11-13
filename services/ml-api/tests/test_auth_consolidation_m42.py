"""Integration and Security Tests for Milestone M4.2:
Authentication Consolidation, Cryptographic JWT Verification, and Environment Isolation.

Tests:
1. Valid Supabase JWT allows access matching user permissions.
2. Expired JWT produces 401 with code TOKEN_EXPIRED.
3. Invalid JWT signature produces 401 with code INVALID_CREDENTIALS.
4. Missing authentication produces 401 with code MISSING_CREDENTIALS.
5. Role enforcement: Student role attempting teacher endpoints produces 403 INSUFFICIENT_PERMISSIONS.
6. Spoofing prevention: Proxy headers cannot override an authentic JWT session.
7. Proxy headers work in development and test environments.
8. Proxy headers are strictly forbidden in production (settings.ENVIRONMENT = 'production').
9. Authoritative backend resolution: Profile in database overrides/supplements JWT claims.
"""

from datetime import UTC, datetime, timedelta
from uuid import UUID

import asyncpg
import httpx
import jwt
import pytest

from app.core.config import settings
from app.main import app

TEST_DB_URL = "postgresql://postgres:postgres@127.0.0.1:5432/plataformamicro_test"
TEST_JWT_SECRET = "super-secret-jwt-token-with-at-least-32-characters-long"

TENANT_A = "11111111-1111-1111-1111-111111111111"
TENANT_B = "22222222-2222-2222-2222-222222222222"

TEACHER_A = "11111111-1111-1111-1111-aaaaaaaaaaaa"
STUDENT_A1 = "11111111-1111-1111-1111-bbbbbbbbbbbb"
STUDENT_B1 = "22222222-2222-2222-2222-bbbbbbbbbbbb"

COURSE_A1 = "11111111-1111-1111-1111-cccccccccccc"
SECTION_A1 = "11111111-1111-1111-1111-dddddddddddd"


def create_test_jwt(
    user_id: str,
    email: str = "test@nexo.edu.pe",
    role: str = "student",
    tenant_id: str | None = None,
    secret: str = TEST_JWT_SECRET,
    expires_in_seconds: int = 3600,
) -> str:
    """Helper generating standard Supabase HS256 JWT tokens for testing."""
    now = datetime.now(UTC)
    payload = {
        "iss": "http://127.0.0.1:54321/auth/v1",
        "sub": user_id,
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
        "email": email,
        "role": "authenticated",
        "app_metadata": {
            "provider": "email",
            "role": role,
            **({"tenant_id": tenant_id} if tenant_id else {}),
        },
        "user_metadata": {
            "role": role,
            **({"tenant_id": tenant_id} if tenant_id else {}),
        },
    }
    return jwt.encode(payload, secret, algorithm="HS256")


@pytest.fixture(autouse=True)
async def setup_auth_database():
    """Ensure database connection pool and test seed are available."""
    import app.content_generation.infrastructure.database as db_mod

    pool = await asyncpg.create_pool(dsn=TEST_DB_URL, min_size=1, max_size=5)
    db_mod._POOL = pool

    async with pool.acquire() as conn:
        # Base Tenants
        await conn.execute(
            """
            INSERT INTO tenants (id, name, slug) VALUES 
                ($1, 'Colegio Piloto A', 'colegio-a-auth'),
                ($2, 'Colegio Piloto B', 'colegio-b-auth')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TENANT_A),
            UUID(TENANT_B),
        )
        # Auth Users
        await conn.execute(
            """
            INSERT INTO auth.users (id, email) VALUES
                ($1, 'teacher_a@nexo.edu.pe'),
                ($2, 'student_a1@nexo.edu.pe'),
                ($3, 'student_b1@nexo.edu.pe')
            ON CONFLICT (id) DO NOTHING;
            """,
            UUID(TEACHER_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_B1),
        )
        # Profiles
        await conn.execute(
            """
            INSERT INTO profiles (id, tenant_id, full_name, role) VALUES
                ($1, $2, 'Docente A', 'teacher'),
                ($3, $2, 'Estudiante A1', 'student'),
                ($4, $5, 'Estudiante B1', 'student')
            ON CONFLICT (id) DO UPDATE SET role = EXCLUDED.role, tenant_id = EXCLUDED.tenant_id;
            """,
            UUID(TEACHER_A),
            UUID(TENANT_A),
            UUID(STUDENT_A1),
            UUID(STUDENT_B1),
            UUID(TENANT_B),
        )

    yield pool
    await pool.close()


# ==============================================================================
# TESTS
# ==============================================================================


@pytest.mark.asyncio
async def test_01_valid_jwt_authenticates_student():
    """Valid student JWT allows accessing student courses and resolves tenant from DB."""
    student_jwt = create_test_jwt(user_id=STUDENT_A1, email="student_a1@nexo.edu.pe", role="student")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {student_jwt}"},
        )
        assert res.status_code == 200
        courses = res.json()
        assert isinstance(courses, list)


@pytest.mark.asyncio
async def test_02_valid_jwt_authenticates_teacher():
    """Valid teacher JWT allows listing teacher activities."""
    teacher_jwt = create_test_jwt(user_id=TEACHER_A, email="teacher_a@nexo.edu.pe", role="teacher")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {teacher_jwt}"},
        )
        assert res.status_code == 200
        activities = res.json()
        assert isinstance(activities, list)


@pytest.mark.asyncio
async def test_03_expired_jwt_rejected():
    """Expired JWT returns HTTP 401 with TOKEN_EXPIRED error code."""
    expired_jwt = create_test_jwt(user_id=STUDENT_A1, expires_in_seconds=-60)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {expired_jwt}"},
        )
        assert res.status_code == 401
        body = res.json()
        assert body["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_04_invalid_signature_jwt_rejected():
    """JWT signed with an unknown or incorrect secret produces HTTP 401 INVALID_CREDENTIALS."""
    forged_jwt = create_test_jwt(user_id=STUDENT_A1, secret="attacker-fake-secret-key-that-does-not-match")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {forged_jwt}"},
        )
        assert res.status_code == 401
        body = res.json()
        assert body["code"] == "INVALID_CREDENTIALS"


@pytest.mark.asyncio
async def test_05_missing_credentials_rejected():
    """Request with neither Bearer token nor proxy headers produces HTTP 401 MISSING_CREDENTIALS."""
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/students/me/courses")
        assert res.status_code == 401
        body = res.json()
        assert body["code"] == "MISSING_CREDENTIALS"


@pytest.mark.asyncio
async def test_06_student_role_forbidden_on_teacher_endpoint():
    """Student trying to access teacher-only endpoint produces HTTP 403 INSUFFICIENT_PERMISSIONS."""
    student_jwt = create_test_jwt(user_id=STUDENT_A1, role="student")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {student_jwt}"},
        )
        assert res.status_code == 403
        body = res.json()
        assert body["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_07_proxy_headers_cannot_override_jwt():
    """Attacker sending student JWT along with X-User-Role: teacher is still treated strictly as student."""
    student_jwt = create_test_jwt(user_id=STUDENT_A1, role="student")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Attempt to spoof teacher role via proxy headers
        res = await client.get(
            "/api/v1/activities",
            headers={
                "Authorization": f"Bearer {student_jwt}",
                "X-User-Id": TEACHER_A,
                "X-Tenant-Id": TENANT_A,
                "X-User-Role": "teacher",
            },
        )
        # Must still be rejected with 403 because JWT identifies user as student
        assert res.status_code == 403
        body = res.json()
        assert body["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_08_proxy_headers_allowed_in_development_and_test():
    """In development/test environment, proxy headers without JWT are accepted for compatibility."""
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "test"
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(
                "/api/v1/activities",
                headers={
                    "X-User-Id": TEACHER_A,
                    "X-Tenant-Id": TENANT_A,
                    "X-User-Role": "teacher",
                },
            )
            assert res.status_code == 200
    finally:
        settings.ENVIRONMENT = orig_env


@pytest.mark.asyncio
async def test_09_proxy_headers_strictly_rejected_in_production():
    """In production environment, proxy headers are rejected with 401 PROXY_HEADERS_FORBIDDEN."""
    orig_env = settings.ENVIRONMENT
    try:
        settings.ENVIRONMENT = "production"
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            res = await client.get(
                "/api/v1/activities",
                headers={
                    "X-User-Id": TEACHER_A,
                    "X-Tenant-Id": TENANT_A,
                    "X-User-Role": "teacher",
                },
            )
            assert res.status_code == 401
            body = res.json()
            assert body["code"] == "PROXY_HEADERS_FORBIDDEN"
    finally:
        settings.ENVIRONMENT = orig_env


# ==============================================================================
# M4.2 HARDENING — ASYMMETRIC SUPABASE TOKENS (ES256 / JWKS)
# ==============================================================================


def create_ec_jwt(
    user_id: str,
    private_key,
    *,
    email: str = "student_a1@nexo.edu.pe",
    role: str = "student",
    expires_in_seconds: int = 3600,
) -> str:
    """Generate an ES256 token matching the payload shape issued by Supabase."""
    now = datetime.now(UTC)
    payload = {
        "iss": "https://example.supabase.co/auth/v1",
        "sub": user_id,
        "aud": "authenticated",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=expires_in_seconds)).timestamp()),
        "email": email,
        "role": "authenticated",
        "app_metadata": {"provider": "email", "role": role},
        "user_metadata": {"role": role},
    }
    return jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "test-key"})


@pytest.mark.asyncio
async def test_10_es256_jwt_verified_via_jwks(monkeypatch):
    """A Supabase-style ES256 token is accepted when its key resolves through JWKS."""
    from types import SimpleNamespace

    from cryptography.hazmat.primitives.asymmetric import ec

    import app.core.auth as auth_mod

    private_key = ec.generate_private_key(ec.SECP256R1())
    token = create_ec_jwt(STUDENT_A1, private_key)
    monkeypatch.setattr(
        auth_mod,
        "_get_jwks_signing_key",
        lambda _token: SimpleNamespace(key=private_key.public_key()),
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 200


@pytest.mark.asyncio
async def test_11_expired_es256_jwt_rejected(monkeypatch):
    """Expired ES256 tokens are rejected with TOKEN_EXPIRED after key resolution."""
    from types import SimpleNamespace

    from cryptography.hazmat.primitives.asymmetric import ec

    import app.core.auth as auth_mod

    private_key = ec.generate_private_key(ec.SECP256R1())
    token = create_ec_jwt(STUDENT_A1, private_key, expires_in_seconds=-60)
    monkeypatch.setattr(
        auth_mod,
        "_get_jwks_signing_key",
        lambda _token: SimpleNamespace(key=private_key.public_key()),
    )

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 401
        assert res.json()["code"] == "TOKEN_EXPIRED"


@pytest.mark.asyncio
async def test_12_unsupported_jwt_algorithm_rejected():
    """Algorithms outside the Supabase contract are rejected with INVALID_CREDENTIALS."""
    token = create_test_jwt(STUDENT_A1)
    # Re-sign with an algorithm the backend does not accept.
    import jwt as pyjwt

    payload = pyjwt.decode(token, TEST_JWT_SECRET, algorithms=["HS256"], options={"verify_aud": False})
    unsupported = pyjwt.encode(payload, "another-secret-long-enough-for-hs512", algorithm="HS512")

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {unsupported}"},
        )
        assert res.status_code == 401
        assert res.json()["code"] == "INVALID_CREDENTIALS"


# ==============================================================================
# F-02 — DATABASE-ONLY IDENTITY (NO CLAIM FALLBACK)
# ==============================================================================


@pytest.mark.asyncio
async def test_13_user_metadata_role_cannot_escalate_privileges():
    """A student cannot become a teacher by editing user_metadata/app_metadata."""
    forged_context_jwt = create_test_jwt(
        user_id=STUDENT_A1,
        role="teacher",
        tenant_id=TENANT_B,
    )
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {forged_context_jwt}"},
        )
        assert res.status_code == 403
        assert res.json()["code"] == "INSUFFICIENT_PERMISSIONS"


@pytest.mark.asyncio
async def test_14_database_unavailable_fails_closed_with_503(monkeypatch):
    """When PostgreSQL cannot verify identity, protected endpoints return 503 (not 403/claims)."""
    import app.core.auth as auth_mod

    async def unavailable(_user_uuid):
        raise OSError("database temporarily unavailable")

    monkeypatch.setattr(auth_mod, "_fetch_identity_once", unavailable)
    monkeypatch.setattr(settings, "DB_STALE_RETRY_ATTEMPTS", 1)

    teacher_claim_jwt = create_test_jwt(user_id=TEACHER_A, role="teacher")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/activities",
            headers={"Authorization": f"Bearer {teacher_claim_jwt}"},
        )
        assert res.status_code == 503
        assert res.json()["code"] == "AUTH_BACKEND_UNAVAILABLE"
        assert res.headers.get("retry-after") == "5"


@pytest.mark.asyncio
async def test_15_unprovisioned_identity_is_forbidden():
    """A valid JWT without a profiles row is rejected with IDENTITY_NOT_PROVISIONED."""
    unprovisioned = "99999999-9999-9999-9999-999999999999"
    token = create_test_jwt(user_id=unprovisioned, role="teacher", tenant_id=TENANT_A)
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert res.status_code == 403
        assert res.json()["code"] == "IDENTITY_NOT_PROVISIONED"


@pytest.mark.asyncio
async def test_16_stale_connection_is_retried_once(monkeypatch):
    """A Lambda thaw may leave a stale pooled connection; one retry must recover it."""
    import app.core.auth as auth_mod

    calls = {"count": 0}

    async def flaky(user_uuid):
        calls["count"] += 1
        if calls["count"] == 1:
            raise OSError("server closed the connection unexpectedly")
        return TENANT_A, "student", set()

    monkeypatch.setattr(auth_mod, "_fetch_identity_once", flaky)
    monkeypatch.setattr(settings, "DB_STALE_RETRY_ATTEMPTS", 1)

    student_jwt = create_test_jwt(user_id=STUDENT_A1, role="student")
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get(
            "/api/v1/students/me/courses",
            headers={"Authorization": f"Bearer {student_jwt}"},
        )
        assert res.status_code == 200
        assert calls["count"] == 2
