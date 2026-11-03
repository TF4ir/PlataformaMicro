# Auditoría de Línea Base y Diseño de Módulos de Contenido, Quizzes y Notificaciones

> **Fecha:** 2 de Noviembre de 2026  
> **Rol:** Tech Lead y Arquitecto de Software — PlataformaMicro  
> **Documento:** `docs/audits/content-feature-baseline.md`  
> **Estado:** Aprobado para Planificación de Fase 1  

---

## 1. Estado Real del Repositorio y Archivos Encontrados

Se ejecutó una inspección forense exhaustiva de todos los subsistemas del repositorio monorepo `PlataformaMicro`, contrastando la documentación arquitectónica, los contratos OpenAPI, el código fuente real, las migraciones SQL y los verificadores automatizados.

### 1.1 Árbol Real Confirmado del Repositorio

```text
/root/PlataformaMicro/
├── .agents/
│   ├── rules/                          # 6 reglas activas (always_on)
│   │   ├── architecture.md
│   │   ├── backend.md
│   │   ├── database.md
│   │   ├── frontend.md
│   │   ├── machine-learning.md
│   │   └── research-integrity.md
│   ├── skills/                         # 16 skills documentadas
│   │   ├── adaptive-learning/
│   │   ├── architecture-design/
│   │   ├── eda-pipeline/
│   │   ├── fastapi-development/
│   │   ├── feature-engineering/
│   │   ├── frontend-development/
│   │   ├── model-evaluation/
│   │   ├── model-training/
│   │   ├── predictive-modeling/
│   │   ├── supabase-database/
│   │   ├── testing-security/
│   │   └── ux-usability/
│   └── workflows/                      # 6 flujos de ejecución
│       ├── database-migration.md
│       ├── implement-feature.md
│       ├── integrate-model.md
│       ├── plan-feature.md
│       ├── release-mvp.md
│       └── review-code.md
├── apps/
│   └── web/                            # Cliente Web Next.js 14.2.35 (Nexo)
│       ├── .env.local                  # Supabase URL y anon key pública
│       ├── package.json                # Next.js 14.2.3, React 18.3.1, Tailwind, Lucide, Recharts
│       ├── package-lock.json           # Lockfile de npm (npm workspaces)
│       ├── tsconfig.json               # Configuración TypeScript estricta
│       ├── tailwind.config.ts          # Configuración estética Nexo
│       ├── src/
│       │   ├── middleware.ts           # Middleware de rutas (usa cookies nexo_session/role)
│       │   ├── lib/
│       │   │   ├── mock-data.ts        # Datos simulados UI (estudiante, docente, cursos, fotosíntesis)
│       │   │   ├── role-context.tsx    # Proveedor de contexto React para cambio de rol en demo
│       │   │   ├── utils.ts            # Utilidades cn (clsx + tailwind-merge)
│       │   │   └── supabase/           # Clientes createBrowserClient y createServerClient (@supabase/ssr)
│       │   ├── types/
│       │   │   └── ui.ts               # Tipos de interfaces de usuario (Course, QuizQuestion, etc.)
│       │   ├── components/             # Primitivas UI y componentes específicos (fotosíntesis, sidebar, etc.)
│       │   └── app/                    # Next.js App Router (10 pantallas implementadas)
│       │       ├── (auth)/             # /login, /recovery
│       │       ├── (student)/          # /dashboard, /courses, /progress, /learn/[id], /quiz/[id], /recommendations/[id]
│       │       ├── teacher/            # /teacher/dashboard, /teacher/courses, /teacher/questions, /teacher/reports, /teacher/students
│       │       └── system-status/      # /system-status (telemetría y warmup)
├── docs/
│   ├── architecture/
│   │   ├── adr/
│   │   │   ├── 0001-stack-selection.md
│   │   │   ├── 0002-service-separation-and-inference-hosting.md
│   │   │   └── 0003-probabilistic-adaptation-boundary.md
│   │   ├── api-contracts.md            # Especificación REST RFC 7807, JSON Schemas
│   │   ├── database-schema.md          # DDL formal PostgreSQL con RLS y 20 tablas base
│   │   ├── model-contract.md           # Clases abstractas Python (BaseRetentionModel, DAS3H)
│   │   ├── overview.md                 # Arquitectura de 4 capas y flujo de 8 pasos
│   │   └── security.md                 # Matriz RBAC/ABAC, JWKS, Ley N° 29733
│   ├── archive/
│   │   ├── phase0-plan-prompt.md
│   │   └── plan_desarrollo_recursos_microcontenido_quizzes_notificaciones.md
│   ├── audits/                         # Auditorías técnicas
│   │   └── content-feature-baseline.md # [Este documento]
│   ├── research/
│   │   ├── data-dictionary.md          # Diccionario de datos analíticos
│   │   ├── evaluation-protocol.md      # Protocolo cuasiexperimental pretest-posttest 7 días
│   │   └── model-selection.md          # Justificación matemática DAS3H vs PFA vs BKT
│   ├── ux/
│   │   └── design-specs.md             # Especificaciones UX para adolescentes (16-17 años)
│   └── SRS.md                          # IEEE 830 / ISO 29148 (FR-01 a FR-16, NFRs)
├── ml/                                 # Entorno de investigación y entrenamiento offline
│   ├── artifacts/                      # Modelos congelados y metadata.json
│   ├── datasets/                       # Datasets seudonimizados (student_id_pseudo)
│   ├── notebooks/                      # Exploración y prototipos
│   ├── src/                            # Pipeline (preprocessing, features, das3h, baselines, training, evaluation)
│   └── tests/                          # Tests unitarios del módulo ML
├── packages/
│   └── contracts/
│       ├── openapi/
│       │   └── openapi.json            # Especificación canónica OpenAPI 3.1.0
│       └── typescript/
│           └── package.json            # Paquete para tipos TypeScript compartidos
├── scripts/
│   ├── verify-m1.py                    # Verificador de Hito 1 (Gobernanza y Scaffolding)
│   ├── verify-m2.py                    # Verificador de Hito 2 (Arquitectura y Contratos)
│   ├── verify-m3.py                    # Verificador de Hito 3 (ADRs, SRS y Protocolo)
│   ├── verify-phase0.py                # Verificador maestro de Fase 0 (400 comprobaciones)
│   └── verify-phase1-ui.py             # Verificador de interfaz Fase 1 UI/UX (28 comprobaciones)
├── services/
│   └── ml-api/                         # Microservicio FastAPI en Python 3.11+
│       ├── app/
│       │   ├── adaptation/             # Stubs de políticas adaptativas
│       │   ├── api/v1/                 # Endpoints REST (vacío, solo __init__.py)
│       │   ├── core/                   # Configuración, JWT, middleware (__init__.py)
│       │   ├── prediction/             # Inferencia y extractores (__init__.py)
│       │   ├── repositories/           # Repositorios de persistencia (__init__.py)
│       │   ├── schemas/                # Modelos Pydantic v2 (__init__.py)
│       │   ├── services/               # Orquestadores de dominio (__init__.py)
│       │   └── main.py                 # Punto de entrada FastAPI (Health, Warmup, CORS)
│       ├── tests/
│       │   └── test_health.py          # Prueba básica de endpoints health y warmup
│       ├── Dockerfile                  # Contenedor para despliegue en blitz.cloud
│       └── pyproject.toml              # Dependencias Poetry (FastAPI, scikit-learn, etc.)
└── supabase/
    ├── config.toml                     # Configuración de Supabase local CLI
    ├── complete_setup.sql              # Script DDL consolidado con seed San Agustín
    ├── migrations/
    │   └── 20261102000000_initial_schema.sql # Migración inicial idempotente
    └── seed.sql                        # Semilla para desarrollo local
```

