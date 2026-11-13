# Release MVP — Endurecimiento de seguridad + despliegue de FastAPI en AWS Lambda

> **Documento:** Informe de release consolidado (preparación, no publicación)
> **Fecha:** 2026-11-12
> **Rama local:** `release/mvp-aws-lambda` (creada desde `main`)
> **Servicios afectados:** Supabase PostgreSQL/RLS, `services/ml-api` (FastAPI), infraestructura AWS SAM/ECR
> **Estado:** entregable preparado y validado en local. **Sin commits, sin push, sin deploy, sin cambios en Cloudflare ni en Supabase remoto.**
> **Veredicto:** apto para revisión y publicación coordinada; **no publicado**.

---

## 1. Resumen ejecutivo

Este release consolida en una sola entrega:

1. **Bloqueantes de seguridad F-01, F-02, F-04, F-05 y F-06** identificados en
   `docs/security/2026-11-09/P0.1_SECURITY_VALIDATION_REPORT.md`.
2. **Despliegue alternativo de FastAPI en AWS Lambda** mediante contenedor de
   imagen, **AWS Lambda Web Adapter 1.1.0** y **Lambda Function URL**
   (`AuthType: NONE`), sin Mangum y sin API Gateway.
3. **Compatibilidad con Supabase Shared Pooler** en modo transacción
   (puerto `6543`), con `statement_cache_size=0`, TLS obligatorio, pool de
   tamaño 1 y recuperación explícita de conexiones obsoletas tras el
   congelamiento (*freeze*) de Lambda.
4. **Capa de identidad fail-closed** en FastAPI: `public.profiles` es la única
   fuente de `role`, `tenant_id` y cursos autorizados. Si la base de datos no
   responde, la petición protegida devuelve **503** y nunca se autoriza con
   claims del JWT.

La validación local se ejecutó con Supabase real (PostgreSQL 15.19, GoTrue
2.197.0, PostgREST 16.5), JWT reales emitidos por GoTrue y dos tenants. Los
resultados principales:

| Verificación | Resultado |
|---|---|
| `npm test` (frontend) | **73/73** pruebas aprobadas |
| `npm run type-check` | Aprobado |
| `npm run build` | Aprobado (Next.js 14.2.35) |
| `pytest` completo (`services/ml-api`) | **273 aprobadas, 2 omitidas** |
| Mypy | **72 archivos, 0 errores** |
| Ruff (`check`) | Aprobado |
| Contratos cruzados (`verify-phase0.py`, Cat 13) | **68/68** aprobadas |
| RLS real con 2 tenants y múltiples secciones | Aislamiento correcto |
| ACL de `profiles` | Sin INSERT/DELETE/TRUNCATE; UPDATE solo `full_name`,`avatar_url` |
| Imagen Lambda (`linux/amd64`) | Construida correctamente (~712 MB) |
| SAM `validate --lint` (2 plantillas) | Aprobado |
| SAM `build` + `local invoke` | Health 200, endpoints protegidos 200/403/503, CORS 200 |

**No se desplegó nada en AWS.** No hubo credenciales de AWS disponibles, por lo
que la verificación se detuvo en build de imagen y ejecución local con SAM.

---

## 2. Alcance, límites y garantías de no publicación

### 2.1 Dentro del alcance

- Migración incremental `supabase/migrations/20261109010000_release_mvp_security_hardening.sql`.
- Endurecimiento de identidad/autorización en `services/ml-api/app/core/auth.py`.
- Configuración de pooling serverless en `app/core/config.py` y
  `app/content_generation/infrastructure/database.py`.
- Resolución de artefactos ML independiente del layout del contenedor
  (`app/prediction/model_registry.py`).
- Imagen Lambda `services/ml-api/Dockerfile.lambda` (contexto: raíz del monorepo).
- Plantillas SAM/ECR, script de build/push y documentación en `deploy/aws/`.
- Ejemplo de variable futura `apps/web/.env.lambda.example`.
- Script raíz `npm test` para ejecutar las pruebas de `apps/web`.

### 2.2 Fuera del alcance / no ejecutado

- **Sin deploy a AWS** (ni ECR, ni Lambda, ni Function URL).
- **Sin cambios en Cloudflare**: el Worker sigue con su configuración actual y
  **no** se reemplazó `NEXT_PUBLIC_API_URL`.
- **Sin cambios en Supabase remoto**: las migraciones se aplicaron **solo** en
  el stack local.
- **Sin commits ni push**: todos los cambios permanecen en el árbol de trabajo
  de la rama local `release/mvp-aws-lambda`.
- **Sin Cloud Run**, sin nuevas bases de datos, sin API Gateway, sin VPC/NAT.
- No se modificaron migraciones históricas.
- No se eliminó ni se hizo `reset`/`checkout` de trabajo previo del usuario.
  El árbol contiene además cambios preexistentes en `apps/web/` que **no** forman
  parte de este release y no fueron alterados por esta preparación.

### 2.3 Garantías sobre el trabajo previo

- No se ejecutó `git reset`, `git checkout -- .`, `git clean` ni `git stash`.
- Los archivos modificados y no rastreados preexistentes se conservan.
- El informe no certifica staging ni producción: la evidencia es local.

---

## 3. Cambios de seguridad en base de datos (F-01, F-04, F-05, F-06)

