# PlataformaMicro — Inventario Operativo y Plan de Publicación Coordinada

> **Documento:** Auditoría de Infraestructura y Preparación de Despliegue  
> **Servicios:** Cloudflare Workers + AWS Lambda (FastAPI) + Supabase PostgreSQL  
> **Repositorio:** `https://github.com/TF4ir/PlataformaMicro`  
> **Rama de trabajo activa (OpenCode):** `release/mvp-aws-lambda`  
> **Rama remota de producción:** `main`  
> **Frontend publicado actualmente:** `https://plataformamicro.fabriziovalerio-c.workers.dev`  
> **Modo de ejecución:** Auditoría de solo lectura (Read-Only). Cero modificaciones a código, contenedores, migraciones o servicios en la nube.

---

## 1. Resumen Ejecutivo del Estado Operativo

| Proveedor / Componente | Estado Operativo | Diagnóstico Técnico | Acción Requerida Pre-Despliegue |
| :--- | :---: | :--- | :--- |
| **Cloudflare Workers** (Frontend Web) | `ONLINE` | Worker activo en `https://plataformamicro.fabriziovalerio-c.workers.dev`. Sirve Next.js 14.2 vía `@opennextjs/cloudflare`. `NEXT_PUBLIC_API_URL` ausente (opera en fallback directo contra Supabase). | Actualizar `vars.NEXT_PUBLIC_API_URL` con la Function URL de AWS Lambda una vez desplegada. |
| **Supabase Remoto** (Base de Datos & Auth) | `ONLINE` | Instancia `oqjahhbqcethwgpufgnm` activa en AWS `us-east-2`. Auth GoTrue v2.197.0 operativo con tokens asimétricos ES256 (JWKS). 26 tablas creadas. | Aplicar migraciones correctivas pendientes (`20261109000000` y `20261109010000`) para desbloquear lectura de secciones y proteger perfiles. |
| **AWS CLI & SAM** (Herramientas Locales) | `NOT CONFIGURED` | Ni AWS CLI ni SAM CLI se encuentran instalados en el entorno de desarrollo. No existen credenciales activas en `~/.aws`. | El usuario debe ejecutar el procedimiento de configuración manual de AWS CLI / SAM documentado en este informe. |
| **AWS ECR & Lambda** (Infraestructura Remota) | `PENDING CREATION` | Plantillas SAM e imagen `Dockerfile.lambda` preparadas por OpenCode. A la espera de que el usuario autentique AWS para crear el repositorio ECR y desplegar la pila. | Ejecutar `sam deploy` en la región `us-east-2` tras la consolidación de código de OpenCode. |
| **Compatibilidad Cruzada** | `ACTION NEEDED` | Parámetro `CorsOrigins` en `template.yaml` no incluye `https://plataformamicro.fabriziovalerio-c.workers.dev` por defecto. Si no se sobreescribe, el navegador bloqueará las peticiones de la UI. | Inyectar el dominio real de Cloudflare en `CorsOrigins` durante el despliegue de Lambda. |

---

## 2. FASE 1 — Auditoría Detallada de Cloudflare Workers

### 2.1 Identificación y Configuración del Worker

* **Nombre del Worker:** `plataformamicro` (definido en `apps/web/wrangler.jsonc`).
* **URL Pública Activa:** `https://plataformamicro.fabriziovalerio-c.workers.dev`.
* **Subdominio de Cuenta Cloudflare:** `fabriziovalerio-c.workers.dev`.
* **Repositorio Git Conectado:** `https://github.com/TF4ir/PlataformaMicro`.
* **Rama configurada para producción:** `main`. (En el repositorio remoto de GitHub `origin` únicamente existe la rama `main`).
* **Último Commit Desplegado:** Commit `415027069981a5addd89b15de0fa828fdcc90e7b` (*"fix(ci): isolate npm cache in .npmrc and synchronize typescript 5.9.3 dependency to fix EINTEGRITY"*), correspondiente al Build ID remoto `FTPYhJa09YwDAk7HEQIFQ`.
* **Fecha del último despliegue:** Viernes 6 de noviembre de 2026 (~01:26 - 04:18 UTC).
* **Motor y Versión de Wrangler:** Wrangler `4.158.0` (`@opennextjs/cloudflare` `^1.20.16`).

