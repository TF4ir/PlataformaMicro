"""Unit tests for document validation, security checks, and zip-bomb defenses."""

import pytest

from app.content_generation.exceptions import (
    FileTooLargeError,
    InvalidFileSignatureError,
    InvalidStoragePathError,
    MimeTypeMismatchError,
    UnauthorizedStorageAccessError,
    UnsupportedMimeTypeError,
    ZipBombDetectedError,
)
from app.content_generation.services.document_validation import (
    MAX_FILE_SIZE_BYTES,
    compute_sha256,
    validate_file_signature_and_mime,
    validate_file_size,
    validate_storage_authorization,
    validate_teacher_job_access,
)
from tests.content_generation.test_fixtures import (
    build_macro_pptx,
    build_script_pptx,
    build_traversal_pptx,
    build_valid_pdf,
    build_zip_bomb_pptx,
)


def test_file_size_validation_limits() -> None:
    """7. Archivo que exceda el límite de tamaño de 30 MB."""
    # 0 bytes -> InvalidFileSignatureError
    with pytest.raises(InvalidFileSignatureError):
        validate_file_size(b"")

    # Valid boundary size
    valid_data = b"%PDF-" + b"x" * 1024
    validate_file_size(valid_data)

    # Exceeding 30 MB
    large_data = b"%PDF-" + b"0" * (MAX_FILE_SIZE_BYTES + 10)
    with pytest.raises(FileTooLargeError) as exc_info:
        validate_file_size(large_data)

    assert exc_info.value.code == "FILE_TOO_LARGE"
    assert exc_info.value.status_code == 413


def test_mime_and_extension_mismatch() -> None:
    """8. Extensión y MIME que no coinciden con el contenido."""
    pdf_bytes = build_valid_pdf(["Texto de prueba"])

    # Extension .pdf declared as PPTX MIME -> MimeTypeMismatchError
    with pytest.raises(MimeTypeMismatchError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=pdf_bytes,
            original_filename="documento.pdf",
            declared_mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )
    assert exc_info.value.code == "MIME_TYPE_MISMATCH"

    # Extension .pptx declared as PDF MIME -> MimeTypeMismatchError
    with pytest.raises(MimeTypeMismatchError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=pdf_bytes,
            original_filename="presentacion.pptx",
            declared_mime="application/pdf",
        )
    assert exc_info.value.code == "MIME_TYPE_MISMATCH"

    # Binary signature does NOT match declared PDF
    fake_pdf_bytes = b"Hello world, I am not a real PDF at all"
    with pytest.raises(MimeTypeMismatchError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=fake_pdf_bytes,
            original_filename="fake.pdf",
            declared_mime="application/pdf",
        )
    assert exc_info.value.code == "MIME_TYPE_MISMATCH"

    # Unsupported MIME
    with pytest.raises(UnsupportedMimeTypeError) as exc_unsupported:
        validate_file_signature_and_mime(
            file_bytes=b"random",
            original_filename="eval.exe",
            declared_mime="application/x-msdownload",
        )
    assert exc_unsupported.value.code == "UNSUPPORTED_MIME_TYPE"


def test_pptx_zip_bomb_detection() -> None:
    """9. PPTX con contenido ZIP excesivamente grande o ratio sospechoso."""
    zip_bomb_bytes = build_zip_bomb_pptx()

    with pytest.raises(ZipBombDetectedError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=zip_bomb_bytes,
            original_filename="bomb.pptx",
            declared_mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    assert exc_info.value.code == "SUSPICIOUS_ARCHIVE_DETECTED"
    assert (
        "Zip Bomb" in exc_info.value.message_safe
        or "compresión" in exc_info.value.message_safe
    )


def test_pptx_path_traversal_detection() -> None:
    """PPTX con rutas maliciosas (..) dentro del archivo ZIP."""
    traversal_bytes = build_traversal_pptx()

    with pytest.raises(ZipBombDetectedError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=traversal_bytes,
            original_filename="traversal.pptx",
            declared_mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        )

    assert exc_info.value.code == "SUSPICIOUS_ARCHIVE_DETECTED"


def test_storage_authorization_tenant_check() -> None:
    """12. Rechazo de archivos no autorizados para el tenant correspondiente."""
    tenant_a = "550e8400-e29b-41d4-a716-446655440000"
    tenant_b = "660e8400-e29b-41d4-a716-446655440001"

    # Authorized path for tenant A
    valid_path = f"{tenant_a}/materials/ciencias_tema1.pdf"
    validate_storage_authorization(valid_path, tenant_id=tenant_a)

    # Attempt to access tenant B's material with tenant A's context
    with pytest.raises(UnauthorizedStorageAccessError) as exc_info:
        validate_storage_authorization(valid_path, tenant_id=tenant_b)

    assert exc_info.value.code == "UNAUTHORIZED_STORAGE_ACCESS"

    # Reject unauthorized bucket
    with pytest.raises(UnauthorizedStorageAccessError) as exc_info:
        validate_storage_authorization(
            valid_path,
            tenant_id=tenant_a,
            storage_bucket="public-bucket",
        )
    assert exc_info.value.code == "UNAUTHORIZED_STORAGE_ACCESS"


def test_storage_authorization_path_traversal_and_external_urls() -> None:
    """Rechazo de URLs externas y escapes de directorio en storage_path."""
    tenant = "550e8400-e29b-41d4-a716-446655440000"

    # Reject external URLs
    with pytest.raises(InvalidStoragePathError) as exc_info:
        validate_storage_authorization("https://evil.com/payload.pdf", tenant_id=tenant)
    assert exc_info.value.code == "INVALID_STORAGE_PATH"

    # Reject path traversal
    with pytest.raises(InvalidStoragePathError):
        validate_storage_authorization(f"{tenant}/../../etc/passwd", tenant_id=tenant)

    # Reject absolute path
    with pytest.raises(InvalidStoragePathError):
        validate_storage_authorization(f"/{tenant}/materials/doc.pdf", tenant_id=tenant)


def test_compute_sha256() -> None:
    """Verificación del hash criptográfico SHA-256."""
    data = b"synthetic content for testing checksum"
    checksum = compute_sha256(data)
    assert len(checksum) == 64
    assert (
        checksum == "27bf65f6dad3100348c330d3a4c631b8badbe1dc554aae23c71bffa850b4fe36"
    )


def test_pptx_active_content_and_macro_rejection() -> None:
    """Detección y rechazo de macros VBA y scripts ejecutables en PPTX."""
    pptx_mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )

    # 1. VBA Macro rejection
    macro_bytes = build_macro_pptx()
    with pytest.raises(InvalidFileSignatureError) as exc_info:
        validate_file_signature_and_mime(
            file_bytes=macro_bytes,
            original_filename="presentacion_con_macro.pptx",
            declared_mime=pptx_mime,
        )
    assert "macros VBA" in exc_info.value.message_safe

    # 2. Embedded executable script rejection
    script_bytes = build_script_pptx()
    with pytest.raises(InvalidFileSignatureError) as exc_script:
        validate_file_signature_and_mime(
            file_bytes=script_bytes,
            original_filename="presentacion_con_script.pptx",
            declared_mime=pptx_mime,
        )
    assert "scripts o ejecutables" in exc_script.value.message_safe


