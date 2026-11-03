# Contratos de API Formales (Especificación REST y JSON Schema)

## 1. Visión General de la API

La API del sistema se estructura bajo los principios de **RESTful API** y utiliza esquemas basados en **OpenAPI 3.1.0** y **JSON Schema Draft 2020-12**.

### Convenciones Generales:
- **Base URL:** `/api/v1`
- **Autenticación:** Cabecera estándar HTTP `Authorization: Bearer <supabase_jwt>`.
- **Idempotencia:** Cabecera obligatoria `X-Idempotency-Key: <uuid-v4>` en todas las operaciones que persisten eventos de interacción (`POST /api/v1/diagnostic/answers`, `POST /api/v1/learning/attempts/{attempt_id}/answers`).
- **Formato de Respuestas de Error:** Cumplimiento estricto del estándar **RFC 7807 (Problem Details for HTTP APIs)** con Content-Type `application/problem+json`.

---

## 2. Endpoints y Contratos

### 2.1 Envío y Evaluación de Respuestas

#### Rutas Disponibles:
- `POST /api/v1/diagnostic/answers` (Envío estándar de respuesta a reactivo diagnóstico/formativo)
- `POST /api/v1/learning/attempts/{attempt_id}/answers` (Envío anclado al intento en la ruta)

#### Cabeceras HTTP Requeridas:
- `Authorization: Bearer <jwt>` (Obligatorio)
- `X-Idempotency-Key: <uuid-v4>` (Obligatorio)
- `Content-Type: application/json`

#### Esquema de Petición (Request JSON Schema):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SubmitAnswerRequest",
  "description": "Cuerpo de solicitud para registrar la respuesta de un estudiante",
  "type": "object",
  "required": [
    "question_id",
    "selected_option_id",
    "response_time_seconds"
  ],
  "properties": {
    "attempt_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID del intento en quiz_attempts (obligatorio si no está en la ruta)"
    },
    "question_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID de la pregunta respondida"
    },
    "selected_option_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID de la alternativa seleccionada por el estudiante"
    },
    "response_time_seconds": {
      "type": "number",
      "minimum": 0.1,
      "maximum": 600.0,
      "description": "Tiempo cronometrado de respuesta en segundos"
    },
    "idempotency_key": {
      "type": "string",
      "format": "uuid",
      "description": "UUID de idempotencia (espejo de la cabecera X-Idempotency-Key)"
    }
  },
  "additionalProperties": false
}
```

#### Esquema de Respuesta Exitosa (201 Created):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "SubmitAnswerResponse",
  "type": "object",
  "required": [
    "event_id",
    "is_correct",
    "feedback",
    "next_question_index",
    "attempt_completed"
  ],
  "properties": {
    "event_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID del evento inmutable persistido en answer_events"
    },
    "is_correct": {
      "type": "boolean",
      "description": "Resultado de la evaluación formativa"
    },
    "feedback": {
      "type": "object",
      "required": ["title", "explanation"],
      "properties": {
        "title": { "type": "string", "example": "¡Respuesta Correcta!" },
        "explanation": { "type": "string", "example": "La fotosíntesis convierte energía lumínica en glucosa en los cloroplastos." }
      },
      "additionalProperties": false
    },
    "next_question_index": {
      "type": ["integer", "null"],
      "minimum": 1,
      "description": "Índice de la siguiente pregunta de la actividad, o null si ha concluido"
    },
    "attempt_completed": {
      "type": "boolean",
      "description": "Indica si el intento de la actividad ha culminado"
    },
    "current_score": {
      "type": ["number", "null"],
      "minimum": 0.0,
      "maximum": 100.0,
      "description": "Puntaje acumulado calculado (0 a 100)"
    }
  },
  "additionalProperties": false
}
```

---

### 2.2 Inferencia Predictiva de Retención y Riesgo