### 2.2 Pipeline de Construcción y Artefactos

* **Comando de Instalación:** `npm ci` (optimizado mediante `.npmrc` con aislamiento de cache).
* **Comando de Build:** `npm --prefix apps/web run build:cloudflare` (ejecuta internamente `opennextjs-cloudflare build --dangerouslyUseUnsupportedNextVersion`).
* **Directorio Raíz de la Aplicación (Monorepo):** `/` (raíz del repositorio).
* **Directorio de la Aplicación Web:** `apps/web`.
* **Directorio de Salida de OpenNext:** `apps/web/.open-next/`.
  * Script del Worker generado: `apps/web/.open-next/worker.js`.
  * Activos estáticos cliente: `apps/web/.open-next/assets/`.
* **Compatibility Date:** `2024-12-30`.
* **Compatibility Flags:** `["nodejs_compat"]`.

### 2.3 Variables de Entorno en el Worker

Inspección de variables declaradas en `apps/web/wrangler.jsonc`:

| Nombre de Variable | Clasificación | Presencia Actual | Propósito / Valor No Sensible |
| :--- | :---: | :---: | :--- |
| `NEXT_PUBLIC_SUPABASE_URL` | Pública | **Presente** | `https://oqjahhbqcethwgpufgnm.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Pública | **Presente** | Clave publicable Supabase (`sb_publishable_...`) |
| `NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY` | Pública | **Presente** | Clave publicable Supabase (`sb_publishable_...`) |
| `NEXT_PUBLIC_ENABLE_DEMO_AUTH` | Pública | **Presente** | `"true"` (habilita selector y credenciales de demo) |
| `NEXT_PUBLIC_API_URL` | Pública | **AUSENTE** | **No configurada**. Causa fallback automático en la UI. |

### 2.4 Comportamiento de `NEXT_PUBLIC_API_URL` y Fallback de Resiliencia

El frontend Next.js evalúa el backend en `apps/web/src/lib/api/client.ts`:
1. `API_BASE_URL` toma el valor de `process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"`.
2. Al estar en producción bajo protocolo `https://` y no tener configurada la variable, `API_BASE_URL` apunta a `http://localhost:8000`.
3. La función `isBackendConfigured()` detecta la discrepancia de protocolo seguro frente a localhost y devuelve `false`.
4. El cliente de Next.js (`apps/web/src/lib/api/teacher.ts`) activa el **modo de resiliencia**, ejecutando lecturas y escrituras directamente sobre Supabase mediante `@supabase/ssr` / `@supabase/supabase-js`, evitando errores de *Mixed Content* o *Failed to fetch*.

### 2.5 Deployments de Preview en Cloudflare

* Si el usuario empuja ramas no productivas a GitHub (por ejemplo, `release/mvp-aws-lambda`), Cloudflare Workers Builds generará despliegues de Preview con dominios del tipo:  
  `https://<hash-o-rama>.plataformamicro.fabriziovalerio-c.workers.dev`.
* **Advertencia crítica para AWS Lambda:** Cualquier Preview generado bajo una URL distinta a la de producción fallará con errores de CORS al intentar comunicarse con la Lambda Function URL, a menos que el parámetro `CorsOrigins` de Lambda contenga dicha URL explícita o se gestione un comodín.

---

## 3. FASE 2 — Auditoría Detallada de Supabase Remoto

### 3.1 Identificación de Proyecto y Conectividad

* **Estado de Sesión Supabase CLI:** No autenticado localmente (`AccessTokenRequiredError`). El comando `supabase projects list` requiere token.
* **Estado de Enlace (`supabase link`):** No vinculado en el entorno local (`ProjectRefNotLinkedError`).
* **Project Reference:** `oqjahhbqcethwgpufgnm`.
* **Project URL:** `https://oqjahhbqcethwgpufgnm.supabase.co`.
* **Región Geográfica Subyacente:** **`us-east-2` (AWS Ohio)**.
  * *Método de verificación empírica:* Resolución de registro AAAA IPv6 para el endpoint directo de base de datos `db.oqjahhbqcethwgpufgnm.supabase.co` (`2600:1f16:1482:9402:4ffa:c5c0:366:7ecc`), cotejado contra el catálogo oficial de rangos IP de AWS (`ip-ranges.json`), arrojando pertenencia inequívoca al bloque `2600:1f16::/34` asignado a `us-east-2`.
