"""AWS Secrets Manager and Database DSN Resolution Module.

Provides secure retrieval and caching of database credentials for AWS Lambda execution.
Guarantees:
- Secrets retrieved once during service initialization and cached in memory.
- Passwords and connection strings are never exposed in log output (masked DSNs only).
- Failure to fetch or parse secrets results in controlled initialization failures (RuntimeError).
- Transparent fallback to DATABASE_URL when DATABASE_SECRET_ARN is not configured (local dev/tests).
"""

from __future__ import annotations

import json
import logging
import os
import urllib.parse
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)

_CACHED_DATABASE_DSN: str | None = None


def mask_database_dsn(url: str | None) -> str:
    """Mask credentials and sensitive tokens in database DSN to guarantee leak-free logging.

    Preserves brackets for IPv6 hostnames and handles URLs with or without scheme,
    passwords (including unescaped special characters), ports, or sensitive query parameters.
    """
    if not url:
        return "<empty>"
    try:
        # Split query string first
        query_part = ""
        base = url
        if "?" in base:
            base, query_part = base.split("?", 1)

        # Extract scheme prefix if present
        if "://" in base:
            scheme, remainder = base.split("://", 1)
            prefix = scheme + "://"
        else:
            prefix = ""
            remainder = base

        # Extract authority (creds + host:port) and path
        if "/" in remainder:
            authority, path = remainder.split("/", 1)
            path = "/" + path
        else:
            authority = remainder
            path = ""

        # In authority, credentials and host are separated by the LAST '@'
        if "@" in authority:
            creds, host = authority.rsplit("@", 1)
            if ":" in creds:
                user, _ = creds.split(":", 1)
                authority = f"{user}:***@{host}"
            else:
                authority = f"{creds}@{host}"

        masked_base = f"{prefix}{authority}{path}"

        if query_part:
            params = urllib.parse.parse_qsl(query_part, keep_blank_values=True)
            masked_params = []
            for k, v in params:
                if any(s in k.lower() for s in ("pass", "secret", "key", "token")):
                    masked_params.append((k, "***"))
                else:
                    masked_params.append((k, v))
            clean_query = urllib.parse.urlencode(masked_params, safe="*")
            return f"{masked_base}?{clean_query}"

        return masked_base
    except Exception:  # noqa: BLE001
        return "<invalid-database-url>"


def invalidate_cached_dsn() -> None:
    """Invalidate cached database DSN and terminate existing DB pool.

    Forces re-fetching fresh credentials from Secrets Manager and re-initializing
    the connection pool on the next database access.
    """
    global _CACHED_DATABASE_DSN
    logger.info("Invalidating cached database DSN; next connection attempt will re-fetch from Secrets Manager.")
    _CACHED_DATABASE_DSN = None
    try:
        from app.content_generation.infrastructure.database import get_current_db_pool

        pool = get_current_db_pool()
        if pool is not None and not getattr(pool, "_closed", True):
            pool.terminate()
            logger.info("Terminated existing asyncpg pool following DSN cache invalidation.")
    except Exception as exc:  # noqa: BLE001
        logger.debug("No active pool to terminate during DSN invalidation: %s", exc)


def reset_cached_dsn() -> None:
    """Clear cached database DSN (alias for invalidate_cached_dsn, used in unit tests)."""
    invalidate_cached_dsn()