Archivo: `supabase/migrations/20261109010000_release_mvp_security_hardening.sql`
(migración **incremental**; las migraciones históricas no se editaron).

### 3.1 F-01 — Recursión infinita de RLS en `sections` / `enrollments`

**Problema:** `sections_select_all` consultaba `enrollments`, cuya política
volvía a consultar `sections`. PostgREST devolvía `42P17 infinite recursion
detected in policy for relation "enrollments"` (HTTP 500) para estudiantes y
docentes.

**Solución:**

- Se eliminaron `sections_select_all`, `sections_select_tenant` y cualquier
  política previa con el mismo nombre.
- Se creó la función `public.is_enrolled_in_section(UUID)`:
  - `SECURITY DEFINER`, `STABLE`, `SET search_path = ''`.
  - Evalúa la matrícula sin reingresar a RLS.
  - Compara `e.student_id = auth.uid()`.
- Se creó `sections_select_scoped` con acceso únicamente para:
  - el docente asignado (`teacher_id = auth.uid()`),
  - el estudiante matriculado (`is_enrolled_in_section`),
  - un `admin` del mismo tenant,
  - un `super_admin` (todos los tenants).

No se concedió acceso de sección “por tenant” a estudiantes ni a docentes no
asignados. Esto corrige la recursión **sin** reintroducir acceso global.

### 3.2 F-04 — Enumeración de perfiles del tenant

**Problema:** `profiles_select_own_or_same_tenant` permitía a cualquier
estudiante listar todos los perfiles de su institución.

**Solución:** tres políticas SELECT de mínimo privilegio:

| Política | Alcance |
|---|---|
| `profiles_select_own` | `id = auth.uid()` |
| `profiles_select_teacher_students` | `public.is_teacher_of_student(id)` (solo alumnos de sus secciones) |
| `profiles_select_admin_scope` | `admin` de su tenant; `super_admin` de todos |

`is_teacher_of_student` ya existía como `SECURITY DEFINER` y une
`sections.teacher_id` con `enrollments.student_id`, por lo que el roster docente
sigue funcionando sin exponer el tenant completo.

### 3.3 F-05 — ACL residual en `profiles`

**Problema:** `anon` y `authenticated` conservaban privilegios de tabla para
INSERT/DELETE/TRUNCATE/REFERENCES/TRIGGER, y `authenticated` tenía UPDATE de
tabla completa.

**Solución:**

```sql
REVOKE UPDATE ON public.profiles FROM anon, authenticated;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER
    ON public.profiles FROM anon, authenticated;
REVOKE INSERT, DELETE, TRUNCATE, REFERENCES, TRIGGER
    ON public.profiles FROM PUBLIC;
GRANT UPDATE (full_name, avatar_url) ON public.profiles TO authenticated;
```

Estado real verificado en local:

| Rol | SELECT | UPDATE | INSERT/DELETE/TRUNCATE/REFERENCES/TRIGGER |
|---|---|---|---|
| `anon` | Sí | No | No |
| `authenticated` | Sí | Solo columnas `full_name`, `avatar_url` | No |
| `service_role` | Sí | Sí | Sí (operaciones de servidor) |
| `ml_api_worker` | Sí | No | No |

Un `PATCH` con `role`, `tenant_id`, `student_code` o `id` falla antes del trigger
con `42501 permission denied for table profiles` (HTTP 403).

### 3.4 F-06 — Trigger fail-closed sin `auth.uid()`

**Problema:** la rama “sin `auth.uid()`” del trigger permitía escribir columnas
de identidad en sesiones SQL sin sujeto verificado. En PostgREST, `anon` tiene
`auth.uid() = NULL`, por lo que la protección dependía únicamente de que no
existiera privilegio UPDATE.

**Solución:** `public.prevent_profile_privilege_escalation()` ahora evalúa
también `auth.role()`:

- Con `auth.uid()`: solo `admin`/`super_admin` pueden cambiar
  `role`/`tenant_id`/`student_code`/`id`.
- Sin `auth.uid()` y con `auth.role()` en `anon`/`authenticated`: **excepción
  `42501`** con el mensaje:
  `profiles: role, tenant_id, student_code and id are immutable for client sessions without a verified user`.
- `service_role`, migraciones y SQL directo de servidor siguen permitidos.

### 3.5 Evidencia de aislamiento RLS (JWT reales, 2 tenants)

Fixtures aplicados y eliminados en el Supabase local. Matriz observada vía
PostgREST con JWT emitidos por GoTrue:

| Usuario | `sections` | `enrollments` | `profiles` |
|---|---:|---:|---:|
| Docente A (tenant A, 2 secciones) | 2 | 10 | 11 |
| Estudiante A1 (tenant A) | 1 | 1 | 1 |
| Docente B (tenant B, 2 secciones) | 2 | 1 | 2 |
| Estudiante B1 (tenant B) | 1 | 1 | 1 |
| Estudiante B2 (tenant B, sin sección) | 0 | 0 | 1 |
| Estudiante A-extra (tenant A, sin sección) | 0 | 0 | 1 |

Sondas directas entre tenants (todas `HTTP 200`, `0 filas`):

- B1 → sección de A: 0
- Docente B → sección de A: 0
- Docente A → sección de B: 0
- B1 → perfil del docente A: 0
- Docente B → perfil del estudiante A1: 0
- Docente A → perfil del estudiante B1: 0

