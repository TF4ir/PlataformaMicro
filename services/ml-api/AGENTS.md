# AGENTS.md — Subsisstema Predictivo y Adaptativo (`services/ml-api/`)

## 1. Misión y Alcance
Microservicio HTTP asíncrono de alto rendimiento desarrollado en FastAPI (Python 3.11+). Es responsable del cálculo de características temporales, inferencia de probabilidad de recuperación ($P(R=1)$) y ejecución de la política de recomendación adaptativa.

## 2. Arquitectura de Módulos (Clean / Hexagonal)
- `core/`: Configuración global (`pydantic-settings`), verificación de JWT de Supabase, CORS, middleware de telemetría y warmup.
- `api/v1/`: Controladores de endpoints (`/answers`, `/predictions`, `/recommendations`, `/health`).
- `schemas/`: Modelos Pydantic v2 de entrada y salida con tipado estricto sincronizados con OpenAPI.
- `services/`: Orquestadores de casos de uso (`LearningService`, `PredictionService`, `RecommendationService`).
- `prediction/`: Cargadores de artefactos congelados, extractores de secuencias temporales e interfaces `BaseRetentionModel`.
- `adaptation/`: Motor de decisiones pedagógicas, umbrales configurables ($\tau$) y fallback basado en reglas.
- `repositories/`: Conexión de lectura/escritura con Supabase PostgreSQL vía `asyncpg` o `supabase-py`.

## 3. Límites y Restricciones Absolutas
1. **Fuente de Verdad Única:** Supabase es la única fuente de persistencia. FastAPI no gestiona migraciones DDL ni posee base de datos local.
2. **Idempotencia Obligatoria:** Todo endpoint que persista intentos o respuestas (`/api/v1/learning/attempts/{id}/answers`) debe exigir y validar `idempotency_key` (UUID).
3. **Manejo de Historia Insuficiente:** Si un estudiante tiene menos intentos que el umbral mínimo para un Knowledge Component, el endpoint predictivo DEBE responder `prediction_status: "insufficient_history"` sin error 500, permitiendo que la política active `rule_based_fallback`.
4. **Aislamiento de Entrenamiento:** Prohibido ejecutar rutinas de optimización, EDA o re-entrenamiento masivo dentro del proceso web de FastAPI. Solo se cargan modelos congelados.
5. **Tipado Estricto:** 100% tipado con validación Pydantic v2 y MyPy en modo estricto. Prohibido el uso de `Any` no documentado.
6. **Mitigación de Cold-Start en blitz.cloud:** Exponer endpoint `POST /api/v1/health/warmup` y asegurar arranque ligero del contenedor.