#### Rutas Disponibles:
- `POST /api/v1/ml/predict-risk` (Predicción multihorizonte con explicabilidad SHAP)
- `POST /api/v1/predictions/retention` (Ruta alternativa homologada)

#### Cabeceras HTTP Requeridas:
- `Authorization: Bearer <jwt>`
- `Content-Type: application/json`

#### Esquema de Petición (Request JSON Schema):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PredictRiskRequest",
  "type": "object",
  "required": [
    "student_id",
    "knowledge_component_id"
  ],
  "properties": {
    "student_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID del perfil del estudiante"
    },
    "knowledge_component_id": {
      "type": "string",
      "format": "uuid",
      "description": "UUID del Knowledge Component objetivo a modelar"
    },
    "horizons_hours": {
      "type": "array",
      "items": { "type": "integer", "minimum": 1 },
      "default": [24, 72, 168],
      "description": "Horizontes de evaluación temporal en horas (24h, 72h, 168h)"
    },
    "include_shap_values": {
      "type": "boolean",
      "default": false,
      "description": "Solicitar cálculo de importancia local de características SHAP"
    }
  },
  "additionalProperties": false
}
```

#### Esquema de Respuesta Exitosa (200 OK - Inferencia Válida o Fallback):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "PredictRiskResponse",
  "type": "object",
  "required": [
    "prediction_status",
    "student_id",
    "knowledge_component_id",
    "predictions"
  ],
  "properties": {
    "prediction_status": {
      "type": "string",
      "enum": ["valid", "insufficient_history", "degraded_fallback"],
      "description": "Estado del proceso predictivo"
    },
    "student_id": {
      "type": "string",
      "format": "uuid"
    },
    "knowledge_component_id": {
      "type": "string",
      "format": "uuid"
    },
    "model": {
      "type": "object",
      "properties": {
        "name": { "type": "string", "example": "DAS3H" },
        "version": { "type": "string", "example": "1.0.0" }
      }
    },
    "predictions": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "horizon_hours",
          "recall_probability",
          "estimated_risk",
          "risk_level"
        ],
        "properties": {
          "horizon_hours": {
            "type": "integer",
            "minimum": 1,
            "description": "Horizonte temporal proyectado en horas"
          },
          "prediction_horizon_hours": {
            "type": "integer",
            "minimum": 1,
            "description": "Alias explícito del horizonte proyectado"
          },
          "recall_probability": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Probabilidad estimada de recuerdo P(R=1 | h)"
          },
          "predicted_recall_probability": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Alias explícito de la probabilidad estimada"
          },
          "estimated_risk": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Nivel de riesgo complementario (1.0 - recall_probability)"
          },
          "risk_level": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "description": "Categorización pedagógica del riesgo"
          }
        },
        "additionalProperties": false
      }
    },
    "feature_importance": {
      "type": ["object", "null"],
      "additionalProperties": { "type": "number" },
      "description": "Atribuciones de importancia SHAP para las características más influyentes"
    },
    "input_event_cutoff": {
      "type": "string",
      "format": "date-time",
      "description": "Marca de tiempo del último evento temporal considerado (prevención de leakage)"
    },
    "reason": {
      "type": ["string", "null"],
      "description": "Detalle explicativo si el estado es insufficient_history o degraded_fallback"
    },
    "created_at": {
      "type": "string",
      "format": "date-time"
    }
  },
  "additionalProperties": false
}
```

---

### 2.3 Recomendaciones Pedagógicas Adaptativas

#### Rutas Disponibles:
- `GET /api/v1/recommendations/{student_id}` (Consulta de recomendaciones activas del estudiante)
- `POST /api/v1/recommendations/generate` (Disparo y generación bajo demanda de recomendación)

#### Parámetros de Consulta (Query Parameters en GET):
- `risk_threshold`: float (Opcional, default: `0.65`)
- `limit`: integer (Opcional, min: `1`, max: `20`, default: `5`)
- `status`: string (Opcional, enum: `["pending", "delivered", "completed", "all"]`, default: `"pending"`)

