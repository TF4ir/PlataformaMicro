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
