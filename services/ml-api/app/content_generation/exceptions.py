"""Domain exceptions for assisted content generation and document extraction.

All exceptions provide safe, sanitized error codes and messages suitable for
client response and audit logging without leaking internal paths, credentials,
or infrastructure secrets.
"""

from typing import Any


class ContentGenerationError(Exception):
    """Base exception for all content generation errors."""

    def __init__(
        self,
        message_safe: str,
        code: str = "CONTENT_GENERATION_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message_safe)
        self.message_safe = message_safe
        self.code = code
        self.status_code = status_code
        self.details = details or {}


# ==============================================================================
# Security & Pre-processing Violations
# ==============================================================================


class DocumentSecurityError(ContentGenerationError):
    """Base class for document security violations."""

    def __init__(
        self,
        message_safe: str,
        code: str = "DOCUMENT_SECURITY_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class FileTooLargeError(DocumentSecurityError):
    """Raised when document size exceeds the allowed limit (30 MB)."""

    def __init__(
        self,
        message_safe: str = "El archivo excede el tamaño máximo permitido de 30 MB.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="FILE_TOO_LARGE",
            status_code=413,
            details=details,
        )


class UnsupportedMimeTypeError(DocumentSecurityError):
    """Raised when file extension or MIME is not among allowed types (PDF, PPTX)."""

    def __init__(
        self,
        message_safe: str = "Formato de archivo no admitido. Solo se admiten archivos PDF y PPTX.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="UNSUPPORTED_MIME_TYPE",
            status_code=415,
            details=details,
        )


class MimeTypeMismatchError(DocumentSecurityError):
    """Raised when declared MIME type does not match actual binary magic signature."""

    def __init__(
        self,
        message_safe: str = "El tipo de contenido declarado no coincide con la firma binaria real del archivo.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="MIME_TYPE_MISMATCH",
            status_code=400,
            details=details,
        )


class InvalidFileSignatureError(DocumentSecurityError):
    """Raised when file binary headers or magic bytes are invalid or corrupt."""

    def __init__(
        self,
        message_safe: str = "La firma binaria o estructura básica del archivo no es válida.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_FILE_SIGNATURE",
            status_code=400,
            details=details,
        )


class ZipBombDetectedError(DocumentSecurityError):
    """Raised when a PPTX container exhibits zip bomb characteristics or dangerous paths."""

    def __init__(
        self,
        message_safe: str = "El contenedor del archivo supera los límites seguros de descompresión o presenta anomalías de compresión.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="SUSPICIOUS_ARCHIVE_DETECTED",
            status_code=400,
            details=details,
        )


class UnauthorizedStorageAccessError(DocumentSecurityError):
    """Raised when storage path or bucket is not authorized for the requesting tenant/user."""

    def __init__(
        self,
        message_safe: str = "No cuenta con autorización para acceder al archivo de almacenamiento solicitado.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="UNAUTHORIZED_STORAGE_ACCESS",
            status_code=403,
            details=details,
        )


class InvalidStoragePathError(DocumentSecurityError):
    """Raised when storage path format is invalid, absolute, or attempts traversal."""

    def __init__(
        self,
        message_safe: str = "La ruta de almacenamiento especificada es inválida.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_STORAGE_PATH",
            status_code=400,
            details=details,
        )


# ==============================================================================
# Extraction & Parsing Violations
# ==============================================================================


class DocumentExtractionError(ContentGenerationError):
    """Base class for document parsing and text extraction errors."""

    def __init__(
        self,
        message_safe: str,
        code: str = "DOCUMENT_EXTRACTION_ERROR",
        status_code: int = 422,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class CorruptDocumentError(DocumentExtractionError):
    """Raised when a document is structurally corrupted and cannot be parsed."""

    def __init__(
        self,
        message_safe: str = "El archivo se encuentra dañado o no puede ser interpretado.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="CORRUPT_DOCUMENT",
            status_code=422,
            details=details,
        )


class EncryptedDocumentError(DocumentExtractionError):
    """Raised when a PDF is password protected or encrypted."""

    def __init__(
        self,
        message_safe: str = "El documento PDF está protegido con contraseña o cifrado y no puede procesarse.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="ENCRYPTED_DOCUMENT",
            status_code=422,
            details=details,
        )


class EmptyDocumentError(DocumentExtractionError):
    """Raised when a document has zero pages or slides."""

    def __init__(
        self,
        message_safe: str = "El documento no contiene páginas o diapositivas para procesar.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EMPTY_DOCUMENT",
            status_code=422,
            details=details,
        )


class NoExtractableTextError(DocumentExtractionError):
    """Raised when a document has pages/slides but zero digital text (e.g. scanned image)."""

    def __init__(
        self,
        message_safe: str = "No se encontró texto extraíble en el documento. Si es un documento escaneado, requiere OCR.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="NO_EXTRACTABLE_TEXT",
            status_code=422,
            details=details,
        )


class ExtractionLimitExceededError(DocumentExtractionError):
    """Raised when page, slide, or character counts exceed defensive limits."""

    def __init__(
        self,
        message_safe: str = "El documento excede el límite máximo de páginas, diapositivas o caracteres permitidos.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EXTRACTION_LIMIT_EXCEEDED",
            status_code=422,
            details=details,
        )


# ==============================================================================
# Job Lifecycle Violations
# ==============================================================================


class JobLifecycleError(ContentGenerationError):
    """Base class for job state and transition violations."""

    def __init__(
        self,
        message_safe: str,
        code: str = "JOB_LIFECYCLE_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class JobNotFoundError(JobLifecycleError):
    """Raised when content generation job is not found in database."""

    def __init__(
        self,
        message_safe: str = "El trabajo de generación no existe.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="JOB_NOT_FOUND",
            status_code=404,
            details=details,
        )


class InvalidJobStateTransitionError(JobLifecycleError):
    """Raised when an illegal status transition is attempted."""

    def __init__(
        self,
        message_safe: str = "Transición de estado del trabajo no permitida.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_JOB_STATE_TRANSITION",
            status_code=409,
            details=details,
        )


# ==============================================================================
# LLM Provider & Generation Violations
# ==============================================================================


class GenerationProviderError(ContentGenerationError):
    """Base class for errors originating from the LLM generation provider."""

    def __init__(
        self,
        message_safe: str = "Error en el proveedor de generación de preguntas.",
        code: str = "GENERATION_PROVIDER_ERROR",
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class UnsupportedProviderError(GenerationProviderError):
    """Raised when configured LLM provider is not implemented or invalid."""

    def __init__(
        self,
        message_safe: str = "El proveedor de generación LLM configurado no es compatible o no está soportado.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="UNSUPPORTED_LLM_PROVIDER",
            status_code=500,
            details=details,
        )


class InvalidProviderConfigurationError(GenerationProviderError):
    """Raised when provider configuration or credentials are missing or invalid."""

    def __init__(
        self,
        message_safe: str = "La configuración o credenciales del proveedor LLM son inválidas o están incompletas.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_PROVIDER_CONFIGURATION",
            status_code=500,
            details=details,
        )


class ProviderAuthenticationError(GenerationProviderError):
    """Raised when LLM provider rejects authentication or API key."""

    def __init__(
        self,
        message_safe: str = "Error de autenticación con el proveedor LLM. Verifique las credenciales de acceso.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="PROVIDER_AUTHENTICATION_ERROR",
            status_code=502,
            details=details,
        )


class ProviderRateLimitError(GenerationProviderError):
    """Raised when provider rate limits or quotas are exceeded."""

    def __init__(
        self,
        message_safe: str = "Se excedió la tasa de peticiones o la cuota del proveedor LLM.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="PROVIDER_RATE_LIMIT_EXCEEDED",
            status_code=429,
            details=details,
        )


class ProviderTimeoutError(GenerationProviderError):
    """Raised when an LLM provider request times out."""

    def __init__(
        self,
        message_safe: str = "El proveedor LLM no respondió dentro del tiempo límite establecido.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="PROVIDER_TIMEOUT",
            status_code=504,
            details=details,
        )


class ProviderResponseFormatError(GenerationProviderError):
    """Raised when provider produces invalid JSON, truncated output or schema mismatches."""

    def __init__(
        self,
        message_safe: str = "La respuesta devuelta por el proveedor LLM no tiene un formato válido o fue truncada.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="PROVIDER_RESPONSE_FORMAT_ERROR",
            status_code=502,
            details=details,
        )


# ==============================================================================
# Draft Validation Violations
# ==============================================================================


class DraftValidationError(ContentGenerationError):
    """Base class for question draft structural and reference validation errors."""

    def __init__(
        self,
        message_safe: str = "El borrador de pregunta generado no cumple con las reglas de validación.",
        code: str = "DRAFT_VALIDATION_ERROR",
        status_code: int = 422,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class EmptyQuestionTextError(DraftValidationError):
    """Raised when generated question text is empty or blank."""

    def __init__(
        self,
        message_safe: str = "El enunciado de la pregunta no puede estar vacío.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EMPTY_QUESTION_TEXT",
            status_code=422,
            details=details,
        )


class InvalidOptionsCountError(DraftValidationError):
    """Raised when options count is outside permitted range for question type."""

    def __init__(
        self,
        message_safe: str = "El número de alternativas no está permitido para el tipo de pregunta.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_OPTIONS_COUNT",
            status_code=422,
            details=details,
        )


class InvalidCorrectOptionsCountError(DraftValidationError):
    """Raised when single_choice does not have exactly one correct option."""

    def __init__(
        self,
        message_safe: str = "Las preguntas de opción única deben tener exactamente una respuesta correcta.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_CORRECT_OPTIONS_COUNT",
            status_code=422,
            details=details,
        )


class DuplicateOptionsError(DraftValidationError):
    """Raised when duplicate options exist after normalization."""

    def __init__(
        self,
        message_safe: str = "Se detectaron alternativas duplicadas en la pregunta.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="DUPLICATE_OPTIONS",
            status_code=422,
            details=details,
        )


class EmptyOptionTextError(DraftValidationError):
    """Raised when an option has empty or whitespace-only text."""

    def __init__(
        self,
        message_safe: str = "El texto de una alternativa o distractor no puede estar vacío.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EMPTY_OPTION_TEXT",
            status_code=422,
            details=details,
        )


class EmptyExplanationError(DraftValidationError):
    """Raised when explanation text is empty or blank."""

    def __init__(
        self,
        message_safe: str = "La explicación pedagógica de la pregunta no puede estar vacía.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EMPTY_EXPLANATION",
            status_code=422,
            details=details,
        )


class InvalidSourceReferenceError(DraftValidationError):
    """Raised when source reference page/slide index does not exist in input document."""

    def __init__(
        self,
        message_safe: str = "La referencia documental no pertenece a una página o diapositiva válida del documento.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_SOURCE_REFERENCE",
            status_code=422,
            details=details,
        )


class SnippetNotFoundError(DraftValidationError):
    """Raised when cited snippet does not exist in the referenced document unit."""

    def __init__(
        self,
        message_safe: str = "El fragmento citado de la referencia no existe en el texto del documento fuente.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="SNIPPET_NOT_FOUND",
            status_code=422,
            details=details,
        )


class UnauthorizedFieldsError(DraftValidationError):
    """Raised when provider output contains unauthorized or unrecognized fields."""

    def __init__(
        self,
        message_safe: str = "La salida generada contiene campos no autorizados.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="UNAUTHORIZED_FIELDS",
            status_code=422,
            details=details,
        )


class InvalidDifficultyError(DraftValidationError):
    """Raised when numeric difficulty prior is outside [0.0, 1.0]."""

    def __init__(
        self,
        message_safe: str = "La dificultad psicométrica debe ser un valor entre 0.0 y 1.0.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="INVALID_DIFFICULTY",
            status_code=422,
            details=details,
        )


class UnprocessedHtmlError(DraftValidationError):
    """Raised when question content contains raw, unprocessed HTML tags or scripts."""

    def __init__(
        self,
        message_safe: str = "El contenido de la pregunta no puede contener etiquetas HTML sin procesar.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="UNPROCESSED_HTML_DETECTED",
            status_code=422,
            details=details,
        )


# ==============================================================================
# Draft Repository & Concurrency Violations
# ==============================================================================


class DraftRepositoryError(ContentGenerationError):
    """Base class for draft persistence and query failures."""

    def __init__(
        self,
        message_safe: str = "Error al persistir o recuperar los borradores de preguntas.",
        code: str = "DRAFT_REPOSITORY_ERROR",
        status_code: int = 500,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe, code=code, status_code=status_code, details=details
        )


class EmptyDraftsError(DraftRepositoryError):
    """Raised when attempting to persist an empty list of question drafts."""

    def __init__(
        self,
        message_safe: str = "No se pueden persistir cero borradores para el trabajo de generación.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="EMPTY_DRAFTS_PERSISTENCE",
            status_code=422,
            details=details,
        )


class DraftAlreadyReviewedError(DraftRepositoryError):
    """Raised when attempting to overwrite drafts that have already been reviewed by a teacher."""

    def __init__(
        self,
        message_safe: str = "No se pueden modificar borradores que ya han sido editados o aprobados por un docente.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="DRAFT_ALREADY_REVIEWED",
            status_code=409,
            details=details,
        )


class DraftNotFoundError(ContentGenerationError):
    """Raised when question draft does not exist or does not belong to the requesting tenant."""

    def __init__(
        self,
        message_safe: str = "El borrador de pregunta solicitado no existe o no pertenece a su institución.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="DRAFT_NOT_FOUND",
            status_code=404,
            details=details,
        )


class ConcurrencyConflictError(ContentGenerationError):
    """Raised when an update conflicts with concurrent modifications (optimistic concurrency)."""

    def __init__(
        self,
        message_safe: str = "Conflicto de concurrencia: el recurso fue modificado por otro usuario desde su última lectura.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="CONCURRENCY_CONFLICT",
            status_code=409,
            details=details,
        )


class KcAssignmentRequiredError(ContentGenerationError):
    """Raised when attempting to approve a question draft without an assigned Knowledge Component."""

    def __init__(
        self,
        message_safe: str = "El borrador no tiene un Componente de Conocimiento asignado. Por favor asigne un Knowledge Component antes de aprobar.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="KC_ASSIGNMENT_REQUIRED",
            status_code=422,
            details=details,
        )


class KnowledgeComponentNotFoundError(ContentGenerationError):
    """Raised when the specified Knowledge Component is not found in the tenant."""

    def __init__(
        self,
        message_safe: str = "El Componente de Conocimiento especificado no existe en su institución.",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message_safe=message_safe,
            code="KNOWLEDGE_COMPONENT_NOT_FOUND",
            status_code=404,
            details=details,
        )