#### Esquema de Respuesta Exitosa (200 OK):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "GetRecommendationsResponse",
  "type": "object",
  "required": [
    "student_id",
    "total_recommendations",
    "recommendations"
  ],
  "properties": {
    "student_id": {
      "type": "string",
      "format": "uuid"
    },
    "total_recommendations": {
      "type": "integer",
      "minimum": 0
    },
    "recommendations": {
      "type": "array",
      "items": {
        "type": "object",
        "required": [
          "id",
          "knowledge_component_id",
          "knowledge_component_name",
          "microcontent",
          "risk_score",
          "selection_method",
          "decision_reason",
          "status",
          "created_at"
        ],
        "properties": {
          "id": {
            "type": "string",
            "format": "uuid"
          },
          "knowledge_component_id": {
            "type": "string",
            "format": "uuid"
          },
          "knowledge_component_name": {
            "type": "string"
          },
          "microcontent": {
            "type": "object",
            "required": [
              "id",
              "title",
              "content_type",
              "estimated_duration_seconds"
            ],
            "properties": {
              "id": { "type": "string", "format": "uuid" },
              "title": { "type": "string" },
              "content_type": {
                "type": "string",
                "enum": ["text_summary", "infographic_card", "concept_map"]
              },
              "estimated_duration_seconds": { "type": "integer" }
            },
            "additionalProperties": false
          },
          "risk_score": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0
          },
          "selection_method": {
            "type": "string",
            "enum": ["predictive_model", "rule_based_fallback", "teacher_assigned"]
          },
          "decision_reason": {
            "type": "string",
            "description": "Justificación pedagógica transparente del algoritmo"
          },
          "review_activity_id": {
            "type": ["string", "null"],
            "format": "uuid",
            "description": "UUID de la actividad de práctica formativa programada"
          },
          "status": {
            "type": "string",
            "enum": ["pending", "delivered", "completed", "dismissed"]
          },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        },
        "additionalProperties": false
      }
    }
  },
  "additionalProperties": false
}
```

---

### 2.4 Mitigación de Arranque en Frío (Warmup Ping)

#### Ruta:
- `POST /api/v1/health/warmup`

#### Esquema de Respuesta (200 OK):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "WarmupResponse",
  "type": "object",
  "required": ["status", "warmed", "models_loaded", "timestamp"],
  "properties": {
    "status": { "type": "string", "example": "healthy" },
    "warmed": { "type": "boolean", "example": true },
    "models_loaded": {
      "type": "array",
      "items": { "type": "string" },
      "example": ["DAS3H", "BKT"]
    },
    "timestamp": { "type": "string", "format": "date-time" }
  },
  "additionalProperties": false
}
```

---

### 2.5 Modelo Estandarizado de Errores (RFC 7807 Problem Details)