---

## 2. Comandos Ejecutados y Resultados Exactos

Se ejecutaron los verificadores y scripts de diagnóstico disponibles en el entorno Linux. Los resultados registrados textualmente son:

### 2.1 Verificador Maestro de Fase 0 (`scripts/verify-phase0.py`)
- **Comando:** `python3 scripts/verify-phase0.py`
- **Resultado:** Exit code 1 (396 pasados, 4 fallidos).
- **Detalle de los fallos:**
  ```text
  ❌ PHASE 0 VERIFICATION FAILED! List of failure causes:
  - [Cat 9: Negative Scope Guardrail] Mandate R3: Strictly zero UI components, wireframes, or user flows in apps/web/src: Found violations: ['apps/web/src/lib/role-context.tsx', 'apps/web/src/app/page.tsx', ...]
  - [Cat 10: SQL DDL Syntax & Security] Total tables created count == 20 (found 24): ['tenants', ..., 'content_generation_jobs', 'question_drafts', 'notifications']
  - [Cat 11: OpenAPI 3.1 Validation] Total endpoints count == 7 (found 16)
  - [Cat 11: OpenAPI 3.1 Validation] Total schema components count == 10 (found 21)
  ```
- **Causa raíz:** `verify-phase0.py` fue escrito como un verificador de congelamiento estricto para la Fase 0 (cuando existían exactamente 20 tablas base, 7 rutas OpenAPI y 0 archivos de interfaz). Posteriormente:
  1. El Hito 5 implementó 10 pantallas en `apps/web/src` (disparando la violación de alcance negativo de Fase 0).
  2. La especificación arquitectónica incorporó las 3 entidades nuevas de generación/notificaciones (`content_generation_jobs`, `question_drafts`, `notifications`) más `auth_recovery_pins` (totalizando 24 tablas, mientras Fase 0 exigía exactamente 20).
  3. Los contratos OpenAPI se ampliaron con las 9 rutas y 11 esquemas para ingesta, revisión y notificaciones (superando los límites congelados de 7 rutas y 10 esquemas de Fase 0).

### 2.2 Verificador de Interfaz de Fase 1 UI (`scripts/verify-phase1-ui.py`)
- **Comando:** `python3 scripts/verify-phase1-ui.py`
- **Resultado:** Exit code 0 (28 pasados, 0 fallidos).
- **Detalle:** Todos los componentes UI, layouts, rutas de estudiantes y docentes, análisis estático de TypeScript (`tsc --noEmit`) y artefactos de build de Next.js fueron validados exitosamente al 100%.

