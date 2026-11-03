"""Storage client abstractions and adapters for private document retrieval.

Guarantees authorized retrieval from the private 'teacher-materials' Supabase Storage bucket.
"""

from typing import Protocol

from app.content_generation.exceptions import (
    CorruptDocumentError,
    UnauthorizedStorageAccessError,
)


class StorageClientProtocol(Protocol):
    """Protocol defining storage operations for curriculum materials."""

    async def download_file(
        self,
        storage_bucket: str,
        storage_path: str,
        tenant_id: str,
    ) -> bytes:
        """Download file bytes from private storage after verifying tenant authorization."""
        ...


class InMemoryStorageClient:
    """In-memory storage adapter for unit testing and offline development."""

    def __init__(self) -> None:
        # Key: (storage_bucket, storage_path) -> bytes
        self._storage: dict[tuple[str, str], bytes] = {}

    def upload_file(
        self,
        storage_bucket: str,
        storage_path: str,
        data: bytes,
    ) -> None:
        """Store simulated file bytes."""
        self._storage[(storage_bucket, storage_path)] = data

    async def download_file(
        self,
        storage_bucket: str,
        storage_path: str,
        tenant_id: str,
    ) -> bytes:
        """Download file bytes validating tenant authorization."""
        from app.content_generation.services.document_validation import (
            validate_storage_authorization,
        )

        validate_storage_authorization(storage_path, tenant_id, storage_bucket)

        key = (storage_bucket, storage_path)
        if key not in self._storage:
            raise CorruptDocumentError(
                "El archivo no fue encontrado en el almacenamiento privado.",
                details={"storage_path": "[REDACTED]", "bucket": storage_bucket},
            )
        return self._storage[key]


class SupabaseStorageClient:
    """Production Supabase Storage client using authorized HTTP service credentials."""

    def __init__(
        self,
        supabase_url: str,
        service_role_key: str,
    ) -> None:
        self._supabase_url = supabase_url.rstrip("/")
        self._service_role_key = service_role_key

    async def download_file(
        self,
        storage_bucket: str,
        storage_path: str,
        tenant_id: str,
    ) -> bytes:
        """Download object bytes from Supabase Storage private endpoint."""
        from app.content_generation.services.document_validation import (
            validate_storage_authorization,
        )

        validate_storage_authorization(storage_path, tenant_id, storage_bucket)

        # In production, httpx async client downloads with Authorization: Bearer <service_role_key>
        import httpx

        endpoint = f"{self._supabase_url}/storage/v1/object/authenticated/{storage_bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self._service_role_key}",
            "apikey": self._service_role_key,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.get(endpoint, headers=headers)
            if resp.status_code == 404:
                raise CorruptDocumentError(
                    "El archivo no existe en el bucket de almacenamiento.",
                    details={"storage_path": "[REDACTED]"},
                )
            if resp.status_code in (401, 403):
                raise UnauthorizedStorageAccessError(
                    "Credenciales de backend insuficientes para acceder a Storage.",
                )
            if resp.status_code >= 400:
                raise CorruptDocumentError(
                    f"Error de almacenamiento HTTP {resp.status_code}.",
                )
            return resp.content