Estado final de la base local tras limpiar fixtures:
`1 tenant, 1 sección, 10 matrículas, 11 perfiles` (sin residuos de prueba).

---

## 4. Endurecimiento de identidad en FastAPI (F-02) y pooling serverless

Archivos: `app/core/auth.py`, `app/core/config.py`,
`app/content_generation/infrastructure/database.py`, `app/main.py`.

### 4.1 F-02 — `profiles` como única fuente de rol y tenant

Antes, si `profiles` fallaba o el pool no estaba inicializado, FastAPI caía a
`user_metadata.role` / `app_metadata.role` / `tenant_id` del JWT. Un estudiante
podía editar `user_metadata` con la clave pública y obtener autorización de
docente cuando la base no respondía.

Ahora:

1. Se valida el JWT (firma/issuer/audience/expiración) como antes.
2. Se resuelve la identidad **exclusivamente** desde PostgreSQL:
   - `SELECT tenant_id, role FROM public.profiles WHERE id = $1`.
   - Cursos autorizados: secciones del docente o matrículas del estudiante.
3. **No existe fallback a claims** para rol, tenant ni cursos.
4. Si el sujeto no tiene perfil: **403 `IDENTITY_NOT_PROVISIONED`**.
5. Si la base no responde tras el reintento: **503
   `AUTH_BACKEND_UNAVAILABLE`** con cabecera `Retry-After: 5`.
6. Una conexión obsoleta tras el *thaw* de Lambda se reintenta **una vez**
   (`DB_STALE_RETRY_ATTEMPTS=1`); el pool descarta la conexión rota y la
   siguiente adquisición crea una nueva.
7. `main.py` propaga las cabeceras de `HTTPException` (incluida `Retry-After`)
   en el formateo RFC 7807.

El endpoint `/api/v1/health` sigue siendo público y no requiere base de datos;
es la ruta de *readiness* del Lambda Web Adapter.

### 4.2 Configuración de pooling

| Variable | Valor por defecto | Uso en Lambda |
|---|---:|---|
| `DB_POOL_MODE` | `auto` | `transaction` |
| `DB_POOL_MIN_SIZE` | `1` | `1` |
| `DB_POOL_MAX_SIZE` | `5` | `1` |
| `DB_STATEMENT_CACHE_SIZE` | `None` | `0` |
| `DB_SSL_MODE` | `auto` | `require` |
| `DB_COMMAND_TIMEOUT` | `30` | `30` |
| `DB_CONNECT_TIMEOUT` | `10` | `5` (plantilla) |
| `DB_MAX_INACTIVE_CONNECTION_LIFETIME` | `300` | `30` |
| `DB_MAX_QUERIES` | `50000` | `1000` |
| `DB_STALE_RETRY_ATTEMPTS` | `1` | `1` |

El pool es un singleton perezoso con doble verificación y lock; **no** se crea
ni se destruye por petición. El modo transacción de Supavisor exige
`statement_cache_size=0`; el código lo aplica automáticamente cuando detecta el
puerto `6543` o `DB_POOL_MODE=transaction`.

### 4.3 Pruebas de regresión añadidas

En `services/ml-api/tests/test_auth_consolidation_m42.py`:

- `test_13`: JWT de estudiante con `user_metadata.role=teacher` y tenant B
  recibe **403 `INSUFFICIENT_PERMISSIONS`** (no escala).
- `test_14`: base inaccesible → **503 `AUTH_BACKEND_UNAVAILABLE`** +
  `Retry-After: 5`.
- `test_15`: JWT válido sin fila en `profiles` → **403
  `IDENTITY_NOT_PROVISIONED`**.
- `test_16`: primera conexión obsoleta, segunda correcta → **200** y exactamente
  dos intentos.

---

## 5. Arquitectura AWS Lambda

### 5.1 Diagrama lógico

```text
Navegador (Cloudflare Worker / Next.js)
        │  HTTPS + Authorization: Bearer <Supabase JWT>
        ▼
Lambda Function URL  (AuthType: NONE, CORS)
        │  evento HTTP v2
        ▼
AWS Lambda  (contenedor linux/amd64)
  ├── AWS Lambda Web Adapter 1.1.0 (extensión)
  │      escucha en :8000 y traduce evento ↔ HTTP
  └── Uvicorn + FastAPI (:8000)
        │  asyncpg, TLS, pool max=1, statement_cache_size=0
        ▼
Supabase Shared Pooler — Transaction Mode (:6543)
        │
        ▼
PostgreSQL 15 + RLS + Auth (GoTrue/JWKS)
```

### 5.2 Decisiones de diseño