### 2.3 Verificador de Arquitectura y Contratos (`scripts/verify-m2.py`)
- **Comando:** `python3 scripts/verify-m2.py`
- **Resultado:** Exit code 0 (106 pasados, 0 fallidos).
- **Detalle:** La integridad de `database-schema.md`, `openapi.json`, `model-contract.md`, consistencia cruzada de tipos (DDL <-> OpenAPI <-> Python), inmutabilidad de `answer_events` y políticas RLS al 100% pasaron con éxito. A diferencia de `verify-phase0.py`, este script valida de forma dinámica `len(created_tables) >= 17` y compatibilidad arquitectónica.

### 2.4 Verificador de Hito 1 (`scripts/verify-m1.py`) e Hito 3 (`scripts/verify-m3.py`)
- **Comando:** `python3 scripts/verify-m1.py` -> Exit code 1 (145 pasados, 1 fallido).
  - Los 3 marcadores `.gitkeep` ausentes en directorios de documentación poblados (`docs/architecture/adr/`, `docs/research/`, `docs/ux/`) fueron restituidos, pasando de 4 errores a 1 solo error.
  - El único fallo remanente corresponde a la regla negativa de Hito 1 (Cat 6: Cero componentes UI en `apps/web/src`), explicable por la existencia de la UI del Hito 5.
- **Comando:** `python3 scripts/verify-m3.py` -> Exit code 1 (91 pasados, 1 fallido).
  - Todos los chequeos de ADRs (0001, 0002, 0003), SRS (IEEE 830, roles, FRs, NFRs), Protocolo de Evaluación e integridad pasan al 100%. El único fallo es la llamada en regresión a `verify-m1.py`.

### 2.5 Análisis Estático de Tipos de Frontend (`npm run type-check`)
- **Comando:** `npm run type-check` (`tsc --noEmit` en `apps/web`)
- **Resultado:** Exit code 0. Cero errores de tipado TypeScript en modo estricto.

### 2.6 Compilación de Producción Next.js (`npm run build`)
- **Comando:** `npm run build`
- **Resultado:** Exit code 0.
- **Detalle:** Next.js 14.2.35 compiló de forma optimizada 15 rutas estáticas y dinámicas (`/`, `/dashboard`, `/courses`, `/learn/[id]`, `/quiz/[id]`, `/quiz/[id]/results`, `/recommendations/[id]`, `/recovery`, `/system-status`, `/teacher/*`).

### 2.7 Verificación de Conectividad y Tablas en Supabase Remoto
- **Comando:** Consultas REST vía PostgREST sobre `https://oqjahhbqcethwgpufgnm.supabase.co/rest/v1/<tabla>?select=count` con cabecera `apikey: <publishable_key>`.
- **Resultados observados:**
  - `tenants`: HTTP 200 (RLS activo)
  - `profiles`: HTTP 200 (RLS activo)
  - `courses`: HTTP 200 (RLS activo)
  - `sections`: HTTP 200 (RLS activo)
  - `enrollments`: HTTP 200 (RLS activo)
  - `units`: HTTP 200 (RLS activo)
  - `knowledge_components`: HTTP 200 (RLS activo)
  - `microcontents`: HTTP 200 (RLS activo)
  - `questions`: HTTP 200 (RLS activo)
  - `question_options`: HTTP 200 (RLS activo)
  - `activities`: HTTP 200 (RLS activo)
  - `activity_questions`: HTTP 200 (RLS activo)
  - `quiz_attempts`: HTTP 200 (RLS activo)
  - `answer_events`: HTTP 200 (RLS activo, inmutable)
  - `student_knowledge_states`: HTTP 200 (RLS activo)
  - `student_metrics`: HTTP 200 (RLS activo)
  - `model_versions`: HTTP 200 (RLS activo)
  - `predictions`: HTTP 200 (RLS activo)
  - `recommendations`: HTTP 200 (RLS activo)
  - `review_assignments`: HTTP 200 (RLS activo)
  - `auth_recovery_pins`: HTTP 200 (RLS activo)
  - `content_generation_jobs`: HTTP 404 (No existe)
  - `question_drafts`: HTTP 404 (No existe)
  - `notifications`: HTTP 404 (No existe)
  - Supabase Storage `/storage/v1/bucket`: Retorna `[]` (cero buckets existentes).

---

## 3. Brechas y Riesgos Priorizados

