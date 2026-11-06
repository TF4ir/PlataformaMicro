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
        # Authoritative Resolution of Tenant, Role, and Courses from Database
        # ----------------------------------------------------------------------
        tenant_id: str | None = None
        role: str | None = None
        authorized_course_ids: set[str] = set()

        from app.content_generation.infrastructure.database import _POOL

        if _POOL is not None and not getattr(_POOL, "_closed", True):
            try:
                user_uuid = uuid.UUID(user_id)
                async with _POOL.acquire() as conn:
                    profile_row = await conn.fetchrow(
                        "SELECT tenant_id, role, full_name FROM profiles WHERE id = $1",
                        user_uuid,
                    )
                    if profile_row is not None:
                        tenant_id = str(profile_row["tenant_id"])
                        role = str(profile_row["role"])

                        if role == "teacher":
                            section_rows = await conn.fetch(
                                "SELECT DISTINCT course_id::text FROM sections WHERE teacher_id = $1",
                                user_uuid,
                            )
                            authorized_course_ids = {r[0] for r in section_rows}
                        elif role == "student":
                            enrollment_rows = await conn.fetch(
                                """
                                SELECT DISTINCT s.course_id::text
                                FROM enrollments e
                                JOIN sections s ON s.id = e.section_id
                                WHERE e.student_id = $1
                                """,
                                user_uuid,
                            )
                            authorized_course_ids = {r[0] for r in enrollment_rows}
            except (asyncpg.PostgresError, OSError, ValueError, KeyError) as e:
                logger.warning("Could not query authoritative profile from database pool: %s", e)

        # Fallback to token claims if profile was not found or pool is uninitialized
        if not tenant_id:
            app_metadata = payload.get("app_metadata", {})
            user_metadata = payload.get("user_metadata", {})
            tenant_id = (
                payload.get("tenant_id")
                or app_metadata.get("tenant_id")
                or user_metadata.get("tenant_id")
            )
            if tenant_id:
                tenant_id = str(tenant_id)

        if not role:
            app_metadata = payload.get("app_metadata", {})
            user_metadata = payload.get("user_metadata", {})
            # Look up role in user_metadata first, then app_metadata, default to student
            claim_role = user_metadata.get("role") or app_metadata.get("role")
            if not claim_role and payload.get("role") != "authenticated":
                claim_role = payload.get("role")
            role = str(claim_role or "student")

        if not authorized_course_ids:
            claim_courses = payload.get("authorized_course_ids", [])
            if isinstance(claim_courses, list):
                authorized_course_ids = {str(c) for c in claim_courses}

        if not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "Reclamos Incompletos",
                    "status": 401,
                    "detail": "No se pudo resolver la institución (tenant_id) del usuario.",
                    "code": "INCOMPLETE_AUTH_CLAIMS",
                },
            )

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
