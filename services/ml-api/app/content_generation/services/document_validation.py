"""Security and structural validation for uploaded curriculum documents.

Guarantees defense-in-depth against malicious files, zip bombs, unauthorized
storage paths, and MIME/signature mismatches.
"""

import hashlib
import io
import os
import re
import zipfile

from app.content_generation.exceptions import (
    FileTooLargeError,
    InvalidFileSignatureError,
    InvalidStoragePathError,
    MimeTypeMismatchError,
    UnauthorizedStorageAccessError,
    UnsupportedMimeTypeError,
    ZipBombDetectedError,
)

# Architectural Constraints
MAX_FILE_SIZE_BYTES: int = 31457280  # 30 MB (30 * 1024 * 1024)
AUTHORIZED_STORAGE_BUCKET: str = "teacher-materials"

# Allowed MIME types and corresponding lowercased extensions
MIME_TO_EXTENSIONS: dict[str, set[str]] = {
    "application/pdf": {".pdf"},
    "application/vnd.openxmlformats-officedocument.presentationml.presentation": {
        ".pptx"
    },
}

# Zip Bomb & Decompression Protection Limits
MAX_UNCOMPRESSED_ZIP_BYTES: int = 125829120  # 120 MB
MAX_ZIP_COMPRESSION_RATIO: float = 30.0
MAX_ZIP_ENTRIES: int = 5000

# Magic signatures
PDF_MAGIC_BYTES: bytes = b"%PDF-"
ZIP_MAGIC_BYTES: bytes = b"PK\x03\x04"
ZIP_MAGIC_EMPTY_OR_SPANNED: tuple[bytes, ...] = (
    b"PK\x03\x04",
    b"PK\x05\x06",
    b"PK\x07\x08",
)


def compute_sha256(data: bytes) -> str:
    """Compute standard SHA-256 hex digest for binary data."""
    return hashlib.sha256(data).hexdigest()


def validate_file_size(file_bytes: bytes) -> None:
    """Validate that the file size is within the allowed 30 MB boundary and non-empty."""
    size = len(file_bytes)
    if size == 0:
        raise InvalidFileSignatureError("El archivo recibido tiene 0 bytes (vacío).")
    if size > MAX_FILE_SIZE_BYTES:
        raise FileTooLargeError(
            f"El archivo excede el tamaño máximo permitido de 30 MB (recibido: {size} bytes).",
            details={"file_size_bytes": size, "limit_bytes": MAX_FILE_SIZE_BYTES},
        )


def validate_storage_authorization(
    storage_path: str,
    tenant_id: str,
    storage_bucket: str = AUTHORIZED_STORAGE_BUCKET,
) -> None:
    """Verify that the storage path belongs strictly to the authorized tenant and bucket.

    Enforces:
    - Bucket must be 'teacher-materials'.
    - Path must not contain null bytes.
    - Path must not contain path traversal ('..' or '\\').
    - Path must not be an arbitrary external URL (no protocol schemes).
    - Path must not have consecutive slashes.
    - First segment of path must match the authenticated tenant_id.
    """
    if storage_bucket != AUTHORIZED_STORAGE_BUCKET:
        raise UnauthorizedStorageAccessError(
            f"Acceso denegado: el bucket '{storage_bucket}' no está autorizado.",
            details={
                "bucket": storage_bucket,
                "expected_bucket": AUTHORIZED_STORAGE_BUCKET,
            },
        )

    # Check for null bytes
    if "\0" in storage_path:
        raise InvalidStoragePathError(
            "Ruta de almacenamiento con caracteres nulos no permitidos.",
            details={"storage_path": "[REDACTED]"},
        )

    # Check for external URLs
    if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", storage_path):
        raise InvalidStoragePathError(
            "Se prohíbe el uso de URLs externas. Solo se admiten rutas internas de Supabase Storage.",
            details={"storage_path": "[REDACTED]"},
        )

    # Normalize and detect directory traversal attempts
    cleaned_path = storage_path.strip().replace("\\", "/")
    if (
        cleaned_path.startswith("/")
        or cleaned_path.endswith("/")
        or "//" in cleaned_path
        or ".." in cleaned_path.split("/")
    ):
        raise InvalidStoragePathError(
            "Ruta de almacenamiento con formato no permitido o intento de escape de directorio.",
            details={"storage_path": "[REDACTED]"},
        )

    segments = cleaned_path.split("/")
    if len(segments) < 2:
        raise InvalidStoragePathError(
            "La ruta de almacenamiento debe contener al menos el prefijo del tenant y el identificador de archivo.",
            details={"storage_path": "[REDACTED]"},
        )

    declared_tenant = segments[0]
    if declared_tenant.lower() != tenant_id.lower():
        raise UnauthorizedStorageAccessError(
            "Acceso denegado: el archivo pertenece a un tenant distinto al autorizado.",
            details={"tenant_id": tenant_id},
        )