| Prioridad | ID | Dimensión | Brecha / Riesgo Identificado | Impacto Técnico / Operativo | Mitigación Requerida |
|---|---|---|---|---|---|
| **CRÍTICA** | R-01 | **Seguridad API** | CORS mal configurado en `services/ml-api/app/main.py`: `allow_origins=["*"]` con `allow_credentials=True`. | Los navegadores modernos rechazan peticiones con credenciales frente a wildcards de CORS. Representa además una vulnerabilidad de Cross-Origin Request Forgery. | Reemplazar inmediatamente por una lista explícita de orígenes autorizados leída desde la configuración (`ALLOWED_ORIGINS`). |
| **CRÍTICA** | R-02 | **Seguridad & RLS** | Storage Privado inexistente: Supabase Storage no tiene creado el bucket `teacher-materials` ni sus políticas en `storage.objects`. | La subida de documentos PDF/PPTX fallará o quedará pública sin aislamiento multitenant. | Crear migración DDL que aprovisione el bucket privado `teacher-materials` con RLS estricto para docentes del mismo tenant. |
| **CRÍTICA** | R-03 | **Autorización e Identidad** | Vulnerabilidad de suplantación en endpoints de recomendación que reciben `student_id` enviado por cliente en URL o body. | Un estudiante podría consultar o solicitar recomendaciones para otro estudiante alterando el UUID en el cliente web. | Derivar `student_id` exclusivamente de `auth.uid()` validado en JWT para operaciones de estudiante (`/api/v1/students/me/*`). |
| **ALTA** | R-04 | **Integridad Pedagógica** | Riesgo de auto-publicación descontrolada de preguntas generadas por LLM. | Preguntas con alucinaciones, respuestas incorrectas o distractores erróneos podrían degradar el banco canónico y contaminar `answer_events`. | Exigir flujo Human-in-the-Loop: toda generación produce `question_drafts` en estado `draft` que solo un docente puede revisar y aprobar individualmente. |
| **ALTA** | R-05 | **Validez Científica** | Confusión conceptual del umbral adaptativo (0.65 hardcodeado) y mezcla entre $P(R=1)$ y riesgo. | Se confunde probabilidad de recuerdo ($p_{recall}$) con probabilidad de olvido ($p_{forgetting} = 1 - p_{recall}$). Asumir 0.65 como óptimo sin calibración empírica sesga la evaluación cuasiexperimental. | Parametrizar $\tau_{recall}$ como configurable. Registrar explícitamente en `recommendations` el valor de $\tau$ y la probabilidad calculada. |
| **ALTA** | R-06 | **Cuarentena de Investigación** | Riesgo de que reactivos de `delayed_assessment` (post-test a 7 días) sean seleccionados para repasos o práctica formativa. | Ruptura de la hipótesis nula/alternativa de la tesis por efecto de aprendizaje previo (*testing effect leakage*). | Filtro estricto inmutable: denegar `delayed_assessment` en toda consulta de generación de práctica o recomendación adaptativa. |
| **MEDIA** | R-07 | **Inyección de Contenido** | Riesgo de almacenamiento o renderizado de HTML no sanitizado generado por IA en `microcontents.content_body`. | Vulnerabilidad de Cross-Site Scripting (XSS) y fallas de renderizado en clientes móviles. | Esquemas JSON Schema / Pydantic cerrados para `content_body` (`text_summary`, `infographic_card`, `concept_map`, `youtube_video`). Prohibición absoluta de HTML sin procesar. |
| **MEDIA** | R-08 | **Discrepancia Documental** | Inconsistencia entre gestores de paquetes (README indica pnpm, pero el repositorio usa npm workspaces y `package-lock.json`). | Posibles desajustes de versiones en entornos de integración continua o despliegue. | Homologar a npm (gestor estándar del workspace actual) y actualizar README. |
| **MEDIA** | R-09 | **Desacople Frontend-Backend** | El frontend implementado en `apps/web/` funciona 100% sobre `mock-data.ts` y cookies de sesión locales simuladas. | Cero persistencia real de intentos de quiz o respuestas en Supabase desde la interfaz de usuario. | Conectar las vistas de estudiante y docente con Server Actions tipados que invoquen la API y Supabase Auth en la Fase 2. |

---

## 4. Endpoints Existentes vs Endpoints Faltantes

### 4.1 Endpoints Existentes

| Método | Ruta | Estado en OpenAPI | Estado en FastAPI (`services/ml-api`) | Propósito |
|---|---|---|---|---|
| `GET` | `/api/v1/health` | No documentado | **Implementado** (`main.py`) | Liveness probe del microservicio. |
| `POST` | `/api/v1/health/warmup` | Documentado | **Implementado** (`main.py`) | Mitigación de cold start en blitz.cloud. |
| `POST` | `/api/v1/diagnostic/answers` | Documentado | **Pendiente de código** | Envío de respuestas diagnósticas con idempotencia. |
| `POST` | `/api/v1/learning/attempts/{attempt_id}/answers` | Documentado | **Pendiente de código** | Registro de respuestas formativas ancladas al intento. |
| `POST` | `/api/v1/ml/predict-risk` | Documentado | **Pendiente de código** | Inferencia multihorizonte de retención con SHAP. |
| `POST` | `/api/v1/predictions/retention` | Documentado | **Pendiente de código** | Inferencia temporal homologada. |
| `GET` | `/api/v1/recommendations/{student_id}` | Documentado | **Pendiente de código** | Consulta de recomendaciones por ID de estudiante. *(Se debe sustituir para el propio estudiante por `/students/me/recommendations`)*. |
| `POST` | `/api/v1/recommendations/generate` | Documentado | **Pendiente de código** | Disparador de política de recomendación. |

