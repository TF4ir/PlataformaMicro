# ML-API: Microservicio Predictivo y Motor de Adaptación Pedagógica

Microservicio backend desarrollado en Python 3.11+ y FastAPI para la predicción probabilística de la curva de retención/olvido estudiantil y la orquestación de políticas de repaso adaptativo.

## Arquitectura Hexagonal y Modular
- `app/core/`: Configuración del entorno (`BaseSettings`), seguridad y validación criptográfica de Supabase JWTs.
- `app/api/v1/`: Rutas HTTP (`/learning`, `/predictions`, `/recommendations`, `/health`).
- `app/schemas/`: Esquemas tipados Pydantic v2 sincronizados con los contratos OpenAPI.
- `app/services/`: Casos de uso de negocio (orquestación de flujos de aprendizaje y cálculo de políticas).
- `app/repositories/`: Clientes y consultas de datos sobre la base de datos Supabase.
- `app/prediction/`: Interfaces abstractas de modelos (`BaseRetentionModel`), cargador de artefactos y extractor temporal.
- `app/adaptation/`: Motor de decisiones pedagógicas, umbrales de retención $\tau$ y fallback determinista.

## Mitigación de Arranque en Frío (blitz.cloud)
- Endpoint dedicado `POST /api/v1/health/warmup` para pre-calentar la instancia 10 minutos antes del inicio de clases.
- Política de degradación elegante: ante timeout (> 5 s) o respuesta `insufficient_history`, se activa `rule_based_fallback`.