* **Supabase Shared Pooler (Supavisor):**
  * Hostname: `aws-0-us-east-2.pooler.supabase.com`.
  * Puerto Transaction Mode: `6543` (verificado TCP Socket Connect exitoso en 3 ms).
  * Puerto Session Mode: `5432`.
  * Usuario Pooler: `postgres.oqjahhbqcethwgpufgnm`.

### 3.2 Estado de Auth (GoTrue) y Validación Criptográfica

* **Versión del Servicio Auth:** GoTrue `v2.197.0` (verificado en `/auth/v1/health`).
* **Algoritmo de Emisión de Tokens:** **`ES256`** (curva elíptica P-256 asimétrica).
* **Endpoint JWKS:** `https://oqjahhbqcethwgpufgnm.supabase.co/auth/v1/.well-known/jwks.json`.
* **Key ID (`kid`) Activo:** `69f5191a-7040-4abe-8bde-14380c22d1bb`.
* **Prueba de Autenticación en Vivo:**
  * Endpoint probado: `POST /auth/v1/token?grant_type=password`.
  * Cuenta de prueba: Docente pre-provisionada (`ana.garcia@nexo.edu.pe`).
  * Resultado: **HTTP 200 OK**. Emisión de JWT válido con firma ES256, `aud: authenticated`, `sub: d0000000-0000-0000-0000-000000000001`.
  * La base remota resolvió satisfactoriamente el error previo 500 (`Database error querying schema`).

### 3.3 Inventario de Esquema y Tablas Remotas

Las 26 tablas definidas en la arquitectura del sistema existen en el esquema `public` de la base remota y responden correctamente a través del API PostgREST:

```
tenants                         [OK - HTTP 200]
profiles                        [OK - HTTP 200]
auth_recovery_pins              [OK - HTTP 200]
courses                         [OK - HTTP 200]
sections                        [OK - HTTP 200]
enrollments                     [OK - HTTP 200]
units                           [OK - HTTP 200]
knowledge_components           [OK - HTTP 200]
microcontents                   [OK - HTTP 200]
questions                       [OK - HTTP 200]
question_options                [OK - HTTP 200]
activities                      [OK - HTTP 200]
activity_questions              [OK - HTTP 200]
quiz_attempts                   [OK - HTTP 200]
answer_events                   [OK - HTTP 200] (Append-Only Event Store)
student_knowledge_states        [OK - HTTP 200]
student_metrics                 [OK - HTTP 200]
model_versions                  [OK - HTTP 200]
predictions                     [OK - HTTP 200]
recommendations                 [OK - HTTP 200]
review_assignments              [OK - HTTP 200]
content_generation_jobs         [OK - HTTP 200]
question_drafts                 [OK - HTTP 200]
notifications                   [OK - HTTP 200]
activity_sections               [OK - HTTP 200]
content_exposure_events         [OK - HTTP 200] (Append-Only Event Store)
```

### 3.4 Historial y Discrepancias de Migraciones

| Archivo de Migración Local | Estado en Remoto | Diagnóstico & Evidencia |
| :--- | :---: | :--- |
| `20261102000000_initial_schema.sql` | **APLICADO** | Tablas base y tipos ENUM operativos. |
| `20261102180000_content_generation_quizzes_notifications.sql` | **APLICADO** | Columnas y tablas de generación presentes. |
| `20261103000000_content_generation_leases_and_idempotency.sql` | **APLICADO** | Columnas de lease en jobs presentes. |
| `20261103010000_content_generation_hardening.sql` | **APLICADO** | Restricciones de integridad activas. |
| `20261103020000_teacher_question_editor_m3.sql` | **APLICADO** | Campos extendidos de editor de reactivos. |
| `20261103030000_learning_flow_and_answer_events_m4.sql` | **APLICADO** | Esquema append-only en `answer_events`. |
| `20261103040000_content_exposure_events_m52.sql` | **APLICADO** | Tabla de exposición a microcontenidos activa. |
| `20261103050000_recommendations_and_predictions_m53.sql` | **APLICADO** | Tablas de inferencia y recomendaciones activas. |
| `20261106000000_fix_rls_select_policies.sql` | **NO APLICADO** | Introducía `sections_select_all`. No llegó a aplicarse al detectarse recursión infinita con `enrollments`. |
| `20261109000000_profiles_privilege_hardening.sql` | **PENDIENTE** | Diseñado por OpenCode. Revoca UPDATE en `profiles` a columnas no sensibles (`full_name`, `avatar_url`) y añade trigger `prevent_profile_privilege_escalation`. |
| `20261109010000_release_mvp_security_hardening.sql` | **PENDIENTE** | Diseñado por OpenCode. Soluciona recursión RLS en `sections` mediante función SECURITY DEFINER `is_enrolled_in_section(UUID)`, reemplaza `profiles_select_own_or_same_tenant` por lectura de menor privilegio y revoca permisos innecesarios. |

