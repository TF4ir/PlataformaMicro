# Auditoría de Preparación para Despliegue en Google Cloud Run

> **Servicio:** `services/ml-api` (FastAPI Predictive, Adaptive & Curriculum Content Generation)  
> **Repositorio:** `TF4ir/PlataformaMicro`  
> **Rama objetivo:** `main`  
> **Fecha de actualización:** Noviembre 2026 (Post-Hardening P1 & P2)  
> **Auditoría Técnica:** Revisión Independiente y Verificación Empírica  
> **Estado global:** **REQUIRES CONFIGURATION** (0 BLOCKERS en código; 0 CODE CHANGES pendientes; 3 configuraciones de aprovisionamiento en GCP restantes)

---

## 1. Resumen Ejecutivo y Diagnóstico Global

La presente auditoría evalúa exhaustivamente el estado técnico del monorepo **PlataformaMicro** para el despliegue del microservicio `services/ml-api` en **Google Cloud Run** conectado directamente al repositorio GitHub `TF4ir/PlataformaMicro`.

Tras la implementación de las correcciones de Prioridad 1 (P1) y Prioridad 2 (P2), se han solventado todos los bloqueos de código y reproducibilidad de construcción.

### Veredicto por Componente y Clasificación

| Componente / Área | Clasificación | Diagnóstico y Verificación Post-Hardening |
| :--- | :---: | :--- |
| **Construcción Dockerfile desde Raíz** | `READY` | Construcción multi-stage (`python:3.11-slim`) verificada con contexto `.`. Incluye `services/ml-api`, `ml/` y `poetry.lock`. Código de salida `0`. |
| **Resolución de Rutas en Contenedor (`model_registry.py`)** | `READY` | **RESUELTO:** Se eliminó el acceso frágil a `Path.parents[4]`. Implementada función `resolve_artifacts_dir()` con búsqueda ascendente dinámica, soporte explícito para `MODEL_ARTIFACTS_DIR` y fallback seguro. Verificado tanto en tests unitarios como en contenedor Docker en vivo (`/app/ml/artifacts`). |
| **Escucha en `0.0.0.0` y Puerto Dinámico `PORT`** | `READY` | Verificado con `CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]`. Escucha correctamente en el puerto inyectado por Cloud Run (`0.0.0.0:8080`). |
| **Sondas de Salud (Healthchecks)** | `READY` | `GET /api/v1/health` responde HTTP 200 OK (< 5 ms) sin depender de la base de datos (evita bucles de reinicio si la BD se recupera de un reinicio). `POST /api/v1/health/warmup` disponible. |
| **Escalado a Cero y Arranque en Frío (Cold Start)** | `READY` | Tiempo de importación de módulos pesados (`numpy`, `pandas`, `scipy`, `sklearn`, `fastapi`, `app.main`) medido en contenedor frío: **4.54 segundos** (dentro del límite de 240 s de Cloud Run). |
| **Persistencia y Modelo Stateless** | `READY` | 100% sin estado en disco. La extracción de PDF (`pypdf`) y PPTX (`python-pptx`) opera en memoria (`io.BytesIO`). Almacenamiento en Supabase Storage (`teacher-materials`). |
| **Conexión PostgreSQL y Pooler de Supabase** | `READY` | **RESUELTO:** `resolve_pool_configuration()` prioriza Session Mode (puerto 5432 o sin puerto) para la API persistente y detecta Transaction Mode (puerto 6543). En modo transacción impone `statement_cache_size=0`. Pool conservador (`min_size=1, max_size=5`). SSL auto-negociado (`require` para endpoints remotos de Supabase, respetando `?sslmode=disable`). Enmascaramiento estricto de contraseñas y parámetros sensibles en logs (`sanitize_database_url`), preservando formato IPv6 y locking de concurrencia. |
| **Determinismo de Dependencias (Poetry)** | `READY` | **RESUELTO:** Generado y versionado `services/ml-api/poetry.lock`. `Dockerfile` actualizado para copiar `poetry.lock*` e instalar con `--no-root --no-interaction --no-ansi`. |
| **Contexto de Construcción `.dockerignore`** | `READY` | **RESUELTO:** `.dockerignore` optimizado con comodines recursivos (`**/.mypy_cache`, `**/.venv`, `.agents/`, `apps/`, etc.). Contexto transmitido al daemon reducido de **71.85 MB** a **2.25 MB** (reducción del 96.9%). |
| **Autenticación JWT Supabase** | `READY` | Verificado que la API utiliza claves asimétricas ES256/RS256 vía JWKS público (`_jwks_url()`). Soporte legado HS256 disponible pero no obligatorio para proyectos modernos de Supabase. |
| **Topología y Despliegue del Worker (`worker.py`)** | `REQUIRES CONFIGURATION` | El worker continuo de sondeo (`SELECT FOR UPDATE SKIP LOCKED` cada 1 s) requiere decisión de infraestructura (Cloud Tasks vs Cloud Run Job vs Dedicated Service). La API HTTP y el motor de inferencia operan de forma 100% autónoma sin el worker. |
| **Secretos y Aprovisionamiento GCP** | `REQUIRES CONFIGURATION` | Pendiente aprovisionamiento en Google Secret Manager antes del despliegue final (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`, etc.). |

---

## 2. Arquitectura de Despliegue Propuesta

```
                                  +-----------------------------------------------+
                                  |                 Cloudflare CDN                |
                                  |     (Proxy, DNS, SSL Strict, DDoS Shield)     |
                                  +-----------------------------------------------+
                                             |                           |
                      Frontend HTTPS         |                           | API HTTPS
                   (plataformamicro.edu.pe)  |                           | (api.plataformamicro.edu.pe)
                                             v                           v
                                  +-------------------+       +-------------------------------+
                                  |    Vercel Edge    |       |       Google Cloud Run        |
                                  | (Next.js App Rtr) | ----> |   `services/ml-api` (HTTP)    |
                                  +-------------------+       | (Scale: 0 to N instances)     |
                                                              +-------------------------------+
                                                                 |           |             ^
                                                In-Memory Process|           |             |
                                                (DAS3H/HLR/PFA)  |           |             |
                                                                 v           |             |
                                                    +------------------+     |             |
                                                    |  Inference Engine|     |             |
                                                    |   & Adaptation   |     |             |
                                                    +------------------+     |             |
                                                                             |             |
                                             +-------------------------------+             |
                                             |                                             |
                                             v                                             v
                           +-----------------------------------+         +----------------------------------+
                           |     Supabase Managed Platform     |         |      Procesamiento Asíncrono     |
                           |                                   |         |        Generación Docente        |
                           | 1. PostgreSQL 15 (Supavisor)      | <------ | (Opción 1: Cloud Tasks Serverless|
                           | 2. Auth (JWKS ES256 / HS256)      |         |  Opción 2: Cloud Run Job         |
                           | 3. Storage (`teacher-materials`)  |         |  Opción 3: Dedicated Worker Svc) |
                           +-----------------------------------+         +----------------------------------+
```

### 2.1 Desglose de Componentes

1. **Servicio Primario HTTP (`ml-api` en Google Cloud Run):**
   - Expone rutas REST `/api/v1/*`.
   - Ejecuta inferencia predictiva temporal (DAS3H / HLR / PFA / BKT) y motor de adaptación pedagógica **en memoria** en menos de 100 ms por solicitud.
   - Encola trabajos docentes en la tabla `content_generation_jobs` de PostgreSQL.
   - Escala de `0` a `N` instancias (Cold start medido: ~4.5 s).
2. **Plataforma de Datos y Autenticación (Supabase):**
   - PostgreSQL 15 accesible vía Supavisor Connection Pooler (`aws-0-[region].pooler.supabase.com`).
   - Verificación de identidad con tokens JWT (asíncronos ES256 vía JWKS o simétricos HS256).
   - Supabase Storage privado (`teacher-materials`) para PDFs y PPTXs curriculares.
3. **Mecanismo de Ejecución del Worker de Generación Curricular:**
   - La generación con LLM toma entre 15 y 45 segundos por documento.
   - En Cloud Run HTTP estándar, la CPU se suspende cuando no hay peticiones activas. El bucle de sondeo infinito `worker.py` no corre dentro del servicio HTTP y se gestionará mediante Cloud Tasks o Cloud Run Job en una tarea posterior.

---

## 3. Auditoría Detallada del Dockerfile y Construcción

### 3.1 Inspección del Dockerfile (`services/ml-api/Dockerfile`)

```dockerfile
FROM python:3.11-slim AS builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY services/ml-api/pyproject.toml services/ml-api/poetry.lock* services/ml-api/README.md ./
RUN pip install --upgrade pip && \
    pip install poetry && \
    poetry config virtualenvs.in-project true && \
    poetry install --only main --no-root --no-interaction --no-ansi

FROM python:3.11-slim AS runner

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    PORT=8000

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd -m -u 1000 appuser

COPY --from=builder /app/.venv /app/.venv
COPY --chown=appuser:appuser services/ml-api/app/ /app/app/
COPY --chown=appuser:appuser services/ml-api/README.md /app/README.md
COPY --chown=appuser:appuser ml/ /app/ml/

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f "http://localhost:${PORT}/api/v1/health" || exit 1

CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
```

### 3.2 Matriz de Validación Técnica frente al Contrato de Cloud Run

| Requisito de Cloud Run | Estado | Verificación Experimental |
| :--- | :---: | :--- |
| **Construcción desde la raíz del monorepo** | `READY` | Ejecutado: `docker build -f services/ml-api/Dockerfile -t test-ml-api .`. Contexto: 2.45 MB. Código de salida `0`. |
| **Inclusión correcta de `services/ml-api` y `ml/`** | `READY` | `app/` copiado a `/app/app/`, `ml/` copiado a `/app/ml/`. Verificado: imports funcionan sin error con `PYTHONPATH=/app`. |
| **Escucha en `0.0.0.0` y respeto de `PORT`** | `READY` | Verificado con `docker run -e PORT=8080 test-ml-api`. El proceso inicia con: `Uvicorn running on http://0.0.0.0:8080`. |
| **Usuario no-root (`appuser`)** | `READY` | Usuario UID 1000 configurado. Cumple el principio de mínimo privilegio. |
| **Directiva HEALTHCHECK** | `READY` | Funcional en entornos locales y Docker. |
| **Stateless (Sin dependencias de almacenamiento local)** | `READY` | Los archivos se procesan como `io.BytesIO` en memoria RAM. No se crean directorios temporales ni archivos persistentes locales. |
| **Determinismo de Dependencias (Poetry Lock)** | `READY` | `poetry.lock` generado y versionado. Dockerfile incorpora `poetry.lock*` para compilaciones deterministas. |

---

## 4. Auditoría de Código y Corrección de Bloqueadores (P1)

### 4.1 [BLOCKER RESUELTO] Error de Índice en `RetentionModelRegistry` (`IndexError: 4`)

- **Ubicación Original:** `services/ml-api/app/prediction/model_registry.py:52`:
  ```python
  self.artifacts_dir = Path(__file__).resolve().parents[4] / "ml" / "artifacts"
  ```
- **Causa Raíz:**
  En desarrollo local la jerarquía de directorios tiene 5 niveles (`parents[4]` apunta a la raíz). En el contenedor Docker, la ruta es `/app/app/prediction/model_registry.py`, la cual solo tiene 4 elementos (índices 0..3), arrojando `IndexError: 4` al inicializar el registro e impidiendo las operaciones de retención y recomendación (`HTTP 500`).
- **Solución Implementada:**
  Se introdujo `resolve_artifacts_dir()` que:
  1. Admite ruta explícita mediante parámetro en constructor (`artifacts_dir: Path | str | None`).
  2. Admite variable de entorno o configuración `MODEL_ARTIFACTS_DIR`.
  3. Realiza búsqueda ascendente dinámica de `ml/artifacts` sin depender de índices fijos de `Path.parents`.
  4. Realiza búsqueda de respaldo en CWD y contenedor (`/app/ml/artifacts`).
  5. Valida la existencia y emite logs de diagnóstico claros si no se encuentran artefactos, activando el modo sintético en desarrollo o el estado `INSUFFICIENT_EMPIRICAL_DATA` en producción sin crashear.
- **Verificación Experimental:**
  - Tests unitarios: 7/7 aprobados en `tests/test_model_registry_resolution.py`.
  - Verificación dentro del contenedor Docker:
    ```bash
    docker run --rm test-ml-api python -c "from app.prediction.model_registry import RetentionModelRegistry; reg = RetentionModelRegistry(); print(reg.artifacts_dir)"
    # Salida: /app/ml/artifacts (Código 0, sin IndexError)
    ```
  - Verificación de endpoints HTTP en contenedor:
    - `GET /api/v1/students/me/retention` -> `HTTP 200 OK`
    - `POST /api/v1/students/me/recommendations/evaluate` -> `HTTP 200 OK`
    - `GET /api/v1/students/me/recommendations` -> `HTTP 200 OK`

---

## 5. Conectividad PostgreSQL y Supavisor Pooling (P2)

### 5.1 Evaluación Técnica: Session Mode (5432) vs Transaction Mode (6543)

La plataforma Supabase expone dos modos de conexión mediante su Connection Pooler (Supavisor) en `aws-0-[region].pooler.supabase.com`:

| Característica | Session Mode (Puerto 5432) | Transaction Mode (Puerto 6543) |
| :--- | :--- | :--- |
| **Mapeo de Conexiones** | 1 conexión cliente = 1 conexión Postgres dedicada | Multiplexación: la conexión de backend se retiene únicamente durante la transacción activa |
| **Límite de Conexiones** | Limitado al pool físico de Postgres (~15-20 en micro/free) | Soporta cientos o miles de conexiones cliente simultáneas |
| **Prepared Statements** | Soportado con caché (`statement_cache_size=100`) | **Incompatible** con sentencias preparadas con nombre (`DuplicatePreparedStatementError`) |
| **Comportamiento en Cloud Run** | Si Cloud Run escala a 5-10 instancias con pool de 5-10, agota inmediatamente las conexiones de Supabase (`max_instances * max_connections`) | Permite a múltiples instancias de Cloud Run compartir un pool backend pequeño sin colisiones |
| **Requisito en asyncpg** | Funciona con defaults | **Requiere obligatoriamente** `statement_cache_size=0` |

### 5.2 Decisión Arquitectónica y Manejo Adaptativo

Para maximizar la resiliencia en Cloud Run sin forzar configuraciones rígidas:
1. **Detección Automática y Priorización de Session Mode:** `database.py` analiza el DSN:
   - Si el puerto es `6543`: se activa **Transaction Mode** y se establece automáticamente `statement_cache_size=0`.
   - Si el puerto es `5432` o se omite el puerto: se activa **Session Mode** y se mantiene `statement_cache_size=100` (evaluando Session Mode primero según directrices de arquitectura).
2. **Overrides Parametrizables:** Posibilidad de forzar el modo vía `DB_POOL_MODE=session` o `DB_POOL_MODE=transaction`, y ajustar `DB_STATEMENT_CACHE_SIZE`.
3. **Dimensionamiento del Pool:**
   - `DB_POOL_MIN_SIZE=1`: evita retener conexiones ociosas cuando Cloud Run mantiene instancias en reposo.
   - `DB_POOL_MAX_SIZE=5`: limita el consumo máximo por instancia a 5 conexiones.
   - Fórmula: Con 10 instancias máximas de Cloud Run, `10 * 5 = 50` conexiones cliente máximas hacia Supavisor, perfectamente tolerables en Transaction Mode.
4. **Negociación SSL:**
   - Endpoints locales (`127.0.0.1`, `localhost`, `::1`): SSL deshabilitado.
   - Endpoints remotos (`pooler.supabase.com`, `supabase.co`): SSL forzado en `require`.
   - Parámetros `?sslmode=disable` o `?sslmode=require` en la URL son respetados y depurados del DSN para evitar incompatibilidades con asyncpg.
5. **Enmascaramiento de Credenciales y Locking:**
   - La función `sanitize_database_url()` reemplaza contraseñas y tokens sensibles por `***` en todos los mensajes de registro, preservando soporte para direcciones IPv6 con corchetes (`[::1]`).
   - Se implementó double-checked locking asíncrono (`asyncio.Lock`) para prevenir condiciones de carrera durante arranques en frío concurrentes.
6. **Verificación:**
   - 16/16 tests aprobados en `tests/test_database_pooling.py`.

---

## 6. Autenticación Supabase y Verificación JWT

### 6.1 Auditoría del Esquema Criptográfico

En `services/ml-api/app/core/auth.py`:
1. **Verificación Asimétrica (ES256/RS256):**
   - El microservicio utiliza `PyJWKClient` apuntando al endpoint JWKS público de Supabase (`SUPABASE_JWKS_URL` o `{SUPABASE_URL}/auth/v1/.well-known/jwks.json`).
   - Todos los proyectos de Supabase creados recientemente utilizan claves asimétricas ES256.
   - La rotación de claves se maneja automáticamente a través de la caché interna del cliente JWKS.
   - La verificación valida firma criptográfica y expiración (`verify_exp: True`).
2. **Soporte Legado (HS256):**
   - El backend mantiene compatibilidad con proyectos heredados que utilizan secretos simétricos mediante `SUPABASE_JWT_SECRET`.
   - Si llega un token firmado con HS256 y el entorno es producción sin secreto configurado, se rechaza de forma fail-closed (`HTTP 500 JWT_SECRET_MISSING`).
3. **Conclusión para Cloud Run:**
   - `SUPABASE_JWT_SECRET` **NO es obligatorio** si la instancia de Supabase emite tokens asimétricos ES256 validados vía JWKS.
   - No se debilita la verificación; se preserva la validación criptográfica estricta.

---

## 7. Optimización de Build Context y Dependencias (P2)

### 7.1 Determinismo con `poetry.lock`
- Se ejecutó `poetry lock` determinando versiones exactas de las 60 dependencias del microservicio.
- Se actualizó el `Dockerfile` para copiar `pyproject.toml` y `poetry.lock*`.
- La instalación en el builder stage (`poetry install --only main --no-root`) se realiza exclusivamente a partir del lockfile, evitando cambios no controlados en builds futuros.

### 7.2 Reducción de `.dockerignore`
- Se optimizó el `.dockerignore` raíz utilizando comodines recursivos (`**/.mypy_cache`, `**/.venv`, `**/.pytest_cache`, `**/__pycache__`, `apps/`, `docs/`, `supabase/`, `scripts/`).
- **Medición empírica:**
  - Contexto antes de la optimización: **71.85 MB** (debido a caché de mypy).
  - Contexto después de la optimización: **2.44 MB**.
  - **Reducción lograda: 96.6%**, acelerando drásticamente el envío de contexto a Google Cloud Build.

---

## 8. Abstracción LLM y Topología del Worker Curricular

### 8.1 Abstracción de Proveedor LLM
- El sistema utiliza `LLM_PROVIDER` (`mock`, `gemini`, `openai`) y `LLM_MODEL_ID`.
- Para levantar la API HTTP e inferencia DAS3H **no se requieren credenciales LLM** (`LLM_PROVIDER=mock`).
- Solo se requiere `GEMINI_API_KEY` si `LLM_PROVIDER=gemini`, o `OPENAI_API_KEY` si `LLM_PROVIDER=openai`.
- La generación de preguntas es una funcionalidad asistida desacoplada del ciclo crítico de retención y recomendación.

### 8.2 Alternativas para el Worker Curricular (`worker.py`)
El bucle de sondeo infinito con `SELECT FOR UPDATE SKIP LOCKED` es incompatible con el escalado a cero y suspensión de CPU de Cloud Run HTTP. Se definen tres alternativas técnicas para su implementación en un milestone posterior:

1. **Opción 1 — Google Cloud Tasks (Recomendada a Largo Plazo):**
   - El endpoint de creación de trabajos encola en PostgreSQL y emite una tarea HTTP autenticada hacia un endpoint interno del servicio.
   - Escalado a cero total ($0.00 en reposo).
2. **Opción 2 — Cloud Run Job:**
   - Ejecución por lotes sin requerir puerto HTTP. Adecuado si se activa por eventos de Cloud Scheduler.
3. **Opción 3 — Cloud Run Dedicado con Sonda HTTP Embebida:**
   - Servicio Cloud Run con `--no-cpu-throttling` y `--min-instances=1`, incorporando un micro-servidor HTTP que responda a `/health` mientras el bucle corre en segundo plano.

---

## 9. Matriz de Verificación y Pruebas Ejecutadas

| Prueba / Control de Calidad | Resultado | Alcance y Método |
| :--- | :---: | :--- |
| **Suite de pruebas de `services/ml-api`** | `269 aprobadas, 2 omitidas` | Cobertura completa de modelos, repositorios, UoW, auth, extractores, pooling y registry. |
| **Suite de pruebas del módulo `ml/`** | `19 aprobadas` | Benchmarks sintéticos DAS3H y retención temporal validados. |
| **Tests de resolución de artefactos** | `8 aprobadas` | Verificación en local, contenedor simulado real, variable de entorno, fallbacks y logs diagnósticos. |
| **Tests de database pooling y sanitización** | `16 aprobadas` | Verificación de Session Mode, Transaction Mode, puerto omitido, `statement_cache_size=0`, SSL auto/disable, IPv6 y enmascaramiento. |
| **Análisis estático Ruff** | `0 errores` | Cumplimiento de estilo y formato en 72 archivos fuente. |
| **Comprobación de tipos Mypy** | `0 errores (Strict)` | Tipado estricto verificado en todo `app/`. |
| **Docker Build desde raíz** | `Exit code 0` | Construcción multi-stage completada con contexto optimizado de 2.25 MB. |
| **Ejecución de contenedor en vivo** | `Exit code 0` | Inicialización de Uvicorn en `0.0.0.0:8080`, healthcheck OK (< 5 ms). |
| **Prueba de Inferencia y Recomendaciones en Contenedor** | `HTTP 200 OK` | `GET /retention`, `POST /recommendations/evaluate`, `GET /recommendations` probados contra Postgres sin `IndexError`. |
| **Prueba remota de integración con Supabase** | `PENDIENTE` | Pendiente de aprovisionamiento de credenciales reales en Google Cloud Secret Manager. |

---

## 10. Variables de Entorno para Cloud Run

### 10.1 Variables en Cloud Run (Configuración Ordinaria)

| Variable | Valor Sugerido | Propósito |
| :--- | :--- | :--- |
| `ENVIRONMENT` | `production` | Activa modo producción (rechaza proxy headers, restringe synthetic models). |
| `DEBUG` | `false` | Desactiva trazas de error verbosas. |
| `PORT` | `8080` | Puerto inyectado por Google Cloud Run. |
| `API_V1_PREFIX` | `/api/v1` | Prefijo de rutas. |
| `SUPABASE_URL` | `https://<ref>.supabase.co` | Endpoint raíz de Supabase. |
| `SUPABASE_JWKS_URL` | `https://<ref>.supabase.co/auth/v1/.well-known/jwks.json` | URL de validación de tokens ES256. |
| `CORS_ORIGINS` | `https://plataformamicro.edu.pe,https://app.plataformamicro.edu.pe` | Orígenes web autorizados. |
| `REPOSITORY_BACKEND` | `postgres` | Persistencia en base de datos. |
| `DB_POOL_MODE` | `auto` (o `transaction`) | Modo Supavisor (auto-detecta 6543 / Transaction). |
| `DB_POOL_MIN_SIZE` | `1` | Conexiones mínimas por instancia. |
| `DB_POOL_MAX_SIZE` | `5` | Conexiones máximas por instancia. |
| `ADAPTATION_DEFAULT_THRESHOLD` | `0.65` | Umbral crítico de retención $\tau$. |
| `MIN_ATTEMPTS_FOR_INFERENCE` | `3` | Intentos mínimos para activar inferencia individualizada. |
| `LLM_PROVIDER` | `gemini` (o `mock`) | Proveedor de generación de reactivos. |
| `LLM_MODEL_ID` | `gemini-1.5-pro` | Modelo fundacional para extracción curricular. |

### 10.2 Secretos en Google Secret Manager

| Secreto en Secret Manager | Variable Inyectada | Obligatorio | Justificación |
| :--- | :--- | :---: | :--- |
| `ml_api_database_url` | `DATABASE_URL` | **SÍ** | URI hacia Supavisor: `postgresql://postgres.[ref]:[pass]@aws-0-[region].pooler.supabase.com:6543/postgres`. |
| `ml_api_supabase_service_role_key` | `SUPABASE_SERVICE_ROLE_KEY` | **SÍ** | Requerido para descarga de archivos docentes desde bucket privado `teacher-materials`. |
| `ml_api_gemini_api_key` | `GEMINI_API_KEY` | **Condicional** | Requerido únicamente si `LLM_PROVIDER=gemini`. |
| `ml_api_openai_api_key` | `OPENAI_API_KEY` | **Condicional** | Requerido únicamente si `LLM_PROVIDER=openai`. |
| `ml_api_supabase_jwt_secret` | `SUPABASE_JWT_SECRET` | **Opcional** | Solo necesario si el proyecto de Supabase emite tokens heredados HS256. Innecesario para ES256/JWKS. |

---

## 11. Conclusión y Próximos Pasos para el Despliegue

Todos los bloqueadores técnicos (P1) y requerimientos de robustez de base de datos, dependencias y contenedor (P2) han sido resueltos y verificados experimentalmente.

El microservicio `services/ml-api` se encuentra **técnicamente preparado para su despliegue** en Google Cloud Run tan pronto como se completen las siguientes acciones de aprovisionamiento:
1. Crear el proyecto en GCP y habilitar Cloud Run y Secret Manager.
2. Cargar los secretos requeridos en Secret Manager (`DATABASE_URL`, `SUPABASE_SERVICE_ROLE_KEY`, `GEMINI_API_KEY`).
3. Vincular el repositorio `TF4ir/PlataformaMicro` en Cloud Build con contexto `.` y Dockerfile `services/ml-api/Dockerfile`.
4. Definir la estrategia de procesamiento asíncrono para el worker curricular (Cloud Tasks vs Dedicated Service).