| Decisión | Justificación |
|---|---|
| **Lambda Web Adapter**, no Mangum | El servicio ya es una app ASGI estándar; LWA evita adaptar el ciclo de vida, mantiene Uvicorn y permite ejecutar la misma imagen/contenedor localmente. |
| **Function URL `AuthType: NONE`** | La autenticación real la hace FastAPI con el JWT de Supabase en cada request. La Function URL no debe añadir IAM SigV4, que el navegador no puede firmar. |
| **Sin API Gateway** | No se necesita enrutamiento, cuotas por API key ni authorizer adicional. La Function URL cubre el caso y reduce costo/complejidad. Justificación explícita solicitada. |
| **Contenedor de imagen** | Incluye dependencias pesadas (`numpy`, `pandas`, `scikit-learn`) y artefactos ML; el límite de 250 MB de ZIP no es viable. |
| **Contexto de build = raíz del monorepo** | Permite copiar `ml/artifacts` a `/app/ml/artifacts` y reutilizar el paquete Python real. `.dockerignore` excluye `apps/`, `docs/`, `supabase/`, `scripts/`, `packages/`. |
| **Puerto 8000** | El Runtime Interface Emulator de `sam local` usa `8080`; LWA y Uvicorn usan `8000` para evitar colisión. |
| **Pool máximo 1 + concurrencia reservada 5** | Protege el pooler de Supabase: como máximo ~5 conexiones simultáneas en el arranque inicial. |
| **Sin VPC/NAT** | Lambda accede al pooler público de Supabase por TLS; no hay recursos privados que justifiquen VPC. |

### 5.3 Imagen Lambda

`services/ml-api/Dockerfile.lambda`:

- Builder `python:3.11-slim` con `poetry install --only main --no-root`.
- Runtime `python:3.11-slim` + extensión
  `public.ecr.aws/awsguru/aws-lambda-adapter:1.1.0`.
- Copia `/app/.venv`, `app/` y `ml/`.
- `PORT=8000`, `AWS_LWA_PORT=8000`,
  `AWS_LWA_READINESS_CHECK_PATH=/api/v1/health`,
  `MODEL_ARTIFACTS_DIR=/app/ml/artifacts`.
- `CMD exec uvicorn --port=${PORT} --host 0.0.0.0 app.main:app ...` para que
  Uvicorn reciba `SIGTERM` del ciclo de apagado de LWA.
- Imagen resultante: **~712 MB** (muy por debajo del límite de 10 GB de Lambda).
- El `Dockerfile` convencional de blitz.cloud **se mantiene** y solo se le añadió
  el `poetry.lock` opcional al `COPY`.

> **Nota de seguridad:** la imagen Lambda no usa `USER appuser` porque el
> Runtime Interface Emulator de SAM local inyecta binarios en `/var/rapid` y el
> build derivado falla con un usuario no-root. En Lambda el aislamiento es a
> nivel de microVM. Si se exige no-root también en local, debe mantenerse una
> variante de imagen separada para pruebas SAM (ver §10).

### 5.4 Plantilla SAM (`deploy/aws/template.yaml`)

| Elemento | Valor |
|---|---|
| `PackageType` | `Image` |
| `FunctionUrlConfig.AuthType` | `NONE` |
| `ReservedConcurrentExecutions` | `5` (parámetro, 1–100) |
| `MemorySize` | `1024` MB (512–4096) |
| `Timeout` | `30` s (3–60) |
| Arquitectura | `x86_64` |
| CORS Function URL | `AllowOrigins` desde `CorsOrigins`; métodos GET/POST/PUT/PATCH/DELETE; headers `authorization`, `content-type`, `x-idempotency-key`, `x-request-id`; `MaxAge=86400` |
| Permisos | `AmazonEC2ContainerRegistryReadOnly` (pull de ECR) |
| Secretos | `DatabaseUrl`, `SupabaseJwtSecret`, `SupabaseServiceRoleKey` con `NoEcho: true` |

`deploy/aws/ecr.yaml` crea el repositorio con:

- `ScanOnPush: true`.
- Cifrado `AES256`.
- Política de ciclo de vida: conserva las **10** imágenes más recientes.

`deploy/aws/build_and_push.sh` construye `linux/amd64` desde la raíz del
monorepo, autentica contra ECR, publica la etiqueta y muestra el `ImageUri`
exacto para `sam deploy`.

---

## 6. Artefactos y variables requeridas

### 6.1 Archivos nuevos o modificados por este release

| Archivo | Propósito |
|---|---|
| `supabase/migrations/20261109010000_release_mvp_security_hardening.sql` | F-01/F-04/F-05/F-06 |
| `services/ml-api/app/core/auth.py` | Identidad DB-only, 503 fail-closed, reintento de conexión obsoleta |
| `services/ml-api/app/core/config.py` | Variables de pool serverless |
| `services/ml-api/app/content_generation/infrastructure/database.py` | Pool singleton, modo transacción, SSL, reciclado |
| `services/ml-api/app/main.py` | Propagación de cabeceras (`Retry-After`) |
| `services/ml-api/app/prediction/model_registry.py` | Resolución de `ml/artifacts` en contenedor |
| `services/ml-api/Dockerfile.lambda` | Imagen Lambda + LWA |
| `services/ml-api/Dockerfile` | Inclusión opcional de `poetry.lock` |
| `services/ml-api/tests/test_auth_consolidation_m42.py` | Regresiones F-02 |
| `deploy/aws/template.yaml` | Lambda, Function URL, CORS, concurrencia |
| `deploy/aws/ecr.yaml` | Repositorio ECR, escaneo, ciclo de vida |
| `deploy/aws/build_and_push.sh` | Build/push de imagen |
| `deploy/aws/README.md` | Procedimiento operativo |
| `apps/web/.env.lambda.example` | Forma futura de `NEXT_PUBLIC_API_URL` (sin aplicar) |
| `apps/web/.gitignore` | Excepción para versionar `.env.lambda.example` |
| `package.json` | Script raíz `npm test` |
| `.dockerignore` | Contexto de build acotado al monorepo |