> **Hallazgo Crítico de Auditoría:**  
> Al realizar una consulta autenticada con el usuario docente `ana.garcia@nexo.edu.pe` hacia `/rest/v1/sections?select=*`, la base remota devuelve `[]` (0 filas) a pesar de existir secciones cargadas en la BD. Esto ocurre porque la política SELECT en `sections` aún no ha sido aplicada en el servidor remoto. La aplicación de la migración `20261109010000_release_mvp_security_hardening.sql` resolverá este bloqueo de forma definitiva.

### 3.5 Almacenamiento (Supabase Storage)

* Bucket registrado en migraciones: `teacher-materials`.
* Visibilidad: `public = false` (privado).
* Límite de archivo: 30 MB (`31457280` bytes).
* Tipos MIME admitidos: `application/pdf`, `application/vnd.openxmlformats-officedocument.presentationml.presentation`.
* Acceso: Exclusivo mediante token autenticado de docentes o `service_role`.

---

## 4. FASE 3 — Auditoría de Entorno AWS

### 4.1 Comprobaciones de Herramientas Locales

* **AWS CLI:** `aws` no se encuentra en el `$PATH` del sistema (código 127).
* **AWS SAM CLI:** `sam` no se encuentra en el `$PATH` del sistema (código 127).
* **Directorio de Configuración:** `/root/.aws` existe como enlace simbólico hacia `/mnt/c/Users/Usuario/.aws`, pero está totalmente vacío (sin archivos `credentials` ni `config`).
* **Variables de Entorno AWS:** Comprobación `[k for k in os.environ if 'AWS' in k]` arrojó `[]`. No existen claves de acceso inyectadas en la sesión.
* **Estado de Docker:** Docker v29.1.3 operativo en el host linux/amd64 (apto para construir imágenes de contenedor).

### 4.2 Procedimiento Manual de Configuración para el Usuario

Dado que este agente opera en modo de solo lectura y no almacena credenciales privadas, el usuario debe ejecutar los siguientes pasos en su terminal:

```bash
# 1. Instalar AWS CLI v2 en Ubuntu/Debian (si no se encuentra disponible)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip -q awscliv2.zip
sudo ./aws/install
rm -rf awscliv2.zip aws

# 2. Instalar AWS SAM CLI
wget -q https://github.com/aws/aws-sam-cli/releases/latest/download/aws-sam-cli-linux-x86_64.zip
unzip -q aws-sam-cli-linux-x86_64.zip -d sam-installation
sudo ./sam-installation/install
rm -rf aws-sam-cli-linux-x86_64.zip sam-installation

# 3. Configurar perfil y credenciales (usar la región us-east-2 para co-ubicación con Supabase)
aws configure
# AWS Access Key ID [None]: <INGRESAR_ACCESS_KEY>
# AWS Secret Access Key [None]: <INGRESAR_SECRET_KEY>
# Default region name [None]: us-east-2
# Default output format [None]: json

# 4. Verificar la identidad autenticada
aws sts get-caller-identity
```

### 4.3 Matriz de Permisos IAM Mínimos para Despliegue SAM

La identidad IAM del usuario debe contar con los siguientes permisos para poder ejecutar la creación de infraestructura:

1. **Amazon ECR:** `ecr:CreateRepository`, `ecr:DescribeRepositories`, `ecr:GetAuthorizationToken`, `ecr:BatchCheckLayerAvailability`, `ecr:PutImage`, `ecr:InitiateLayerUpload`, `ecr:UploadLayerPart`, `ecr:CompleteLayerUpload`.
2. **AWS CloudFormation:** `cloudformation:CreateChangeSet`, `cloudformation:ExecuteChangeSet`, `cloudformation:DescribeStacks`, `cloudformation:GetTemplateSummary`, `cloudformation:DescribeStackEvents`.
3. **AWS IAM:** `iam:CreateRole`, `iam:AttachRolePolicy`, `iam:PassRole`, `iam:GetRole`, `iam:DeleteRole`, `iam:DetachRolePolicy` (para el rol de ejecución de Lambda).
4. **AWS Lambda:** `lambda:CreateFunction`, `lambda:UpdateFunctionCode`, `lambda:UpdateFunctionConfiguration`, `lambda:CreateFunctionUrlConfig`, `lambda:AddPermission`, `lambda:GetFunction`, `lambda:PutFunctionConcurrency`.
5. **Amazon S3:** Acceso a bucket de despliegue SAM (`--resolve-s3` o bucket existente).

### 4.4 Inventario de Archivos SAM Preparados en el Repositorio

* `deploy/aws/template.yaml`: Plantilla SAM sin API Gateway ni ALB. Utiliza **AWS Lambda Function URL** (`AuthType: NONE`) y **AWS Lambda Web Adapter 1.1.0**.
* `deploy/aws/ecr.yaml`: Plantilla para el repositorio ECR `nexo-mvp-ml-api` con escaneo automático de vulnerabilidades y retención de últimas 10 imágenes.
* `services/ml-api/Dockerfile.lambda`: Imagen optimizada basada en `python:3.11-slim`, con el binario `/opt/extensions/lambda-adapter`, usuario no-root `appuser` y contexto en la raíz del repositorio para incluir `/app/ml/artifacts`.
* `deploy/aws/build_and_push.sh`: Script parametrizado para autenticación en ECR, construcción linux/amd64 y etiquetado con SHA de git.

---

## 5. FASE 4 — Matriz de Compatibilidad Entre Proveedores

```text
┌───────────────────────────────────────────────┐
│              Cloudflare Workers               │
│  plataformamicro.fabriziovalerio-c.workers.dev │
│           Next.js 14.2 (OpenNext)             │
└───────────────────────┬───────────────────────┘
                        │
                        │ HTTPS Fetch + Bearer JWT
                        │ Header: X-Idempotency-Key
                        ▼
┌───────────────────────────────────────────────┐
│            AWS Lambda Function URL            │
│       https://<func-id>.on.aws (Auth: NONE)   │
│             Region: us-east-2                 │
├───────────────────────────────────────────────┤
│          AWS Lambda Web Adapter 1.1.0         │
│          FastAPI (Uvicorn puerto 8080)        │
│          Model Artifacts (/app/ml/artifacts)  │
└───────────────────────┬───────────────────────┘
                        │
                        │ PostgreSQL Protocol (asyncpg)
                        │ TLS/SSL Strict (sslmode=require)
                        ▼
┌───────────────────────────────────────────────┐
│           Supabase Managed Platform           │
│             Region: us-east-2                 │
├───────────────────────────────────────────────┤
│  1. Supavisor Pooler (Puerto 6543 Tx Mode)    │
│  2. PostgreSQL 15+ (26 tablas con RLS)        │
│  3. GoTrue Auth (JWKS ES256 / Public Keys)    │
│  4. Supabase Storage (teacher-materials)      │
└───────────────────────────────────────────────┘
```

### 5.1 Parámetros de Integración y Mapeo de Variables