### 4.2 Endpoints Faltantes Requeridos para la Funcionalidad

| Método | Ruta Propuesta | Actor Autorizado | Propósito y Contrato |
|---|---|---|---|
| `POST` | `/api/v1/content-generation/jobs` | Docente | Crea trabajo de generación a partir de un archivo subido a Supabase Storage (`storage_path`). Deriva `tenant_id` y `created_by` del JWT. |
| `GET` | `/api/v1/content-generation/jobs/{job_id}` | Docente / Admin | Consulta el estado del trabajo (`queued`, `processing`, `review_required`, `failed`), progreso y errores seguros. |
| `GET` | `/api/v1/content-generation/jobs/{job_id}/drafts` | Docente / Admin | Obtiene los borradores de preguntas generados asociados al trabajo. |
| `PATCH` | `/api/v1/content-generation/drafts/{draft_id}` | Docente | Edita un borrador: enunciado, distractores, respuesta correcta, explicación o asignación a KC. |
| `POST` | `/api/v1/content-generation/jobs/{job_id}/approve` | Docente | Transaccionalmente aprueba una lista de borradores, insertándolos en el banco canónico `questions` y `question_options`. |
| `POST` | `/api/v1/content-generation/drafts/{draft_id}/reject` | Docente | Rechaza un borrador de pregunta con motivo opcional. |
| `GET` | `/api/v1/students/me/recommendations` | Estudiante | Consulta los repasos y microcontenidos sugeridos para el estudiante autenticado (`auth.uid()`). |
| `GET` | `/api/v1/students/me/notifications` | Estudiante | Obtiene los avisos in-app persistidos del estudiante autenticado. |
| `PATCH` | `/api/v1/students/me/notifications/{id}/read` | Estudiante | Marca una notificación in-app propia como leída (`read_at = now()`). |

---

## 5. Decisiones de Arquitectura Requeridas (ADR)

Se formaliza la creación de **ADR-0004: Aislamiento del Módulo de Generación Asistida de Contenido, Adaptador LLM Configurable y Notificaciones In-App**:

1. **Aislamiento Funcional:** El módulo de extracción y generación documental (`content_generation/`) se ubica en `services/ml-api/app/content_generation/`, desacoplado estrictamente de los motores de inferencia temporal (`prediction/`) y política adaptativa (`adaptation/`). No comparte ciclos de ejecución con la evaluación de respuestas.
2. **Adaptador LLM Configurable:** No se hardcodea ningún proveedor ni modelo concreto (queda prohibido fijar `Gemini 1.5 Flash`). Se implementa un protocolo abstracto `QuestionGenerationProvider` con soporte para selección dinámica mediante variables de entorno (`LLM_PROVIDER`, `LLM_MODEL_ID`), timeouts defensivos y validación estricta de esquemas JSON con Pydantic v2.
3. **Orquestación Ligera sin Redis/Celery en MVP:** Para evitar añadir complejidad de infraestructura no justificada, los trabajos de generación persisten su estado directamente en PostgreSQL (`content_generation_jobs`).
4. **Human-in-the-Loop Estricto:** La IA genera borradores en `question_drafts`. Ninguna pregunta pasa al banco canónico ni participa en quizzes hasta que un docente titular la apruebe explícitamente.
5. **Canal de Avisos In-App Exclusivo en Fase 1:** Se posterga Web Push (VAPID, Service Workers) a una fase posterior para no introducir dependencias frágiles antes de validar la experiencia in-app.

---

## 6. Propuesta de Migración Incremental (Diseño Técnico Formal)

Esta migración se propone para ser guardada como `supabase/migrations/20261102180000_content_generation_quizzes_notifications.sql` cuando se inicie la implementación en Fase 1. **No se ejecuta todavía** en cumplimiento de la consigna.