### 6.2 Variables de entorno de Lambda

| Variable | Obligatoria | Valor / nota |
|---|---|---|
| `DATABASE_URL` | Sí | Supabase Shared Pooler **Transaction Mode**, puerto **6543**, `sslmode=require` |
| `DB_POOL_MODE` | Sí | `transaction` |
| `DB_POOL_MIN_SIZE` / `DB_POOL_MAX_SIZE` | Sí | `1` / `1` |
| `DB_STATEMENT_CACHE_SIZE` | Sí | `0` |
| `DB_SSL_MODE` | Sí | `require` |
| `SUPABASE_URL` | Sí | URL del proyecto Supabase |
| `SUPABASE_JWKS_URL` | No | Derivada: `${SUPABASE_URL}/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_SECRET` | Solo HS256 | Vacía si el proyecto usa ES256/RS256 con JWKS |
| `SUPABASE_SERVICE_ROLE_KEY` | Solo trabajos de servidor | Nunca se expone al navegador |
| `CORS_ORIGINS` | Sí | Incluye el dominio real de Cloudflare |
| `ENVIRONMENT` | Sí | `production` |
| `REPOSITORY_BACKEND` | Sí | `postgres` |
| `MODEL_ARTIFACTS_DIR` | Sí | `/app/ml/artifacts` |
| `DB_MAX_INACTIVE_CONNECTION_LIFETIME` | Recomendada | `30` |
| `DB_MAX_QUERIES` | Recomendada | `1000` |
| `DB_STALE_RETRY_ATTEMPTS` | Recomendada | `1` |
| `PORT` / `AWS_LWA_PORT` | Sí | `8000` |
| `AWS_LWA_READINESS_CHECK_PATH` | Recomendada | `/api/v1/health` |
| `AWS_LWA_INVOKE_MODE` | Recomendada | `buffered` |

**CORS por defecto** (incluye el frontend real hoy publicado):

```text
https://plataformamicro.fabriziovalerio-c.workers.dev
https://plataformamicro.edu.pe
https://app.plataformamicro.edu.pe
```

El valor es un parámetro SAM (`CorsOrigins`) y se puede ajustar por entorno sin
recompilar la imagen. Debe incluir también las URLs de *preview* de Cloudflare
si se van a probar antes de publicar.

> Esto resuelve el desajuste de CORS señalado como “ACTION NEEDED” en
> `docs/releases/MVP_DEPLOYMENT_OPERATIONS_INVENTORY.md` §1: el dominio real del
> Worker ya está en el valor por defecto, por lo que no es obligatorio
> sobreescribir `CorsOrigins` para el dominio actual (sí para previews).

### 6.3 Frontend

`apps/web/.env.lambda.example` documenta la forma esperada:

```dotenv
NEXT_PUBLIC_API_URL=https://<function-id>.lambda-url.<region>.on.aws
```

**No se aplicó** este valor al Worker. `apps/web/src/lib/api/client.ts` ya
consume `NEXT_PUBLIC_API_URL`; el cambio se hará únicamente en el paso de
publicación coordinada.

---

## 7. Evidencia de validación

Todas las ejecuciones son del **2026-11-12**, en el entorno local del
repositorio. No se usaron credenciales de AWS ni entornos remotos.

### 7.1 Frontend

| Comando | Resultado |
|---|---|
| `npm test` | `# tests 73`, `# pass 73`, `# fail 0` |
| `npm run type-check` | Sin errores (`tsc --noEmit`) |
| `npm run build` | Compilación correcta; 17 rutas generadas; Next.js 14.2.35 |

### 7.2 Backend

| Comando | Resultado |
|---|---|
| `pytest -q` | **273 passed, 2 skipped** |
| `mypy app` | **Success: no issues found in 72 source files** |
| `ruff check app tests` | **All checks passed** |
| `ruff format --check app tests` | 53 archivos se reformatearían, 42 ya formateados (deriva preexistente; no bloqueante, no se aplicó un reformateo masivo) |

### 7.3 Contratos y arquitectura

`python3 scripts/verify-phase0.py`:

| Categoría | Resultado |
|---|---|
| Cat 1–8, 12–14 | Todas aprobadas |
| **Cat 13 — consistencia cruzada SQL/OpenAPI/Python** | **68/68 aprobadas** |
| Cat 9 — guardrail “cero UI” | **Falla preexistente**: el proyecto ya tiene UI en Fase 1 |
| Cat 10 — conteo de tablas | Falla preexistente: 24 tablas frente a 20 esperadas por el script |
| Cat 11 — conteo de endpoints/esquemas | Falla preexistente: 34 endpoints y 65 esquemas frente a 7/10 esperados |
| **Total** | **396/400** |

Las 4 fallas son guardrails obsoletos de Fase 0, no regresiones de este release:
el propio Cat 13 (contratos) pasa completo. No se “ajustaron” los números del
script para ocultar la deriva.

### 7.4 RLS, ACL y trigger (Supabase local real)