def validate_teacher_job_access(
    job_tenant_id: str,
    job_created_by: str,
    job_course_id: str | None,
    tenant_id: str,
    requesting_user_id: str | None = None,
    user_role: str | None = None,
    authorized_course_ids: set[str] | list[str] | None = None,
) -> None:
    """Verify that a user is authorized to process or access a content generation job.

    Implements the security constraints defined in ADR-0004 and M1 RLS policies:
    - Students are strictly forbidden from accessing content generation jobs.
    - Tenant isolation is mandatory.
    - Teachers can only access jobs they created (auth.uid() = created_by).
    - Teachers must be assigned to the course associated with the job (if course_id is set).
    - Admins and super_admins have elevated tenant-level or global access.
    """
    normalized_role = (user_role or "teacher").lower()

    if normalized_role == "student":
        raise UnauthorizedStorageAccessError(
            "Acceso denegado: los estudiantes no tienen autorización para procesar materiales docentes.",
            details={"role": user_role},
        )

    # Super admin bypasses tenant restriction
    if normalized_role == "super_admin":
        return

    # Tenant boundary check
    if job_tenant_id.lower() != tenant_id.lower():
        raise UnauthorizedStorageAccessError(
            "Acceso denegado: el trabajo pertenece a otro tenant institucional.",
            details={"job_tenant_id": job_tenant_id, "requesting_tenant_id": tenant_id},
        )

    # Tenant admin has access to all jobs in their tenant
    if normalized_role == "admin":
        return

    # Teacher checks: ownership and course assignment
    if (
        requesting_user_id is not None
        and job_created_by.lower() != requesting_user_id.lower()
    ):
        raise UnauthorizedStorageAccessError(
            "Acceso denegado: el docente no es el creador de este trabajo de generación.",
            details={
                "created_by": job_created_by,
                "requesting_user": requesting_user_id,
            },
        )

    if job_course_id is not None and authorized_course_ids is not None:
        course_set = {str(cid).lower() for cid in authorized_course_ids}
        if job_course_id.lower() not in course_set:
            raise UnauthorizedStorageAccessError(
                "Acceso denegado: el docente no tiene asignado el curso vinculado a este material.",
                details={"course_id": job_course_id},
            )


def validate_file_signature_and_mime(
    file_bytes: bytes,
    original_filename: str,
    declared_mime: str,
) -> str:
    """Strictly validate declared MIME, file extension, and binary magic bytes.

    Returns normalized document format type ('pdf' or 'pptx').
    """
    # 1. Validate size first
    validate_file_size(file_bytes)

    # 2. Check declared MIME against allowed catalog
    if declared_mime not in MIME_TO_EXTENSIONS:
        raise UnsupportedMimeTypeError(
            f"Tipo MIME no admitido: {declared_mime}. Se requiere PDF o PPTX.",
            details={"declared_mime": declared_mime},
        )

    # 3. Check filename extension against declared MIME
    _, ext = os.path.splitext(original_filename.lower())
    allowed_extensions = MIME_TO_EXTENSIONS[declared_mime]
    if ext not in allowed_extensions:
        raise MimeTypeMismatchError(
            f"La extensión '{ext}' del archivo '{original_filename}' no coincide con el MIME declarado '{declared_mime}'.",
            details={
                "filename": original_filename,
                "extension": ext,
                "declared_mime": declared_mime,
            },
        )

    # 4. Check binary magic signature
    if declared_mime == "application/pdf":
        if not file_bytes.startswith(PDF_MAGIC_BYTES):
            raise MimeTypeMismatchError(
                "La firma binaria del archivo no corresponde a un documento PDF válido (falta firma %PDF-).",
                details={"expected_magic": "%PDF-", "declared_mime": declared_mime},
            )
        return "pdf"

    elif (
        declared_mime
        == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    ):
        # Check ZIP magic header
        if not any(
            file_bytes.startswith(magic) for magic in ZIP_MAGIC_EMPTY_OR_SPANNED
        ):
            raise MimeTypeMismatchError(
                "La firma binaria del archivo no corresponde a un contenedor PPTX/ZIP válido.",
                details={"expected_magic": "PK...", "declared_mime": declared_mime},
            )

        # Inspect internal ZIP structure and defensive limits
        _validate_pptx_zip_container(file_bytes)
        return "pptx"

    raise UnsupportedMimeTypeError(f"Tipo de archivo desconocido: {declared_mime}")