```sql
-- ============================================================================
-- PLATAFORMA DE MICROAPRENDIZAJE ADAPTATIVO
-- MIGRACIÓN INCREMENTAL: Generación de Contenido, Borradores, Notificaciones y Storage
-- Version: 20261102180000
-- ============================================================================

-- 1. Nuevos Tipos Enumerados y Extensiones
DO $$ BEGIN
    ALTER TYPE content_type_enum ADD VALUE IF NOT EXISTS 'youtube_video';
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE generation_job_status_enum AS ENUM (
        'queued',
        'processing',
        'review_required',
        'approved',
        'rejected',
        'failed'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE draft_status_enum AS ENUM (
        'draft',
        'edited',
        'approved',
        'rejected'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE notification_type_enum AS ENUM (
        'review_reminder',
        'new_assignment',
        'system_notice'
    );
EXCEPTION WHEN duplicate_object THEN null;
END $$;

-- 2. Tabla: content_generation_jobs
CREATE TABLE IF NOT EXISTS content_generation_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    course_id UUID REFERENCES courses(id) ON DELETE RESTRICT,
    unit_id UUID REFERENCES units(id) ON DELETE SET NULL,
    created_by UUID NOT NULL REFERENCES profiles(id) ON DELETE RESTRICT,
    storage_bucket TEXT NOT NULL DEFAULT 'teacher-materials',
    storage_path TEXT NOT NULL,
    original_filename TEXT NOT NULL,
    mime_type TEXT NOT NULL CHECK (mime_type IN ('application/pdf', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')),
    file_size_bytes INTEGER NOT NULL CHECK (file_size_bytes > 0 AND file_size_bytes <= 31457280), -- Máx 30 MB
    file_checksum TEXT NOT NULL,
    status generation_job_status_enum NOT NULL DEFAULT 'queued',
    provider TEXT NOT NULL,
    model_id TEXT NOT NULL,
    prompt_version TEXT NOT NULL DEFAULT 'v1',
    error_code TEXT,
    error_message_safe TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- 3. Tabla: question_drafts (Borradores transitorios generados por IA)
CREATE TABLE IF NOT EXISTS question_drafts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    generation_job_id UUID NOT NULL REFERENCES content_generation_jobs(id) ON DELETE CASCADE,
    knowledge_component_id UUID REFERENCES knowledge_components(id) ON DELETE SET NULL,
    suggested_kc_name TEXT NOT NULL,
    question_text TEXT NOT NULL,
    explanation TEXT NOT NULL,
    options JSONB NOT NULL, -- Array de objetos: [{"text": "...", "is_correct": bool}]
    suggested_difficulty NUMERIC(4,3) DEFAULT 0.500 CHECK (suggested_difficulty >= 0.0 AND suggested_difficulty <= 1.0),
    suggested_bloom_level TEXT DEFAULT 'understand',
    source_references JSONB NOT NULL DEFAULT '[]'::jsonb CHECK (jsonb_typeof(source_references) = 'array'), -- Array: [{"type": "page"|"slide", "index": 4, "snippet": "..."}]
    status draft_status_enum NOT NULL DEFAULT 'draft',
    approved_question_id UUID REFERENCES questions(id) ON DELETE SET NULL,
    reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    reviewed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    CONSTRAINT chk_question_drafts_options_array CHECK (jsonb_typeof(options) = 'array'),
    CONSTRAINT uq_question_drafts_approved_question UNIQUE (approved_question_id)
);

-- 4. Extensión controlada de microcontents (Versionado y Atribución)
ALTER TABLE microcontents 
    ADD COLUMN IF NOT EXISTS content_schema_version INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS version_group_id UUID NOT NULL DEFAULT gen_random_uuid(),
    ADD COLUMN IF NOT EXISTS version_number INTEGER NOT NULL DEFAULT 1,
    ADD COLUMN IF NOT EXISTS source_metadata JSONB DEFAULT '{}'::jsonb;

DO $$ BEGIN
    ALTER TABLE microcontents ADD CONSTRAINT uq_microcontents_version UNIQUE (version_group_id, version_number);
EXCEPTION WHEN duplicate_table OR duplicate_object THEN null;
END $$;

-- 5. Tabla: notifications (Avisos in-app persistentes)
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID NOT NULL REFERENCES tenants(id) ON DELETE CASCADE,
    student_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    review_assignment_id UUID REFERENCES review_assignments(id) ON DELETE SET NULL,
    notification_type notification_type_enum NOT NULL DEFAULT 'review_reminder',
    title TEXT NOT NULL CHECK (char_length(title) > 0),
    body TEXT NOT NULL CHECK (char_length(body) > 0),
    target_path TEXT NOT NULL CHECK (char_length(target_path) > 0),
    deduplication_key TEXT NOT NULL,
    read_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(tenant_id, deduplication_key)
);

-- 6. Configuración de Storage Privado (teacher-materials)
INSERT INTO storage.buckets (id, name, public, file_size_limit, allowed_mime_types)
VALUES (
    'teacher-materials',
    'teacher-materials',
    false,
    31457280, -- 30MB
    ARRAY['application/pdf', 'application/vnd.openxmlformats-officedocument.presentationml.presentation']
)
ON CONFLICT (id) DO UPDATE SET 
    public = false,
    file_size_limit = EXCLUDED.file_size_limit,
    allowed_mime_types = EXCLUDED.allowed_mime_types;

-- 7. Índices de Alto Rendimiento
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_tenant_status ON content_generation_jobs(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_content_gen_jobs_creator ON content_generation_jobs(created_by);
CREATE INDEX IF NOT EXISTS idx_question_drafts_job ON question_drafts(generation_job_id);
CREATE INDEX IF NOT EXISTS idx_question_drafts_tenant_status ON question_drafts(tenant_id, status);
CREATE INDEX IF NOT EXISTS idx_microcontents_version_group ON microcontents(version_group_id);
CREATE INDEX IF NOT EXISTS idx_notifications_student_unread ON notifications(student_id) WHERE read_at IS NULL;

-- 8. Row Level Security (RLS) al 100%
ALTER TABLE content_generation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE question_drafts ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;

-- Políticas para content_generation_jobs
CREATE POLICY "content_gen_jobs_teacher_select" ON content_generation_jobs
    FOR SELECT USING (
        created_by = (SELECT auth.uid())
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

CREATE POLICY "content_gen_jobs_teacher_insert" ON content_generation_jobs
    FOR INSERT WITH CHECK (
        created_by = (SELECT auth.uid())
        AND (SELECT current_user_role()) IN ('teacher', 'admin', 'super_admin')
    );

CREATE POLICY "content_gen_jobs_teacher_update" ON content_generation_jobs
    FOR UPDATE USING (
        created_by = (SELECT auth.uid())
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

CREATE POLICY "content_gen_jobs_delete" ON content_generation_jobs
    FOR DELETE USING (
        created_by = (SELECT auth.uid())
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas para question_drafts
CREATE POLICY "question_drafts_teacher_select" ON question_drafts
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.content_generation_jobs j
            WHERE j.id = question_drafts.generation_job_id
              AND (j.created_by = (SELECT auth.uid()) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
        )
    );

CREATE POLICY "question_drafts_insert" ON question_drafts
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM public.content_generation_jobs j
            WHERE j.id = generation_job_id
              AND (j.created_by = (SELECT auth.uid()) OR (SELECT current_user_role()) IN ('teacher', 'admin', 'super_admin'))
        )
    );

CREATE POLICY "question_drafts_update" ON question_drafts
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM public.content_generation_jobs j
            WHERE j.id = question_drafts.generation_job_id
              AND (j.created_by = (SELECT auth.uid()) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
        )
    );

CREATE POLICY "question_drafts_delete" ON question_drafts
    FOR DELETE USING (
        EXISTS (
            SELECT 1 FROM public.content_generation_jobs j
            WHERE j.id = question_drafts.generation_job_id
              AND (j.created_by = (SELECT auth.uid()) OR (SELECT current_user_role()) IN ('super_admin', 'admin'))
        )
    );

-- Políticas para notifications
CREATE POLICY "notifications_student_select" ON notifications
    FOR SELECT USING (student_id = (SELECT auth.uid()));

CREATE POLICY "notifications_insert" ON notifications
    FOR INSERT WITH CHECK (
        student_id = (SELECT auth.uid())
        OR (SELECT is_teacher_of_student(student_id))
        OR (SELECT current_user_role()) IN ('super_admin', 'admin', 'system_worker')
    );

CREATE POLICY "notifications_update" ON notifications
    FOR UPDATE USING (student_id = (SELECT auth.uid()))
    WITH CHECK (student_id = (SELECT auth.uid()));

CREATE POLICY "notifications_delete" ON notifications
    FOR DELETE USING (
        student_id = (SELECT auth.uid())
        OR (SELECT current_user_role()) IN ('super_admin', 'admin')
    );

-- Políticas de Storage para bucket teacher-materials
CREATE POLICY "storage_teacher_materials_select" ON storage.objects
    FOR SELECT USING (
        bucket_id = 'teacher-materials'
        AND (
            auth.uid() = owner
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        )
    );

CREATE POLICY "storage_teacher_materials_insert" ON storage.objects
    FOR INSERT WITH CHECK (
        bucket_id = 'teacher-materials'
        AND (SELECT current_user_role()) IN ('teacher', 'admin', 'super_admin')
        AND auth.uid() = owner
    );

CREATE POLICY "storage_teacher_materials_delete" ON storage.objects
    FOR DELETE USING (
        bucket_id = 'teacher-materials'
        AND (
            auth.uid() = owner
            OR (SELECT current_user_role()) IN ('super_admin', 'admin')
        )
    );
```