- Matriz de dos tenants y múltiples secciones: ver §3.5.
- `PATCH` propio `{"full_name": ...}` → **204**.
- `PATCH` propio `{"role": "admin"}` → **403 `42501`**.
- `POST` de perfil → **403 `42501`**.
- `DELETE` de perfil → **403 `42501`**.
- Actualización anónima → **401**.
- Sesión `authenticated` sin `sub` que intenta cambiar `role` →
  **error `42501`** con el mensaje de F-06; `ROLLBACK` aplicado.
- `service_role` conserva sus privilegios de servidor.
- Fixtures eliminados; base local restaurada a `1/1/10/11`.

### 7.5 Imagen Lambda y SAM

| Paso | Resultado |
|---|---|
| `docker build --platform linux/amd64 -f services/ml-api/Dockerfile.lambda -t nexo-ml-api-lambda:final .` | **Successfully tagged** (~712 MB) |
| `sam validate --lint` (`template.yaml`) | **valid SAM Template** |
| `sam validate --lint` (`ecr.yaml`) | **valid SAM Template** |
| `sam build --template-file deploy/aws/template.yaml` | **Build Succeeded**; imagen `mlapifunction:mvp-local` |
| `sam local invoke` health (DB inaccesible) | **200** `{"status":"ok","service":"ml-api"}` |
| `sam local invoke` estudiante `/api/v1/students/me/courses` | **200** con curso/sección reales |
| `sam local invoke` docente `/api/v1/activities` | **200** con actividades reales |
| JWT de estudiante con metadata de docente | **403 `INSUFFICIENT_PERMISSIONS`** |
| JWT válido + base inaccesible | **503 `AUTH_BACKEND_UNAVAILABLE`**, `retry-after: 5` |
| Preflight CORS con origen real de Cloudflare | **200**, `access-control-allow-origin: https://plataformamicro.fabriziovalerio-c.workers.dev` |

La ruta local validada es `sam local invoke` con un evento **Function URL v2**.
`sam local start-api` no aplica porque la función no declara `Events` REST: su
único ingreso es la Function URL. SAM inicia su RIE en `8080`; por eso la
aplicación y LWA escuchan en `8000`.

> La duración de ~2,4 s observada en `sam local invoke` incluye el arranque del
> contenedor y de la aplicación en este host. **No** es una medición de cold
> start de AWS Lambda y no debe citarse como tal.

---

## 8. Costos, límites y capacidad operativa

### 8.1 Límites configurados

| Recurso | Valor | Comentario |
|---|---:|---|
| Memoria | 1024 MB | Parámetro SAM (512–4096) |
| Timeout | 30 s | Parámetro SAM (3–60) |
| Concurrencia reservada | 5 | Protección inicial del pooler |
| Pool DB por entorno de ejecución | 1 | `DB_POOL_MAX_SIZE=1` |
| Conexiones simultáneas estimadas | ≤ 5 | Derivado de concurrencia × pool (no medido en AWS) |
| Imágenes ECR retenidas | 10 | Política de ciclo de vida |
| Tamaño de imagen | ~712 MB | Límite Lambda: 10 GB |
| Payload Function URL (buffered) | 6 MB | Límite de AWS |
| `/tmp` de Lambda | 512 MB por defecto | No se usa almacenamiento temporal persistente |

### 8.2 Factores de costo

El costo mensual depende de cuatro componentes y **no se presenta una cifra
monetaria** porque no hay cuenta/cotización de AWS disponible y los precios
varían por región y fecha:

1. **Invocaciones**: número de requests × precio por millón.
2. **GB-segundo**: `memoria_GB × duración_segundo × invocaciones`.
   Con 1024 MB y ~2,4 s locales, cada request “fría” es ~2,4 GB-s; las
   invocaciones calientes son mucho menores.
3. **ECR**: almacenamiento de las imágenes retenidas + transferencia de salida.
4. **CloudWatch Logs**: volumen de logs; conviene fijar retención (p. ej. 14–30
   días) al crear el stack o después.

Además, Supabase tiene su propio costo/plan y límite de conexiones. El diseño
`pool max=1` + `ReservedConcurrency=5` es deliberadamente conservador para no
agotar el pooler durante la validación.

### 8.3 Límites operativos relevantes

- **Cold start**: LWA añade una comprobación de *readiness*; el arranque de
  FastAPI + carga de artefactos ML puede tardar. La primera invocación tras un
  *freeze* puede ser más lenta; el reintento de conexión obsoleta está diseñado
  para ese escenario.
- **Supavisor Transaction Mode**: no admite *prepared statements* persistentes;
  por eso `statement_cache_size=0` es obligatorio.
- **Function URL**: no ofrece WAF, API keys ni *throttling* por ruta. La
  protección es JWT + RLS + concurrencia reservada.
- **CORS**: la Function URL y FastAPI deben tener orígenes coherentes; un
  *preview* de Cloudflare con otra URL será bloqueado si no se agrega.
- **JWT**: si el proyecto remoto usa ES256/JWKS (así lo indica el inventario
  operativo), `SUPABASE_JWT_SECRET` debe quedar vacío; un secreto HS256
  incorrecto rompería la validación.

---

## 9. Runbook de publicación coordinada

> **Este runbook no se ejecutó.** Requiere autorización explícita, credenciales
> de AWS y acceso al Supabase remoto.

### Paso 0 — Revisión y commit (pendiente de autorización)