| Variable | Dónde se define | Tipo | Descripción y Restricción Técnica |
| :--- | :--- | :---: | :--- |
| `NEXT_PUBLIC_API_URL` | Cloudflare Worker (`vars`) | Pública | Function URL de AWS Lambda (ej. `https://<id>.lambda-url.us-east-2.on.aws`). **Debe terminar sin slash.** |
| `NEXT_PUBLIC_SUPABASE_URL` | Cloudflare Worker (`vars`) | Pública | `https://oqjahhbqcethwgpufgnm.supabase.co` |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Cloudflare Worker (`vars`) | Pública | `sb_publishable_u5AIwepBNqqKzQPxVtg5QQ_d_IQ3yrX` |
| `CorsOrigins` | AWS SAM (`Parameters`) | Config | **Obligatorio incluir:** `https://plataformamicro.fabriziovalerio-c.workers.dev`. |
| `DATABASE_URL` | AWS Lambda (`Environment`) | **SECRETO** | `postgresql://postgres.oqjahhbqcethwgpufgnm:<PASS>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require` |
| `DB_POOL_MODE` | AWS Lambda (`Environment`) | Config | `transaction` |
| `DB_STATEMENT_CACHE_SIZE` | AWS Lambda (`Environment`) | Config | `0` (**MANDATORIO:** Supavisor en Transaction Mode falla con prepared statements). |
| `DB_POOL_MIN_SIZE` / `MAX_SIZE` | AWS Lambda (`Environment`) | Config | `1` / `1` (evita agotar el pooler durante picos de concurrencia). |
| `SUPABASE_URL` | AWS Lambda (`Environment`) | Pública | `https://oqjahhbqcethwgpufgnm.supabase.co` |
| `SUPABASE_JWKS_URL` | AWS Lambda (`Environment`) | Pública | `https://oqjahhbqcethwgpufgnm.supabase.co/auth/v1/.well-known/jwks.json` |
| `SUPABASE_JWT_SECRET` | AWS Lambda (`Environment`) | **SECRETO** | Dejar vacío `""` (Supabase utiliza JWKS ES256 asimétrico). |
| `SUPABASE_SERVICE_ROLE_KEY` | AWS Lambda (`Environment`) | **SECRETO** | Requerido únicamente para workers en segundo plano de generación docente. |
| `ReservedConcurrency` | AWS SAM (`Parameters`) | Config | `5` (guardián inicial para proteger el pool de conexiones de Supabase). |

### 5.2 Análisis de Latencia y Selección de Región AWS

* **Región de la Base de Datos:** `us-east-2` (Ohio).
* **Región Recomendada para AWS Lambda:** **`us-east-2`**.
* **Justificación de Rendimiento:** Desplegar Lambda en la misma región que la base de datos reduce la latencia RTT de cada consulta SQL de ~45 ms (si se desplegara en `us-east-1` o `sa-east-1`) a **< 2.5 ms**. Dado que endpoints de aprendizaje ejecutan 2 a 4 transacciones de validación de estado por intento, la co-ubicación en `us-east-2` ahorra hasta 150 ms en el tiempo total de respuesta.

---

## 6. FASE 5 — Plan de Publicación Coordinada

### 6.1 Matriz de Fases y Dependencias

```
[PASO 1: Respaldo] ──► [PASO 2: Migraciones RLS] ──► [PASO 3: Verificación BD]
                                                             │
                                                             ▼
[PASO 6: Verif. Lambda] ◄── [PASO 5: Despliegue Lambda] ◄── [PASO 4: Build & Push ECR]
         │
         ▼
[PASO 7: Config Cloudflare] ──► [PASO 8: Pruebas E2E] ──► [PASO 9: Producción OK]
```

### 6.2 Secuencia de Despliegue Detallada

#### Paso 1 — Respaldo Preventivo de Esquema y Datos Remotos
* **Tipo:** Sin interrupción de servicio.
* **Acción:** Exportar el esquema y filas actuales de Supabase mediante pg_dump o script de respaldo antes de aplicar las nuevas políticas.

#### Paso 2 — Aplicación de Migraciones de Seguridad Pendientes
* **Tipo:** Bloqueante para la consistencia de RLS (tiempo estimado: < 15 segundos).
* **Acción:** Ejecutar en el SQL Editor de Supabase o vía asyncpg:
  1. `supabase/migrations/20261109000000_profiles_privilege_hardening.sql`
  2. `supabase/migrations/20261109010000_release_mvp_security_hardening.sql`
* **Resultado Esperado:** Se soluciona la recursión de `sections`, se aplica la política de menor privilegio en `profiles` y se bloquea el escalamiento de roles.

#### Paso 3 — Verificación de Salud del Esquema Remoto
* **Tipo:** Verificación de solo lectura.
* **Comprobación:** Ejecutar consulta REST como docente hacia `/rest/v1/sections?select=id,name`. Debe devolver la sección del colegio piloto San Agustín sin errores 500 ni conjuntos vacíos involuntarios.