def get_database_dsn(boto_client: Any = None) -> str:
    """Resolve database DSN from AWS Secrets Manager or environment settings.

    In AWS Lambda / production, when DATABASE_SECRET_ARN is configured, this retrieves
    the connection string from AWS Secrets Manager, caches it in memory for the life of the
    execution environment, and guarantees that raw credentials are never logged.

    If DATABASE_SECRET_ARN is empty or unset, it falls back to settings.DATABASE_URL.
    Controlled initialization errors (RuntimeError) are raised upon failure without
    exposing secret values in exceptions or logs.
    """
    global _CACHED_DATABASE_DSN

    if _CACHED_DATABASE_DSN is not None:
        return _CACHED_DATABASE_DSN

    secret_arn = (settings.DATABASE_SECRET_ARN or "").strip()
    if not secret_arn:
        raw_url = os.getenv("DATABASE_URL") or settings.DATABASE_URL or ""
        _CACHED_DATABASE_DSN = raw_url
        return raw_url

    # Extract region from ARN: arn:aws:secretsmanager:<region>:<account>:secret:...
    region = None
    arn_parts = secret_arn.split(":")
    if len(arn_parts) >= 4 and arn_parts[3]:
        region = arn_parts[3]
    if not region:
        region = getattr(settings, "AWS_REGION", "us-east-2")

    logger.info(
        "Resolving database credentials from AWS Secrets Manager (ARN: %s, Region: %s)...",
        secret_arn,
        region,
    )

    try:
        if boto_client is None:
            import boto3
            client = boto3.client("secretsmanager", region_name=region)
        else:
            client = boto_client

        response = client.get_secret_value(SecretId=secret_arn)
    except Exception as exc:
        logger.error(
            "Failed to retrieve database secret from AWS Secrets Manager (ARN: %s): %s",
            secret_arn,
            type(exc).__name__,
        )
        raise RuntimeError(
            f"Controlled initialization failure: unable to retrieve database credentials from Secrets Manager: {type(exc).__name__}"
        ) from exc

    secret_string = response.get("SecretString")
    if not secret_string and "SecretBinary" in response:
        secret_bytes = response["SecretBinary"]
        if isinstance(secret_bytes, bytes):
            secret_string = secret_bytes.decode("utf-8")
        elif isinstance(secret_bytes, str):
            secret_string = secret_bytes

    if not secret_string:
        logger.error(
            "Secrets Manager returned empty or non-string secret for ARN: %s",
            secret_arn,
        )
        raise RuntimeError(
            "Controlled initialization failure: Secrets Manager returned empty or non-string secret."
        )

    secret_string = secret_string.strip()
    if secret_string.startswith("export "):
        secret_string = secret_string[7:].strip()
    if secret_string.startswith("DATABASE_URL="):
        secret_string = secret_string[13:].strip().strip('"').strip("'")

    resolved_dsn = ""

    if secret_string.startswith("{"):
        try:
            payload = json.loads(secret_string)
            if isinstance(payload, dict):
                # Check for explicit DSN/URL keys
                for key in (
                    "DATABASE_URL",
                    "database_url",
                    "dsn",
                    "DATABASE_DSN",
                    "url",
                    "POSTGRES_URL",
                    "postgres_url",
                    "connectionString",
                    "connection_string",
                    "uri",
                ):
                    if payload.get(key):
                        resolved_dsn = str(payload[key]).strip()
                        break

                # If no direct URL key, build from discrete component keys
                if not resolved_dsn:
                    user = payload.get("username") or payload.get("user") or "postgres"
                    password = payload.get("password") or payload.get("pass") or ""
                    raw_host = str(payload.get("host") or payload.get("hostname") or "localhost")
                    port = payload.get("port") or 6543
                    if ":" in raw_host and not raw_host.startswith("["):
                        host_parts = raw_host.split(":", 1)
                        host = host_parts[0]
                        port = host_parts[1]
                    else:
                        host = raw_host

                    dbname = payload.get("dbname") or payload.get("database") or "postgres"
                    sslmode = payload.get("sslmode", "require")
                    encoded_user = urllib.parse.quote(str(user), safe="")
                    if password:
                        encoded_pass = urllib.parse.quote(str(password), safe="")
                        user_pass = f"{encoded_user}:{encoded_pass}@"
                    else:
                        user_pass = f"{encoded_user}@"
                    resolved_dsn = f"postgresql://{user_pass}{host}:{port}/{dbname}?sslmode={sslmode}"
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON secret from Secrets Manager: %s", type(exc).__name__)
            raise RuntimeError(
                "Controlled initialization failure: database secret contains invalid JSON."
            ) from exc
    else:
        resolved_dsn = secret_string

    if not resolved_dsn or not (
        resolved_dsn.startswith(("postgresql://", "postgres://", "postgresql+asyncpg://"))
    ):
        logger.error(
            "Secrets Manager secret payload does not conform to PostgreSQL DSN format for ARN: %s",
            secret_arn,
        )
        raise RuntimeError(
            "Controlled initialization failure: secret does not contain a valid PostgreSQL connection string."
        )

    _CACHED_DATABASE_DSN = resolved_dsn
    logger.info(
        "Successfully retrieved and cached database DSN from Secrets Manager: %s",
        mask_database_dsn(resolved_dsn),
    )
    return resolved_dsn