1. Revisar el diff completo de la rama `release/mvp-aws-lambda`.
2. Confirmar que los cambios preexistentes de `apps/web/` no se mezclan con este
   release si no corresponde.
3. Crear el commit de release y abrir PR **sin** hacer merge a `main` todavía.

### Paso 1 — Respaldo remoto

- Snapshot/backup del esquema y datos del proyecto Supabase de producción.
- Exportar el estado actual de políticas RLS y ACL de `profiles`, `sections`,
  `enrollments`.

### Paso 2 — Migraciones remotas (solo las pendientes)

Aplicar en orden, sin editar migraciones históricas:

1. `20261109000000_profiles_privilege_hardening.sql`
2. `20261109010000_release_mvp_security_hardening.sql`

Verificar después:

```sql
SELECT policyname, cmd FROM pg_policies
WHERE schemaname = 'public' AND tablename IN ('sections', 'profiles');
```

Resultado esperado: `sections_select_scoped`, `profiles_select_own`,
`profiles_select_teacher_students`, `profiles_select_admin_scope` y
`profiles_update_own`. No debe existir `sections_select_all` ni
`profiles_select_own_or_same_tenant`.

### Paso 3 — Certificación RLS en remoto

Repetir la matriz de dos tenants descrita en §3.5 **contra el entorno remoto**
con JWT reales. No se debe certificar RLS de producción usando solo el entorno
local.

### Paso 4 — ECR e imagen

```bash
export AWS_REGION=us-east-2          # co-ubicación recomendada con Supabase
export IMAGE_TAG="mvp-$(git rev-parse --short HEAD)"
./deploy/aws/build_and_push.sh
```

Opcional: desplegar primero `deploy/aws/ecr.yaml` como stack independiente.

### Paso 5 — Stack SAM

```bash
sam deploy \
  --template-file deploy/aws/template.yaml \
  --stack-name nexo-mvp-ml-api \
  --region "$AWS_REGION" \
  --capabilities CAPABILITY_IAM \
  --resolve-s3 \
  --parameter-overrides \
    ImageUri="<account>.dkr.ecr.${AWS_REGION}.amazonaws.com/nexo-mvp-ml-api:${IMAGE_TAG}" \
    DatabaseUrl="postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require" \
    SupabaseUrl="https://oqjahhbqcethwgpufgnm.supabase.co" \
    SupabaseJwtSecret="" \
    CorsOrigins="https://plataformamicro.fabriziovalerio-c.workers.dev,https://plataformamicro.edu.pe,https://app.plataformamicro.edu.pe" \
    ReservedConcurrency=5
```

Preferir **AWS Secrets Manager / SSM Parameter Store** para
`DatabaseUrl` y `SupabaseServiceRoleKey` en lugar de pasarlos por CLI.

### Paso 6 — Verificación en AWS

```bash
sam list stack-outputs --stack-name nexo-mvp-ml-api --region "$AWS_REGION"
curl -i "<FunctionUrl>api/v1/health"
```

Comprobaciones mínimas:

- Health → `200`.
- Sin JWT en endpoint protegido → `401`.
- JWT de estudiante en endpoint docente → `403`.
- JWT válido + base inaccesible (prueba controlada) → `503` +
  `Retry-After: 5`.
- Preflight CORS desde el dominio real de Cloudflare → `200` con el
  `Access-Control-Allow-Origin` correcto.
- Revisar métricas de Lambda: errores, duración p50/p95, *concurrent
  executions*, *throttles*.
- Revisar conexiones del pooler en Supabase.

### Paso 7 — Cloudflare (solo tras validar Lambda)

1. En el Worker `plataformamicro`, definir
   `vars.NEXT_PUBLIC_API_URL = <FunctionUrl>` (sin barra final).
2. Redesplegar el Worker.
3. Verificar login, dashboard, cursos, quiz y recomendaciones.
4. **Rollback inmediato**: quitar `NEXT_PUBLIC_API_URL` y redesplegar; el
   frontend vuelve al modo de resiliencia contra Supabase sin tocar datos.

### Paso 8 — Observación

- Ventana sugerida: 24–48 h con `ReservedConcurrency=5`.
- Revisar `5xx`, `429`, latencia y conexiones del pooler.
- Incrementar concurrencia solo con medición previa de conexiones.

### Rollback de base de datos

La migración es aditiva en funciones y políticas, pero **elimina** políticas
anteriores y revoca privilegios. No se debe aplicar un “down” ciego:

1. Restaurar el backup del Paso 1 si hay que volver al estado previo.
2. Si se necesita un rollback parcial, recrear las políticas desde
   `20261106000000_fix_rls_select_policies.sql` de forma consciente y **sin**
   volver a conceder UPDATE de tabla completa ni INSERT/DELETE a clientes.
3. Las funciones `is_enrolled_in_section` y el trigger endurecido pueden
   permanecer: son compatibles con el estado anterior.

---

## 10. Riesgos residuales y pendientes