def test_storage_authorization_null_bytes_and_consecutive_slashes() -> None:
    """Detección y rechazo de caracteres nulos y barras dobles en rutas de storage."""
    tenant = "550e8400-e29b-41d4-a716-446655440000"

    # Null byte attack
    with pytest.raises(InvalidStoragePathError):
        validate_storage_authorization(
            f"{tenant}/\x00materials/doc.pdf", tenant_id=tenant
        )

    # Double slash attack
    with pytest.raises(InvalidStoragePathError):
        validate_storage_authorization(f"{tenant}//materials/doc.pdf", tenant_id=tenant)

    # Trailing slash
    with pytest.raises(InvalidStoragePathError):
        validate_storage_authorization(f"{tenant}/materials/", tenant_id=tenant)


def test_teacher_job_access_validation() -> None:
    """Verificación de permisos del docente sobre el trabajo y curso asociado."""
    tenant_a = "550e8400-e29b-41d4-a716-446655440000"
    tenant_b = "660e8400-e29b-41d4-a716-446655440001"
    teacher_1 = "11111111-1111-1111-1111-111111111111"
    teacher_2 = "22222222-2222-2222-2222-222222222222"
    course_ciencias = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    course_historia = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # 1. Student role is strictly denied
    with pytest.raises(UnauthorizedStorageAccessError) as exc_student:
        validate_teacher_job_access(
            job_tenant_id=tenant_a,
            job_created_by=teacher_1,
            job_course_id=course_ciencias,
            tenant_id=tenant_a,
            requesting_user_id=teacher_1,
            user_role="student",
        )
    assert "estudiantes" in exc_student.value.message_safe.lower()

    # 2. Cross-tenant is denied
    with pytest.raises(UnauthorizedStorageAccessError):
        validate_teacher_job_access(
            job_tenant_id=tenant_a,
            job_created_by=teacher_1,
            job_course_id=course_ciencias,
            tenant_id=tenant_b,
            requesting_user_id=teacher_1,
            user_role="teacher",
        )

    # 3. Teacher who is NOT creator is denied
    with pytest.raises(UnauthorizedStorageAccessError) as exc_owner:
        validate_teacher_job_access(
            job_tenant_id=tenant_a,
            job_created_by=teacher_1,
            job_course_id=course_ciencias,
            tenant_id=tenant_a,
            requesting_user_id=teacher_2,
            user_role="teacher",
        )
    assert "creador" in exc_owner.value.message_safe.lower()

    # 4. Teacher who is not assigned to the course is denied
    with pytest.raises(UnauthorizedStorageAccessError) as exc_course:
        validate_teacher_job_access(
            job_tenant_id=tenant_a,
            job_created_by=teacher_1,
            job_course_id=course_ciencias,
            tenant_id=tenant_a,
            requesting_user_id=teacher_1,
            user_role="teacher",
            authorized_course_ids=[
                course_historia
            ],  # Only assigned to history, not science
        )
    assert "curso" in exc_course.value.message_safe.lower()

    # 5. Teacher who is creator and assigned to the course is authorized
    validate_teacher_job_access(
        job_tenant_id=tenant_a,
        job_created_by=teacher_1,
        job_course_id=course_ciencias,
        tenant_id=tenant_a,
        requesting_user_id=teacher_1,
        user_role="teacher",
        authorized_course_ids=[course_ciencias, course_historia],
    )

    # 6. Admin has tenant-wide access
    validate_teacher_job_access(
        job_tenant_id=tenant_a,
        job_created_by=teacher_1,
        job_course_id=course_ciencias,
        tenant_id=tenant_a,
        requesting_user_id="admin-id",
        user_role="admin",
    )