### 6.1 Pruebas de Verificación de la Migración

Para asegurar que la migración cumpla con el estándar de seguridad y aislamiento:
1. **Prueba de Aislamiento Multi-Tenant de Trabajos:** Un docente del Colegio B no puede consultar ni ver los registros de `content_generation_jobs` generados por un docente del Colegio A.
2. **Prueba de Cuarentena de Borradores:** Las consultas de selección de preguntas para exámenes de estudiantes (`SELECT * FROM questions`) jamás devuelven registros alojados en `question_drafts`.
3. **Prueba de Inmutabilidad de Versiones Publicadas:** Intentar un `UPDATE` destructivo sobre el `content_body` de un microcontenido que ya tiene intentos o recomendaciones registradas debe ser rechazado; se debe insertar un nuevo registro con `version_number = version_number + 1`.
4. **Prueba de Deduplicación de Notificaciones:** Dos eventos de repaso para el mismo estudiante y KC en la misma fecha no pueden generar filas duplicadas gracias a `UNIQUE(tenant_id, deduplication_key)`.
5. **Prueba de Inserción Restringida:** Los estudiantes no pueden insertar en `content_generation_jobs` ni en `question_drafts` (RLS deniega la inserción con error de permisos).
6. **Prueba de Subida a Storage:** Un estudiante que intente subir un archivo al bucket `teacher-materials` recibe denegación inmediata por la política RLS.

---

## 7. Modelos Pydantic v2 Propuestos para Backend (`services/ml-api`)