| ID | Riesgo / pendiente | Severidad | Estado | Mitigación |
|---|---|---|---|---|
| F-03 | Un access token sigue siendo válido tras el logout hasta su expiración | Media | **Aceptado temporalmente** | TTL corto del JWT; a futuro, comprobación de sesión/revocación en FastAPI. No se modificó el contrato en este release. |
| F-07 | No existe administración por JWT de cliente | Informativa | **Limitación funcional** | Operaciones administrativas vía `service_role`/backoffice. Si se requiere desde la web, diseñar RPC `SECURITY DEFINER` auditada. |
| R-01 | Migraciones no aplicadas en Supabase remoto | Alta | **Pendiente** | Paso 2 del runbook + certificación RLS remota (Paso 3). |
| R-02 | Sin credenciales AWS: no hay deploy real ni Function URL | Alta | **Bloqueado** | Autenticar AWS CLI/SAM y ejecutar Pasos 4–6. |
| R-03 | Sin staging remoto: RLS solo certificada en local | Alta | **Pendiente** | Repetir matriz con JWT reales en remoto antes de publicar. |
| R-04 | `NEXT_PUBLIC_API_URL` no actualizado en Cloudflare | Media | **Intencional** | Cambio coordinado en Paso 7, con rollback inmediato. |
| R-05 | Imagen Lambda corre como root en el contenedor | Baja | **Aceptado** | Aislamiento de microVM en Lambda; si se exige no-root, usar una variante de imagen solo para SAM local. |
| R-06 | 4 guardrails obsoletos de Fase 0 | Baja | **Preexistente** | Documentado; Cat 13 de contratos pasa. No se alteró el script para ocultarlo. |
| R-07 | Deriva de `ruff format` (53 archivos) | Baja | **Preexistente** | No se aplicó reformateo masivo para no contaminar el diff del release. |
| R-08 | Costo real de AWS desconocido | Media | **Sin datos** | No hay cuenta/cotización; monitorear tras el deploy y fijar retención de logs. |
| R-09 | CORS de *previews* de Cloudflare | Media | **Pendiente** | Agregar cada URL de preview a `CorsOrigins` o probar solo desde el dominio de producción. |
| R-10 | `SUPABASE_JWT_SECRET` incorrecto en proyecto ES256 | Alta | **Pendiente de verificación** | Dejar vacío y confiar en JWKS; validar `iss`/`aud` con un token real antes de publicar. |

### 10.1 Lo que este release **no** certifica

- No certifica el comportamiento de AWS Lambda real (cold start, límites de
  concurrencia, latencia de red al pooler).
- No certifica el esquema/datos de producción.
- No certifica que las migraciones pendientes se puedan aplicar sin conflicto
  en remoto; el inventario operativo reporta discrepancias de historial.
- No certifica el frontend contra la Function URL; eso ocurre en el Paso 7.

---

## 11. Conclusión

El release deja el repositorio en un estado **desplegable y verificable**:

- Los bloqueantes F-01/F-02/F-04/F-05/F-06 están corregidos y cubiertos por
  pruebas y validación real contra PostgreSQL/Supabase local.
- FastAPI falla de forma cerrada cuando no puede verificar identidad y no
  acepta claims como respaldo.
- La imagen Lambda, la plantilla SAM y el repositorio ECR están listos, con
  puerto, CORS, pooling y concurrencia ajustados al entorno serverless.
- El frontend actual **no** fue modificado en su configuración de producción.

**No se publicó nada.** El siguiente paso requiere autorización explícita para
commit/push y credenciales de AWS/Supabase remoto, seguido del runbook de §9.

---

## Anexo A — Comandos reproducibles (local)

```bash
# Frontend
cd /root/PlataformaMicro
npm test
npm run type-check
npm run build

# Backend
cd services/ml-api
.venv/bin/python -m pytest -q
.venv/bin/python -m mypy app
.venv/bin/python -m ruff check app tests

# Contratos
cd /root/PlataformaMicro
python3 scripts/verify-phase0.py

# Imagen Lambda
docker build --platform linux/amd64 \
  -f services/ml-api/Dockerfile.lambda \
  -t nexo-ml-api-lambda:local .

# SAM
sam validate --lint --template-file deploy/aws/template.yaml
sam build --template-file deploy/aws/template.yaml --build-dir /tmp/sam-build
sam local invoke MlApiFunction \
  --template-file /tmp/sam-build/template.yaml \
  --event /tmp/lambda-health-event.json \
  --skip-pull-image \
  --parameter-overrides \
    DatabaseUrl="postgresql://postgres:postgres@172.17.0.1:54322/postgres"
```

Para el entorno local con Supabase en Docker se usa
`172.17.0.1:54322`, `DB_SSL_MODE=disable` y `DB_POOL_MODE=session`. Esos valores
**no** forman parte de la plantilla desplegada; producción usa el pooler
`6543` con TLS.

## Anexo B — Evidencia y artefactos temporales

- Matriz RLS: `/tmp/opencode/rls_matrix.txt`.
- Eventos Function URL v2: `/tmp/opencode/event-*.json`,
  `/tmp/opencode/lambda-health-event.json`.
- Salida de contratos: `/tmp/opencode/verify0.out`, `/tmp/opencode/verify0.err`.
- Plantilla construida: `/tmp/opencode/sam-build/template.yaml`.
- Informe de seguridad origen:
  `docs/security/2026-11-09/P0.1_SECURITY_VALIDATION_REPORT.md`.
- Inventario operativo:
  `docs/releases/MVP_DEPLOYMENT_OPERATIONS_INVENTORY.md`.

Ninguno de estos artefactos temporales se versionó.
