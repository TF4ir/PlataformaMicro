"""Authentication and authorization dependencies for FastAPI endpoints.

Implements Milestone M4.2 + MVP hardening:
- Cryptographic verification of Supabase JWTs using JWKS (ES256/RS256) and
  HS256 legacy secrets. Supabase projects created after October 2025 sign
  access tokens with asymmetric ES256 keys and publish them via JWKS.
- Authoritative resolution of tenant, roles, and course permissions from PostgreSQL.
- Strict rejection of proxy identity headers in production/demo environments (fail-closed).
- Retention of proxy headers strictly for development and test execution.
- Prevention of identity spoofing or header overriding over verified JWTs.
"""

import asyncio
import logging
import uuid
from collections.abc import Callable
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Annotated, Any

import asyncpg
import jwt
from fastapi import Depends, Header, HTTPException, status
from jwt import PyJWKClient

from app.content_generation.infrastructure.database import get_db_pool
from app.core.config import settings

logger = logging.getLogger(__name__)

# Algorithms accepted from Supabase-issued access tokens.
_ASYMMETRIC_ALGORITHMS = frozenset({"ES256", "RS256"})


def _jwks_url() -> str:
    """Resolve the Supabase JWKS endpoint for the configured project."""
    if settings.SUPABASE_JWKS_URL:
        return settings.SUPABASE_JWKS_URL
    return f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"


@lru_cache(maxsize=8)
def _get_jwks_client(jwks_url: str) -> PyJWKClient:
    """Cache one JWKS client per URL (PyJWT caches the fetched keys internally)."""
    return PyJWKClient(jwks_url)


def _get_jwks_signing_key(token: str) -> Any:
    """Resolve the signing key for an asymmetric Supabase token via JWKS."""
    return _get_jwks_client(_jwks_url()).get_signing_key_from_jwt(token)


def decode_supabase_jwt(token: str) -> dict[str, Any]:
    """Verify and decode a Supabase access token.

    Supports the two signing schemes used by Supabase:
    - ES256/RS256 (new projects): public key resolved from the project JWKS.
    - HS256 (legacy projects): shared JWT secret.

    Raises ``jwt.PyJWTError`` for invalid tokens so the caller can map them to
    RFC 7807 responses. Expired tokens raise ``jwt.ExpiredSignatureError``.
    """
    is_prod = settings.ENVIRONMENT.lower() == "production"

    header = jwt.get_unverified_header(token)
    algorithm = str(header.get("alg", ""))

    if algorithm == "HS256":
        if settings.SUPABASE_JWT_SECRET:
            return jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False, "verify_exp": True},
            )
        if is_prod:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/server-misconfigured",
                    "title": "Error de Configuración",
                    "status": 500,
                    "detail": "El secreto de verificación JWT no está configurado en el servidor.",
                    "code": "JWT_SECRET_MISSING",
                },
            )
        # Development/testing without configured secret: inspect claims only.
        return jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": True},
        )

    if algorithm in _ASYMMETRIC_ALGORITHMS:
        signing_key = _get_jwks_signing_key(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=[algorithm],
            options={"verify_aud": False, "verify_exp": True},
        )

    raise jwt.InvalidAlgorithmError(
        f"Unsupported JWT signing algorithm: {algorithm or 'missing'}"
    )


@dataclass
class AuthenticatedUser:
    """Identity context extracted from verified JWT or trusted proxy headers."""

    user_id: str
    tenant_id: str
    role: str
    email: str | None = None
    authorized_course_ids: set[str] = field(default_factory=set)


def _auth_http_error(
    status_code: int,
    *,
    title: str,
    detail: str,
    code: str,
    retry_after: int | None = None,
) -> HTTPException:
    """Build an RFC 7807 style authentication/authorization error."""
    headers = {"Retry-After": str(retry_after)} if retry_after is not None else None
    return HTTPException(
        status_code=status_code,
        detail={
            "type": f"https://api.plataformamicro.edu.pe/errors/{code.lower().replace('_', '-')}",
            "title": title,
            "status": status_code,
            "detail": detail,
            "code": code,
        },
        headers=headers,
    )