#### Paso 4 — Construcción y Publicación de Imagen en Amazon ECR
* **Tipo:** Fuera de línea / CI.
* **Comandos (tras configurar credenciales AWS en `us-east-2`):**
  ```bash
  export AWS_REGION=us-east-2
  aws cloudformation deploy \
    --template-file deploy/aws/ecr.yaml \
    --stack-name nexo-mvp-ecr \
    --region "$AWS_REGION"

  export IMAGE_TAG="mvp-$(git rev-parse --short HEAD)"
  ./deploy/aws/build_and_push.sh
  ```

#### Paso 5 — Despliegue de la Pila SAM AWS Lambda
* **Tipo:** Aprovisionamiento de infraestructura.
* **Comando:**
  ```bash
  sam deploy \
    --template-file deploy/aws/template.yaml \
    --stack-name nexo-mvp-ml-api \
    --region us-east-2 \
    --capabilities CAPABILITY_IAM \
    --resolve-s3 \
    --parameter-overrides \
      ImageUri="<ACCOUNT_ID>.dkr.ecr.us-east-2.amazonaws.com/nexo-mvp-ml-api:${IMAGE_TAG}" \
      DatabaseUrl="postgresql://postgres.oqjahhbqcethwgpufgnm:<PASSWORD>@aws-0-us-east-2.pooler.supabase.com:6543/postgres?sslmode=require" \
      SupabaseUrl="https://oqjahhbqcethwgpufgnm.supabase.co" \
      CorsOrigins="https://plataformamicro.fabriziovalerio-c.workers.dev" \
      ReservedConcurrency=5 \
      MemorySize=1024 \
      Timeout=30
  ```
* **Extracción de Salidas:** Anotar `MlApiFunctionUrl` generado en los outputs del stack.

#### Paso 6 — Verificación de Endpoints, CORS y JWT en Lambda
* **Tipo:** Verificación sintética directa.
* **Prueba 1 (Salud sin BD):**
  ```bash
  curl -i "<MlApiFunctionUrl>api/v1/health"
  # Esperado: HTTP 200 OK {"status":"healthy"}
  ```
* **Prueba 2 (Preflight CORS):**
  ```bash
  curl -i -X OPTIONS "<MlApiFunctionUrl>api/v1/activities" \
    -H "Origin: https://plataformamicro.fabriziovalerio-c.workers.dev" \
    -H "Access-Control-Request-Method: GET"
  # Esperado: HTTP 200 con Access-Control-Allow-Origin correspondiente
  ```
* **Prueba 3 (Protección JWT sin token):**
  ```bash
  curl -i "<MlApiFunctionUrl>api/v1/activities"
  # Esperado: HTTP 401 Unauthorized
  ```
* **Prueba 4 (Llamada autenticada con JWT de prueba):**
  ```bash
  curl -i "<MlApiFunctionUrl>api/v1/activities" \
    -H "Authorization: Bearer <TOKEN_VALIDO_ES256>"
  # Esperado: HTTP 200 OK con catálogo de actividades
  ```

#### Paso 7 — Inyección de `NEXT_PUBLIC_API_URL` en Cloudflare Workers
* **Tipo:** Actualización de configuración del frontend.
* **Acción:**
  * Actualizar la variable de entorno `NEXT_PUBLIC_API_URL` en el Cloudflare Dashboard (Settings > Variables and Secrets) o añadirla en `apps/web/wrangler.jsonc` y re-desplegar:
    `NEXT_PUBLIC_API_URL = "https://<unique-id>.lambda-url.us-east-2.on.aws"` (sin barra final).

#### Paso 8 — Pruebas Integrales de Usuario Final (E2E)
* **Tipo:** Validación funcional de extremo a extremo en el navegador.
* **Verificaciones en `https://plataformamicro.fabriziovalerio-c.workers.dev`:**
  1. Login exitoso con credenciales demo (Docente Ana García y Estudiante Lucía Mendoza).
  2. Navegación a `/system-status`: Comprobar que la telemetría reporta `FastAPI Lambda` en estado `healthy`, latencia medida y modelos de inferencia activos.
  3. Ejecución de un cuestionario interactivo: Comprobar inserción inmutable en `answer_events` con `X-Idempotency-Key`.
  4. Generación de recomendaciones adaptativas: Verificar que el motor de adaptación devuelve el siguiente microcontenido sin bloqueos.