def _validate_pptx_zip_container(file_bytes: bytes) -> None:
    """Inspect PPTX ZIP container structure and enforce zip bomb defenses."""
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as zf:
            infolist = zf.infolist()
            total_entries = len(infolist)

            if total_entries == 0:
                raise InvalidFileSignatureError(
                    "El contenedor PPTX no contiene archivos internos."
                )

            if total_entries > MAX_ZIP_ENTRIES:
                raise ZipBombDetectedError(
                    f"El contenedor PPTX supera el límite defensivo de {MAX_ZIP_ENTRIES} entradas.",
                    details={"total_entries": total_entries},
                )

            total_uncompressed_bytes = 0
            compressed_size = max(len(file_bytes), 1)
            filenames = set()

            for info in infolist:
                # Path traversal check within zip archive
                name = info.filename.replace("\\", "/")
                if name.startswith("/") or ".." in name.split("/"):
                    raise ZipBombDetectedError(
                        "Ruta maliciosa detectada dentro del contenedor PPTX.",
                        details={"internal_path": "[REDACTED]"},
                    )

                filenames.add(name)
                total_uncompressed_bytes += info.file_size

                if total_uncompressed_bytes > MAX_UNCOMPRESSED_ZIP_BYTES:
                    raise ZipBombDetectedError(
                        f"El tamaño descomprimido supera el límite defensivo de {MAX_UNCOMPRESSED_ZIP_BYTES // (1024 * 1024)} MB.",
                        details={
                            "uncompressed_bytes": total_uncompressed_bytes,
                            "limit_bytes": MAX_UNCOMPRESSED_ZIP_BYTES,
                        },
                    )

            # Compression ratio check
            ratio = total_uncompressed_bytes / compressed_size
            if ratio > MAX_ZIP_COMPRESSION_RATIO:
                raise ZipBombDetectedError(
                    f"Ratio de compresión sospechoso ({ratio:.1f}x > límite {MAX_ZIP_COMPRESSION_RATIO:.1f}x). Posible Zip Bomb.",
                    details={"compression_ratio": ratio},
                )

            # Active content, VBA macros, and dangerous script/executable detection
            for name in filenames:
                lower_name = name.lower()
                if lower_name.endswith(("vbaproject.bin", "vbadata.xml")):
                    raise InvalidFileSignatureError(
                        "El archivo PPTX contiene macros VBA activas, las cuales están estrictamente prohibidas por seguridad.",
                        details={"forbidden_entry": "vbaProject"},
                    )
                if re.search(
                    r"\.(exe|bat|cmd|sh|vbs|js|ps1|scr|jar|com|pif|dll|hta|cpl|wsf)$",
                    lower_name,
                ):
                    raise InvalidFileSignatureError(
                        "El archivo PPTX contiene scripts o ejecutables embebidos no autorizados.",
                        details={"forbidden_entry": "[REDACTED]"},
                    )

            # Required OpenXML structure elements for PowerPoint
            has_content_types = "[Content_Types].xml" in filenames
            has_presentation_xml = any(
                f.startswith("ppt/") and f.endswith("presentation.xml")
                for f in filenames
            )

            if not has_content_types or not has_presentation_xml:
                raise InvalidFileSignatureError(
                    "El archivo ZIP no contiene la estructura canónica de una presentación PPTX (faltan [Content_Types].xml o ppt/presentation.xml).",
                    details={
                        "has_content_types": has_content_types,
                        "has_presentation_xml": has_presentation_xml,
                    },
                )

    except zipfile.BadZipFile as e:
        raise InvalidFileSignatureError(
            "El archivo ZIP está corrupto o mal formado.",
            details={"error": str(e)},
        )
