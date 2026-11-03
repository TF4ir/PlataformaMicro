"""Authentication and authorization dependencies for FastAPI endpoints."""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Annotated

import jwt
from fastapi import Depends, Header, HTTPException, status

from app.core.config import settings

logger = logging.getLogger(__name__)


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
    """Extract authenticated user and institutional tenant context."""
    # 1. Direct proxy headers (for dev, service-to-service, and integration tests)
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

    # 2. Bearer JWT Token
    if authorization and authorization.startswith("Bearer "):
        token = authorization.split("Bearer ", 1)[1].strip()
        try:
            if settings.SUPABASE_JWT_SECRET:
                payload = jwt.decode(
                    token,
                    settings.SUPABASE_JWT_SECRET,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            else:
                # In development or testing without configured secret, decode payload without verification
                payload = jwt.decode(
                    token,
                    options={"verify_signature": False},
                )
        except Exception as e:
            logger.warning("Failed to decode JWT token: %s", e)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "No Autorizado",
                    "status": 401,
                    "detail": "El token de autenticación no es válido o ha expirado.",
                    "code": "INVALID_CREDENTIALS",
                },
            ) from e

        user_id = payload.get("sub") or payload.get("user_id")
        app_metadata = payload.get("app_metadata", {})
        user_metadata = payload.get("user_metadata", {})

        tenant_id = (
            payload.get("tenant_id")
            or app_metadata.get("tenant_id")
            or user_metadata.get("tenant_id")
        )
        role = (
            payload.get("role")
            or app_metadata.get("role")
            or user_metadata.get("role")
            or "teacher"
        )
        email = payload.get("email")

        if not user_id or not tenant_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "type": "https://api.plataformamicro.edu.pe/errors/unauthorized",
                    "title": "No Autorizado",
                    "status": 401,
                    "detail": "El token no contiene los reclamos de identidad o institución requeridos.",
                    "code": "INCOMPLETE_AUTH_CLAIMS",
                },
            )

        courses_raw = payload.get("authorized_course_ids", [])
        return AuthenticatedUser(
            user_id=str(user_id),
            tenant_id=str(tenant_id),
            role=str(role),
            email=email,
            authorized_course_ids=set(courses_raw),
        )

    # 3. No credentials provided
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