async def _fetch_identity_once(
    user_uuid: uuid.UUID,
) -> tuple[str, str, set[str]] | None:
    """Read role, tenant and course scope from `public.profiles` exactly once.

    Returns ``None`` when the authenticated subject has no provisioned profile.
    Any database/network exception is propagated so the caller can retry or
    fail closed with 503.
    """
    pool = await get_db_pool()
    async with pool.acquire() as conn:
        profile_row = await conn.fetchrow(
            "SELECT tenant_id, role FROM public.profiles WHERE id = $1",
            user_uuid,
        )
        if profile_row is None:
            return None

        tenant_id = str(profile_row["tenant_id"])
        role = str(profile_row["role"])
        authorized_course_ids: set[str] = set()

        if role == "teacher":
            section_rows = await conn.fetch(
                "SELECT DISTINCT course_id::text FROM public.sections WHERE teacher_id = $1",
                user_uuid,
            )
            authorized_course_ids = {row[0] for row in section_rows}
        elif role == "student":
            enrollment_rows = await conn.fetch(
                """
                SELECT DISTINCT s.course_id::text
                FROM public.enrollments e
                JOIN public.sections s ON s.id = e.section_id
                WHERE e.student_id = $1
                """,
                user_uuid,
            )
            authorized_course_ids = {row[0] for row in enrollment_rows}

        return tenant_id, role, authorized_course_ids


async def _resolve_identity_from_db(user_id: str) -> tuple[str, str, set[str]]:
    """Resolve the authoritative authorization context from PostgreSQL.

    Security contract:
    - `public.profiles` is the sole source of `role` and `tenant_id`.
    - JWT claims are never consulted as a fallback.
    - A transient/stale connection (common when Lambda thaws a frozen
      execution environment) is retried once. If the database still cannot be
      verified, the request fails with 503 and is never authorized.
    """
    try:
        user_uuid = uuid.UUID(user_id)
    except (TypeError, ValueError) as exc:
        raise _auth_http_error(
            status.HTTP_401_UNAUTHORIZED,
            title="Token Inválido",
            detail="El token no contiene un identificador de usuario válido (sub).",
            code="INVALID_TOKEN_SUBJECT",
        ) from exc

    attempts = max(1, settings.DB_STALE_RETRY_ATTEMPTS + 1)
    last_error: Exception | None = None

    for attempt in range(attempts):
        try:
            identity = await _fetch_identity_once(user_uuid)
        except (TimeoutError, asyncpg.PostgresError, OSError, RuntimeError) as exc:
            last_error = exc
            logger.warning(
                "Authoritative identity lookup failed (attempt %d/%d): %s",
                attempt + 1,
                attempts,
                type(exc).__name__,
            )
            if attempt + 1 < attempts:
                # Yield to the event loop; asyncpg discards broken connections
                # from the pool so the next acquire gets a fresh one.
                await asyncio.sleep(0)
                continue
        else:
            if identity is None:
                raise _auth_http_error(
                    status.HTTP_403_FORBIDDEN,
                    title="Identidad No Habilitada",
                    detail="El usuario autenticado no tiene un perfil institucional habilitado.",
                    code="IDENTITY_NOT_PROVISIONED",
                )

            tenant_id, role, authorized_course_ids = identity
            if not tenant_id or not role:
                raise _auth_http_error(
                    status.HTTP_503_SERVICE_UNAVAILABLE,
                    title="Identidad No Verificable",
                    detail="No se pudo verificar la institución o el rol del usuario en la base de datos.",
                    code="AUTH_BACKEND_UNAVAILABLE",
                    retry_after=5,
                )
            return tenant_id, role, authorized_course_ids

    logger.error(
        "Authoritative identity lookup unavailable after %d attempt(s): %s",
        attempts,
        type(last_error).__name__ if last_error else "unknown",
    )
    raise _auth_http_error(
        status.HTTP_503_SERVICE_UNAVAILABLE,
        title="Servicio de Identidad No Disponible",
        detail="No se pudo verificar la identidad del usuario. Intenta nuevamente en unos segundos.",
        code="AUTH_BACKEND_UNAVAILABLE",
        retry_after=5,
    ) from last_error