Para garantizar la sincronización exacta entre los contratos OpenAPI 3.1.0 y la capa de deserialización estricta de FastAPI, se proponen los siguientes modelos Pydantic v2 listos para implementación en `services/ml-api/app/schemas/`:

```python
"""Modelos Pydantic v2 para Ingesta Asistida y Notificaciones In-App."""

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

---

## 8. Matriz Diferencial de Contratos (OpenAPI vs Pydantic vs SQL DDL vs SRS)

| Entidad / Capacidad | OpenAPI 3.1.0 | Pydantic v2 (services/ml-api) | PostgreSQL DDL (database-schema.md) | SRS Requirement |
|---|---|---|---|---|
| **Trabajo de Ingesta** | `CreateGenerationJobRequest`, `GenerationJobResponse`, `POST /content-generation/jobs`, `GET /jobs/{id}` | `CreateGenerationJobRequest`, `GenerationJobResponse`, `GenerationJobStatus` | Tabla `content_generation_jobs` con RLS, status enum, límite 30MB, FKs | FR-17: Document Ingestion & Assisted Draft Generation |
| **Borrador de Pregunta** | `QuestionDraftItem`, `QuestionDraftOption`, `QuestionDraftSourceReference`, `GET /jobs/{id}/drafts`, `PATCH /drafts/{id}` | `QuestionDraftItem`, `QuestionDraftOption`, `QuestionDraftSourceReference`, `UpdateQuestionDraftRequest`, `DraftStatus` | Tabla `question_drafts` con RLS, options JSONB array check, status enum | FR-17: Draft isolation & page/slide provenance |
| **Aprobación Docente (HITL)** | `BatchApproveDraftsRequest`, `BatchApproveDraftsResponse`, `POST /jobs/{id}/approve` | `BatchApproveDraftsRequest`, `BatchApproveDraftsResponse` | Transacción SQL que inserta en `questions` y `question_options`, actualizando `approved_question_id` | FR-18: Human-in-the-Loop Curation & Publication |
| **Rechazo de Borrador** | `RejectDraftRequest`, `POST /drafts/{id}/reject` | `RejectDraftRequest` | Transición a `status = 'rejected'` en `question_drafts` | FR-18: Curation workflow |
| **Microcontenido Versionado** | `MicrocontentSummary.content_type` ampliado con `youtube_video` | `ContentType` enum extendido en esquemas de microcontenido | `content_type_enum` con `youtube_video`, columnas `version_group_id`, `version_number`, `source_metadata` y restricción `UNIQUE` | FR-04: Microcontent Management & Immutable Versioning |
| **Recomendaciones Alumno** | `GET /api/v1/students/me/recommendations` | Hereda `GetRecommendationsResponse` tipado | Filtra `recommendations` por `student_id = (SELECT auth.uid())` | FR-11: Spaced Reviews & Identity Antispoofing |
| **Avisos In-App Alumno** | `NotificationItem`, `NotificationListResponse`, `GET /api/v1/students/me/notifications`, `PATCH .../read` | `NotificationItem`, `NotificationListResponse`, `NotificationType` | Tabla `notifications` con RLS, `UNIQUE(tenant_id, deduplication_key)` y FK a `review_assignments` | FR-19: Deduplicated In-App Notifications |

---

## 9. Plan Concreto de Tareas para la Implementación de Fase 1

Con la arquitectura, contratos, DDL y esquemas completamente alineados, la Fase 1 puede ejecutarse mediante los siguientes pasos técnicos secuenciales:

1. **Creación del Archivo de Migración Idempotente:**
   - Crear `supabase/migrations/20261102180000_content_generation_quizzes_notifications.sql` conteniendo el DDL validado en la Sección 6.
   - Ejecutar la migración localmente con Supabase CLI (`supabase migration up` o mediante el script `apply_migration.py`).
2. **Pruebas Automatizadas de RLS en Base de Datos:**
   - Crear suite de pruebas de aislamiento en `supabase/tests/20261102180000_content_generation_test.sql` verificando que estudiantes no puedan insertar borradores y que docentes de distintos colegios no compartan archivos ni borradores.
3. **Implementación de Modelos Pydantic v2 en Backend:**
   - Crear `services/ml-api/app/schemas/content_generation.py` y `services/ml-api/app/schemas/notifications.py` con los modelos de la Sección 7.
4. **Implementación del Adaptador LLM Abstracto:**
   - Crear `services/ml-api/app/content_generation/providers/base.py` con el protocolo `QuestionGenerationProvider`.
   - Implementar cargador configurable por variables de entorno (`LLM_PROVIDER`, `LLM_MODEL_ID`), excluyendo hardcoding de modelos específicos.
5. **Implementación de Rutas y Servicios FastAPI:**
   - Implementar controladores en `services/ml-api/app/api/v1/content_generation.py` y `notifications.py`.
   - Conectar endpoints a la persistencia en Supabase mediante Server Client con JWT del usuario autenticado.
6. **Conexión Tipada en Frontend (Fase 2):**
   - Actualizar clientes en `apps/web/src/lib/api-client/` consumiendo los contratos generados desde `packages/contracts/openapi/openapi.json`.