Todos los códigos de error HTTP (400, 401, 403, 404, 409, 422, 500, 503) retornan una carga útil estructurada conforme a RFC 7807:

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ProblemDetails",
  "type": "object",
  "required": ["type", "title", "status", "detail", "code"],
  "properties": {
    "type": {
      "type": "string",
      "format": "uri",
      "example": "https://api.plataformamicro.edu.pe/errors/duplicate-idempotency-key"
    },
    "title": {
      "type": "string",
      "example": "Conflicto de Idempotencia"
    },
    "status": {
      "type": "integer",
      "example": 409
    },
    "detail": {
      "type": "string",
      "example": "La clave de idempotencia suministrada ya fue procesada anteriormente."
    },
    "instance": {
      "type": "string",
      "example": "/api/v1/diagnostic/answers"
    },
    "code": {
      "type": "string",
      "example": "DUPLICATE_IDEMPOTENCY_KEY"
    },
    "errors": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "field": { "type": "string", "example": "response_time_seconds" },
          "message": { "type": "string", "example": "El tiempo de respuesta debe ser mayor a 0.1 segundos." }
        }
      }
    }
  },
  "additionalProperties": false
}
```

---

### 2.6 Ingesta Documental y Generación Asistida de Preguntas (Docente)

#### 2.6.1 Crear Trabajo de Generación
- **Ruta:** `POST /api/v1/content-generation/jobs`
- **Rol Autorizado:** `teacher`, `admin`, `super_admin`
- **Cabeceras:** `Authorization: Bearer <jwt>`, `Content-Type: application/json`
- **Seguridad:** El backend deriva `tenant_id` y `created_by` del JWT (`auth.uid()`). El docente debe haber subido previamente el archivo al bucket privado `teacher-materials`.

##### Esquema de Petición (Request):
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "CreateGenerationJobRequest",
  "type": "object",
  "required": ["storage_path", "original_filename", "mime_type", "file_size_bytes", "file_checksum"],
  "properties": {
    "course_id": { "type": "string", "format": "uuid" },
    "unit_id": { "type": "string", "format": "uuid" },
    "storage_bucket": { "type": "string", "default": "teacher-materials" },
    "storage_path": { "type": "string" },
    "original_filename": { "type": "string" },
    "mime_type": {
      "type": "string",
      "enum": [
        "application/pdf",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
      ]
    },
    "file_size_bytes": { "type": "integer", "minimum": 1, "maximum": 31457280 },
    "file_checksum": { "type": "string" }
  },
  "additionalProperties": false
}
```

##### Esquema de Respuesta (202 Accepted):
Retorna objeto `GenerationJobResponse` con estado `'queued'`, identificador de trabajo `job_id`, proveedor y modelo configurados.

#### 2.6.2 Consultar y Aprobar Borradores (Human-in-the-Loop)
- **Consultar Borradores:** `GET /api/v1/content-generation/jobs/{job_id}/drafts`
- **Editar Borrador:** `PATCH /api/v1/content-generation/drafts/{draft_id}`
- **Aprobar Borradores:** `POST /api/v1/content-generation/jobs/{job_id}/approve`
  - Valida que cada borrador tenga un `knowledge_component_id` asignado y exactamente una opción correcta.
  - Inserta transaccionalmente en `questions` y `question_options`, vinculando `approved_question_id`.
- **Rechazar Borrador:** `POST /api/v1/content-generation/drafts/{draft_id}/reject`

---

### 2.7 Recomendaciones y Notificaciones In-App para Estudiantes

#### Regla de Seguridad Antisuplantación:
Las peticiones del estudiante resuelven su identidad **exclusivamente desde el token JWT validado (`auth.uid()`)**. Queda terminantemente prohibido exigir o aceptar `student_id` enviado en el cuerpo o la URL para operaciones del propio estudiante.

#### 2.7.1 Consulta de Recomendaciones del Estudiante Autenticado
- **Ruta:** `GET /api/v1/students/me/recommendations`
- **Rol Autorizado:** `student`
- **Cabeceras:** `Authorization: Bearer <jwt>`
- **Respuesta (200 OK):** Retorna `GetRecommendationsResponse` con los repasos y microcontenidos asignados al estudiante de la sesión.

#### 2.7.2 Consulta y Gestión de Avisos In-App
- **Ruta:** `GET /api/v1/students/me/notifications?unread_only=true`
- **Rol Autorizado:** `student`
- **Respuesta (200 OK):**
```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "NotificationListResponse",
  "type": "object",
  "required": ["notifications", "unread_count"],
  "properties": {
    "notifications": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "notification_type", "title", "body", "target_path", "created_at", "is_read"],
        "properties": {
          "id": { "type": "string", "format": "uuid" },
          "notification_type": { "type": "string", "enum": ["review_reminder", "new_assignment", "system_notice"] },
          "title": { "type": "string" },
          "body": { "type": "string" },
          "target_path": { "type": "string" },
          "review_assignment_id": { "type": ["string", "null"], "format": "uuid" },
          "is_read": { "type": "boolean" },
          "read_at": { "type": ["string", "null"], "format": "date-time" },
          "created_at": { "type": "string", "format": "date-time" }
        }
      }
    },
    "unread_count": { "type": "integer", "minimum": 0 }
  }
}
```
- **Marcar Leído:** `PATCH /api/v1/students/me/notifications/{id}/read` (Retorna `NotificationItem` actualizado con `read_at = now()`).