async def get_current_user(
    authorization: str | None = Header(None, alias="Authorization"),
    x_user_id: str | None = Header(None, alias="X-User-Id"),
    x_tenant_id: str | None = Header(None, alias="X-Tenant-Id"),
    x_user_role: str | None = Header(None, alias="X-User-Role"),
    x_course_ids: str | None = Header(None, alias="X-Course-Ids"),
) -> AuthenticatedUser:
    """Extract authenticated user and institutional tenant context.

    Precedence and security rules:
    1. If `Authorization: Bearer <jwt>` is provided, verify JWT cryptographically.
       Any proxy headers present in the request are strictly ignored and cannot override JWT claims.
    2. If no `Authorization` header is provided:
       - In 'production': Reject immediately (401). Proxy headers are strictly forbidden.
       - In 'development' or 'test': Allow proxy headers for testing and automated suites.
    3. If neither valid JWT nor allowed proxy headers exist, raise 401 Unauthorized.
    """
    # --------------------------------------------------------------------------
    # 1. Bearer JWT Token Verification (Primary & Authoritative)
    # --------------------------------------------------------------------------
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()

        try:
            payload = decode_supabase_jwt(token)
        except jwt.ExpiredSignatureError as e:
            logger.warning("Supabase JWT expired: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "Token Expirado",
                    "status": 401,
                    "detail": "La sesión ha expirado. Por favor, inicia sesión nuevamente.",
                    "code": "TOKEN_EXPIRED",
                },
            ) from e
        except jwt.PyJWTError as e:
            logger.warning("Supabase JWT verification failed: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "No Autorizado",
                    "status": 401,
                    "detail": "El token de autenticación no es válido o está corrupto.",
                    "code": "INVALID_CREDENTIALS",
                },
            ) from e

        user_id_raw = payload.get("sub") or payload.get("user_id")
        if not user_id_raw:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "Token Inválido",
                    "status": 401,
                    "detail": "El token no contiene un identificador de usuario válido (sub).",
                    "code": "INVALID_TOKEN_SUBJECT",
                },
            )
        user_id = str(user_id_raw)
        email = payload.get("email")

        # ----------------------------------------------------------------------
        # Authoritative Resolution of Tenant, Role, and Courses from Database.
        #
        # `public.profiles` is the ONLY source of role and tenant. JWT claims
        # (`user_metadata`, `app_metadata`, `tenant_id`, `role`, ...) are NEVER
        # trusted for authorization: a user can edit `user_metadata` on the
        # client side with Supabase's public anon key.
        #
        # If the database cannot be reached, the request MUST fail closed with
        # 503 instead of falling back to claims or executing a protected
        # endpoint without a verified identity.
        # ----------------------------------------------------------------------
        tenant_id, role, authorized_course_ids = await _resolve_identity_from_db(user_id)

        return AuthenticatedUser(
            user_id=user_id,
            tenant_id=tenant_id,
            role=role,
            email=email,
            authorized_course_ids=authorized_course_ids,
        )

    # --------------------------------------------------------------------------
    # 2. Proxy Headers (Strictly Gated for Development & Testing)
    # --------------------------------------------------------------------------
    is_production = settings.ENVIRONMENT.lower() == "production"

    if x_user_id or x_tenant_id:
        if is_production:
            logger.error("SECURITY ALERT: Proxy headers (X-User-Id / X-Tenant-Id) rejected in production!")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "Cabeceras de Proxy Prohibidas",
                    "status": 401,
                    "detail": "Las cabeceras proxy de identidad están estrictamente prohibidas en producción. Se requiere Authorization: Bearer <jwt>.",
                    "code": "PROXY_HEADERS_FORBIDDEN",
                },
            )

        # Allowed strictly in development / test environments
        if x_user_id and x_tenant_id:
            course_set = (
                {c.strip() for c in x_course_ids.split(",") if c.strip()}
                if x_course_ids
                else set()
            )
            return AuthenticatedUser(
                user_id=x_user_id,
                tenant_id=x_tenant_id,
                role=x_user_role or "teacher",
                authorized_course_ids=course_set,
            )

    # --------------------------------------------------------------------------
    # 3. No Valid Credentials Provided
    # --------------------------------------------------------------------------
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail={
            "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
            "title": "No Autorizado",
            "status": 401,
            "detail": "Se requiere cabecera Authorization: Bearer <jwt> para acceder a este recurso.",
            "code": "MISSING_CREDENTIALS",
        },
    )


def require_role(*allowed_roles: str) -> Callable[..., AuthenticatedUser]:
    """Dependency factory checking that user holds at least one permitted role."""

    def role_checker(
        user: Annotated[AuthenticatedUser, Depends(get_current_user)],
    ) -> AuthenticatedUser:
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "No Autorizado",
                    "status": 401,
                    "detail": "Usuario no autenticado.",
                    "code": "UNAUTHORIZED",
                },
            )
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/forbidden",
                    "title": "Acceso Prohibido",
                    "status": 403,
                    "detail": f"El rol '{user.role}' no cuenta con permisos suficientes para esta operación.",
                    "code": "INSUFFICIENT_PERMISSIONS",
                },
            )
        return user

    return role_checker