#### Paso 9 — Cierre y Consolidación en Git
* **Tipo:** Operación de control de versiones.
* **Acción:** Crear Pull Request de `release/mvp-aws-lambda` hacia `main` e integrar los cambios tras la aprobación de pruebas.

---

## 7. Estrategia de Rollback

### 7.1 Rollback de Frontend (Cloudflare Workers)
* **Mecanismo:** Despliegues instantáneos inmutables de Cloudflare.
* **Procedimiento:**
  1. En el Cloudflare Dashboard, acceder a **Workers & Pages > plataformamicro > Deployments**.
  2. Localizar el despliegue previo estable (Build ID `FTPYhJa09YwDAk7HEQIFQ`).
  3. Seleccionar **Rollback to this deployment**.
  4. La propagación global en el Edge de Cloudflare toma **menos de 3 segundos**, restaurando de inmediato la versión con fallback directo a Supabase.

### 7.2 Rollback de Backend (AWS Lambda)
* **Mecanismo:** Control de versiones de CloudFormation / SAM.
* **Procedimiento:**
  * Si la nueva versión del contenedor en Lambda presenta fallos de memoria o latencia:
    ```bash
    aws lambda update-function-code \
      --function-name nexo-mvp-ml-api-ml-api \
      --image-uri "<IMAGE_URI_ANTERIOR>" \
      --region us-east-2
    ```
  * En caso de fallo crítico en el servicio, reducir temporalmente `ReservedConcurrentExecutions: 0` para detener invocaciones mientras se investiga, forzando a los clientes web a usar su política de fallback.

### 7.3 Rollback de Migraciones de Base de Datos
* **Mecanismo:** Scripts SQL de reversión idempotente.
* Si la migración `20261109010000_release_mvp_security_hardening.sql` requiere revertirse temporalmente:
  ```sql
  -- Reversión de emergencia: Restaurar lectura amplia de perfiles si falla el aislamiento
  DROP POLICY IF EXISTS "profiles_select_own" ON public.profiles;
  DROP POLICY IF EXISTS "profiles_select_teacher_students" ON public.profiles;
  DROP POLICY IF EXISTS "profiles_select_admin_scope" ON public.profiles;

  CREATE POLICY "profiles_select_own_or_same_tenant" ON public.profiles
      FOR SELECT USING (
          id = (SELECT auth.uid())
          OR tenant_id = (SELECT public.current_user_tenant_id())
          OR (SELECT public.current_user_role()) = 'super_admin'
      );
  ```

---

## 8. Bloqueos Detectados y Acciones Manuales Pendientes

### Bloqueos Operativos Actuales

1. **Ausencia de Sesión AWS en el Entorno:** Ni AWS CLI ni SAM CLI están autenticados localmente. La creación de repositorios ECR y despliegue de Lambda requiere que el usuario suministre una sesión válida en su terminal.
2. **Desajuste de Dominio CORS en `template.yaml`:** La plantilla SAM tiene configurado por defecto `CorsOrigins: "https://plataformamicro.edu.pe,https://app.plataformamicro.edu.pe"`. Se debe suministrar obligatoriamente `--parameter-overrides CorsOrigins="https://plataformamicro.fabriziovalerio-c.workers.dev"` durante el despliegue para no romper la comunicación con el frontend actual.
3. **Migración RLS de Secciones Pendiente en Supabase:** La base remota rechaza consultas a `sections` para usuarios autenticados debido a políticas RLS pendientes (`20261109010000`).

### Check-list Previo al Despliegue para OpenCode

Antes de que DevOps inicie la publicación en AWS, OpenCode debe certificar:
* [x] Contenedor `Dockerfile.lambda` configurado con Lambda Web Adapter en puerto `8080`.
* [x] Contexto de Dockerfile en la raíz para resolver artefactos `/app/ml/artifacts`.
* [x] Configuración de asyncpg con `statement_cache_size=0` para Supavisor Transaction Mode.
* [x] Soporte asimétrico ES256 verificado contra el JWKS de Supabase.
* [ ] Tests unitarios y de integración de FastAPI completados exitosamente en la rama `release/mvp-aws-lambda`.
* [ ] Consolidación limpia de los archivos modificados sin cambios espurios.