---

### 2.8 Modelos Pydantic v2 Propuestos para Ingesta y Notificaciones (`services/ml-api`)

Los siguientes modelos Pydantic v2 reflejan de manera estricta los esquemas de OpenAPI 3.1.0 y deben ubicarse en `services/ml-api/app/schemas/content_generation.py` y `services/ml-api/app/schemas/notifications.py`:

```python
"""Esquemas Pydantic v2 para Ingesta de Documentos y Avisos In-App."""

from datetime import datetime
from enum import Enum
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field


class GenerationJobStatus(str, Enum):
    QUEUED = "queued"
    PROCESSING = "processing"
    REVIEW_REQUIRED = "review_required"
    APPROVED = "approved"
    REJECTED = "rejected"
    FAILED = "failed"


class DraftStatus(str, Enum):
    DRAFT = "draft"
    EDITED = "edited"
    APPROVED = "approved"
    REJECTED = "rejected"


class NotificationType(str, Enum):
    REVIEW_REMINDER = "review_reminder"
    NEW_ASSIGNMENT = "new_assignment"
    SYSTEM_NOTICE = "system_notice"


class CreateGenerationJobRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    course_id: Optional[UUID] = None
    unit_id: Optional[UUID] = None
    storage_bucket: str = "teacher-materials"
    storage_path: str
    original_filename: str
    mime_type: str = Field(
        ...,
        pattern=r"^(application/pdf|application/vnd\.openxmlformats-officedocument\.presentationml\.presentation)$",
    )
    file_size_bytes: int = Field(..., ge=1, le=31457280)
    file_checksum: str


class GenerationJobResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    job_id: UUID
    status: GenerationJobStatus
    storage_path: str
    original_filename: str
    provider: str
    model_id: str
    prompt_version: str
    created_at: datetime
    error_code: Optional[str] = None
    error_message_safe: Optional[str] = None


class QuestionDraftOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str
    is_correct: bool


class QuestionDraftSourceReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str = Field(..., pattern=r"^(page|slide)$")
    index: int = Field(..., ge=1)
    snippet: Optional[str] = None


class QuestionDraftItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    generation_job_id: UUID
    knowledge_component_id: Optional[UUID] = None
    suggested_kc_name: str
    question_text: str
    explanation: str
    options: List[QuestionDraftOption] = Field(..., min_length=2, max_length=4)
    suggested_difficulty: float = Field(0.5, ge=0.0, le=1.0)
    suggested_bloom_level: str = "understand"
    source_references: List[QuestionDraftSourceReference] = Field(default_factory=list)
    status: DraftStatus
    approved_question_id: Optional[UUID] = None
    created_at: datetime


class UpdateQuestionDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    knowledge_component_id: Optional[UUID] = None
    question_text: Optional[str] = None
    explanation: Optional[str] = None
    options: Optional[List[QuestionDraftOption]] = None
    suggested_difficulty: Optional[float] = Field(None, ge=0.0, le=1.0)
    suggested_bloom_level: Optional[str] = None


class BatchApproveDraftsRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    draft_ids: List[UUID] = Field(..., min_length=1)


class BatchApproveDraftsResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    approved_count: int
    published_question_ids: List[UUID]


class RejectDraftRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    rejection_reason: Optional[str] = None


class NotificationItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    notification_type: NotificationType
    title: str
    body: str
    target_path: str
    review_assignment_id: Optional[UUID] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationListResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    notifications: List[NotificationItem]
    unread_count: int = Field(..., ge=0)
```

