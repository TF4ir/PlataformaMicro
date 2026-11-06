# Plan de MVP demostrable — Nexo

**Fecha:** 2026-11-05  
**Instancia analizada:** `https://oqjahhbqcethwgpufgnm.supabase.co`  
**Alcance:** dejar un MVP navegable y demostrable para la entrega del profesor, sin depender todavía de un modelo predictivo entrenado.

---

## 1. Veredicto

El código está mucho más avanzado que lo que dice el README: hay 46 endpoints de API (48 contando health/warmup), 18 rutas web, 8 migraciones y el ciclo adaptativo implementado. El frontend compila y el backend pasa sus pruebas.

Pero **la demo pública no funciona hoy** por cuatro bloqueos concretos:

1. **La base remota está a medio migrar.** Solo tiene el esquema inicial. Le faltan tablas y columnas de M2–M5.
2. **Supabase Auth remoto devuelve HTTP 500** (`Database error querying schema`), así que ni siquiera se puede iniciar sesión.
3. **El backend solo valida JWT HS256**, pero Supabase (local y remoto) emite **ES256**. Todas las llamadas autenticadas devuelven 401.
4. **No hay datos de clase**: el seed local tiene 1 estudiante, 1 KC, 1 pregunta y 0 respuestas. No alcanza para demostrar retención, recomendaciones ni reportes docentes.

La buena noticia: los cuatro se resuelven sin reescribir la arquitectura. El flujo local ya funciona cuando se usan las cabeceras de desarrollo, y el frontend construye correctamente.

---

## 2. Evidencia verificada

| # | Hallazgo | Cómo se verificó | Severidad |
|---|---|---|---|
| 1 | La BD remota solo tiene el esquema inicial | `GET /rest/v1/activities?select=status` → `42703 column activities.status does not exist`; faltan `content_generation_jobs`, `question_drafts`, `notifications`, `activity_sections`, `content_exposure_events` | **Bloqueante** |
| 2 | Auth remoto roto | `POST /auth/v1/token?grant_type=password` → `500 Database error querying schema` | **Bloqueante** |
| 3 | Tokens ES256 rechazados | Header del token local: `alg=ES256`; `GET /students/me/dashboard` con Bearer → 401 `INVALID_CREDENTIALS` | **Bloqueante** |
| 4 | Sin datos de demostración | BD local: 1 tenant, 2 perfiles, 1 curso, 1 sección, 1 KC, 1 microcontenido, 1 pregunta, 0 `answer_events`, 0 `content_exposure_events`, 0 recomendaciones | **Bloqueante** |
| 5 | El Dockerfile no arranca | `app/` importa `ml.src.*`, pero la imagen solo copia `app/` → `ModuleNotFoundError: No module named 'ml'` | Alta |
| 6 | Trayectoria docente inventada | `services/ml-api/app/repositories/teacher_repository.py` líneas 606–612: valores 70/74/78/75/80/84 fijos en código | Alta (integridad) |
| 7 | Quedan mocks | `role-context.tsx`, `sidebar.tsx`, `system-status/page.tsx` importan `mock-data` | Media |
| 8 | `complete_setup.sql` desactualizado | 21 tablas vs. 26 de las migraciones; faltan 5 tablas y ~30 columnas | Alta |
| 9 | README describe “Fase 0” | El código está en M5.4; el README no refleja el estado real | Media |
| 10 | Sin lockfile raíz | `npm ci` en la raíz falla; el monorepo usa workspaces | Media |
| 11 | Middleware confía en cookies del cliente | `nexo_session` y `nexo_role` las fija el navegador; la seguridad real está en la API + RLS | Media |
| 12 | El modelo no es el de la tesis | No hay artefacto entrenado ni PyTorch; en desarrollo se usa un HLR sintético y en producción cae a reglas. DAS3H/PFA/BKT existen y se probaron con datos sintéticos | Media (documentación) |

**Corrección al análisis previo:** los 57 tests fallidos no se reproducen en este entorno. Aquí el backend pasa **242 tests** y el frontend **37**. Los fallos probablemente dependen de una BD limpia sin fixtures; hay que aislar los tests de integración para que no dependan de filas preexistentes.

---

## 3. Arquitectura recomendada para el MVP

La UI actual es de componentes cliente que llaman a FastAPI desde el navegador. Por eso, para la demo, el servicio FastAPI sigue siendo necesario. La forma más rápida y coherente con tu infraestructura es:

```text
Navegador (estudiante / docente)
        │  HTTPS + Bearer JWT de Supabase
        ▼
Next.js 14.2.35 en Cloudflare Workers (OpenNext)
        │  REST + JWT
        ▼
FastAPI en blitz.cloud (contenedor)
  · hoy: API de lectura/escritura + motor de reglas
  · después: carga del artefacto DAS3H congelado
        │  asyncpg (pooler de Supabase)
        ▼
Supabase: PostgreSQL + Auth + Storage + RLS
```

- **Cloudflare:** solo el frontend.
- **Supabase:** datos, identidad, storage y RLS.
- **Docker:** solo el servicio FastAPI/modelo, en blitz.cloud o un host equivalente.
- **No** se dockeriza toda la plataforma.

**¿Por qué no “todo en Supabase” ahora?** Sería necesario portar 46 endpoints y la lógica de recomendación a RPC de Postgres o a Server Actions. Es un rewrite de 1–2 semanas y agrega riesgo para la fecha de entrega. Para el MVP, FastAPI cumple el rol de “servicio del modelo”; cuando el modelo esté entrenado, solo se reemplaza el artefacto, no la arquitectura.

**Alternativa si no quieres ningún host externo:** mover CRUD y reglas a funciones RPC de Supabase y acciones de servidor de Next.js. Es viable, pero es la Fase 4 opcional, no la ruta crítica.

---

## 4. Plan por fases

### Fase 0 — Base de datos y datos de demostración (0.5–1 día)

**Objetivo:** que la instancia remota tenga el esquema completo, Auth sano y una clase piloto con historial.

Tareas:

1. **Decidir** entre reparar la instancia actual o crear una nueva. Dado que las tablas están vacías y Auth está roto, recomiendo **crear un proyecto nuevo** o **resetear** el actual y aplicar todo desde cero.
2. Aplicar las 8 migraciones en orden (`supabase/migrations/`).
3. Crear el seed de demostración (`supabase/seed_demo.sql` + `scripts/seed_demo.py`):
   - 1 tenant, 1 docente, **10 estudiantes seudonimizados**.
   - 1 curso, 1 sección, 4 unidades.
   - **5 KC**: fotosíntesis, respiración celular, estructura celular, herencia mendeliana y ciclos biogeoquímicos.
   - **5 microcontenidos** publicados (uno por KC).
   - **15 preguntas** (3 por KC) con 4 opciones y explicación.
   - **5 actividades** de práctica (una por KC) asignadas a la sección.
   - **6 semanas de historial**: 120 intentos y 360 `answer_events`.
   - 60 `content_exposure_events`.
   - 2 recomendaciones pendientes + 1 completada por estudiante (30 en total).
4. Regenerar `complete_setup.sql` a partir de las migraciones (para que no vuelva a quedar desactualizado).
5. Verificar:
   - 26 tablas en `public`.
   - Login de docente y estudiante.
   - `answer_events` con historial por KC.
   - `/students/me/dashboard` devuelve cursos y recomendaciones.

**Criterio de aceptación:** la estudiante demo inicia sesión y su dashboard muestra una recomendación; el docente ve 10 estudiantes con datos.

### Fase 1 — Correcciones funcionales (1–1.5 días)

1. **JWKS + ES256** en `services/ml-api/app/core/auth.py`, conservando HS256 como respaldo.
2. **Modo `demo` seguro**:
   - Prohíbe `X-User-Id`/`X-Tenant-Id` igual que producción.
   - Permite el motor de reglas o el modelo sintético, pero lo marca visiblemente como **“no validado”**.
   - Evita el dilema actual: `development` acepta suplantación; `production` rechaza el modelo sintético.
3. **Trayectoria docente real**:
   - Reemplazar los valores fijos por precisión semanal observada desde `answer_events`.
   - Quitar las curvas “proyectadas” inventadas o etiquetarlas como proyección heurística. Para el MVP, recomiendo mostrar solo lo observado y un aviso de “modelo pendiente”.
4. **Eliminar mocks** de `role-context.tsx`, `sidebar.tsx` y `system-status/page.tsx`.
5. **Guardas de sesión en servidor** para `/teacher/*` y rutas de estudiante (layout de servidor con `supabase.auth.getUser()`), sin confiar solo en cookies del cliente.
6. **Dockerfile**:
   - Contexto de build en la raíz del repo.
   - Copiar `ml/` y `app/`.
   - `PYTHONPATH=/app`.
   - `PORT` configurable.
   - Probar la imagen real con Docker.
7. **Variables de entorno** para local y remoto; documentar el pooler de Supabase.
8. **Tests**: aislar integraciones, agregar pruebas de ES256 y del modo demo.
9. **Build**: `next build`, `tsc`, `pytest`, `ruff`, `mypy`.

**Criterio de aceptación:** flujo completo local sin cabeceras de desarrollo y con tokens ES256.

### Fase 2 — Despliegue (1 día)

1. **FastAPI en blitz.cloud**:
   - Variables: `DATABASE_URL`, `SUPABASE_URL`, `CORS_ORIGINS`, `ENVIRONMENT=demo`.
   - Pooler de Supabase con `statement_cache_size=0` si se usa transaction mode.
   - Healthcheck `/api/v1/health`.
2. **Frontend en Cloudflare Workers**:
   - `@opennextjs/cloudflare` + `wrangler`.
   - `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`, `NEXT_PUBLIC_API_URL`.
   - CORS del backend con el dominio de Cloudflare.
3. **Smoke tests** en producción:
   - Login estudiante/docente.
   - Dashboard, recomendación, microlección, quiz, feedback.
   - Reportes docentes y exportación CSV.
4. **Dominio** y certificado.

**Criterio de aceptación:** URL pública usable desde un navegador limpio, sin cabeceras especiales.

### Fase 3 — Evidencia y documentación (1 día)

1. Guion de demo de 10 minutos (ver sección 6).
2. Capturas y video del flujo.
3. Actualizar `README.md`, `PROJECT.md` y `docs/architecture/overview.md` al estado M5.4/MVP.
4. Documento para el profesor con los 5 ítems:
   - solución tecnológica y relación con el problema;
   - funcionalidades principales justificadas;
   - prototipo/MVP;
   - flujos de interacción y UX;
   - validación y criterios de utilidad.
5. Anexo de integridad: qué está implementado, qué es regla, qué es modelo sintético y qué falta entrenar.

### Fase 4 — Modelo predictivo (post-MVP)

1. Entrenar DAS3H/PFA/BKT con datos reales o sintéticos reproducibles.
2. Congelar artefacto con `metadata.json` (versión, métricas, commit).
3. Evaluar AUC-ROC, Brier, ECE y calibración.
4. Reemplazar el motor de reglas por el artefacto, manteniendo el modo demo.
5. Protocolo cuasiexperimental a 7 días.

---

## 5. Dataset de demostración implementado

| Entidad | Cantidad | Notas |
|---|---:|---|
| Tenants | 1 | Colegio Piloto San Agustín |
| Docentes | 1 | `ana.garcia@nexo.edu.pe` |
| Estudiantes | 10 | Lucía Mendoza + 9 identificadores seudónimos |
| Cursos / secciones | 1 / 1 | Ciencias, 5.° A |
| Unidades | 4 | Estructura celular, nutrición, genética, ecología |
| Knowledge Components | 5 | Fotosíntesis, respiración celular, estructura celular, herencia mendeliana, ciclos biogeoquímicos |
| Microcontenidos | 5 | Publicados, con cuerpo JSON |
| Preguntas | 15 | 3 por KC, 4 opciones, explicación |
| Actividades | 5 | Práctica formativa, una por KC |
| Intentos | 120 | 6 semanas × 2 actividades/semana × 10 estudiantes |
| `answer_events` | 360 | Inmutables, con timestamps distribuidos |
| `content_exposure_events` | 60 | Una exposición semanal por estudiante |
| Recomendaciones | 30 | 20 pendientes + 10 completadas, todas `rule_based_fallback` |

**Cómo cargarlo:**

```bash
# Supabase local: reset + migraciones + ambos seeds
supabase db reset

# O cargar solo los seeds sobre una base ya migrada
services/ml-api/.venv/bin/python scripts/seed_demo.py

# Proyecto remoto (cadena Postgres del proyecto)
SUPABASE_DB_URL='postgresql://postgres.<ref>:<password>@<host>:5432/postgres' \
  services/ml-api/.venv/bin/python scripts/seed_demo.py --yes
```

El script ejecuta `supabase/seed.sql` y luego `supabase/seed_demo.sql`. Ambos son
idempotentes: usan UUID deterministas y `ON CONFLICT DO NOTHING`, por lo que se
pueden repetir sin duplicar datos. **No se insertan predicciones ni métricas de
modelo**: las recomendaciones se etiquetan como `rule_based_fallback` y su motivo
declara que aún no existe un artefacto predictivo validado.

**Cuentas demo** (contraseña `Nexo2026!`, solo para la demo; rotar después):

- Docente: `ana.garcia@nexo.edu.pe`
- Estudiante principal: `lucia.mendoza@nexo.edu.pe`
- Estudiantes secundarios: `estudiante.502@nexo.edu.pe` … `estudiante.510@nexo.edu.pe`

> Los estudiantes nuevos usan nombres seudónimos (“Estudiante 502”…“Estudiante 510”). No se incorporan nombres reales, correos personales ni datos de menores.

---

## 6. Guion de demo (10 minutos)

1. **Login estudiante** (`lucia.mendoza@nexo.edu.pe`).
2. **Dashboard**: saludo, curso, hero de repaso prioritario.
3. **Microlección**: lectura activa; se registra `content_exposure_events`.
4. **Cuestionario**: responder, ver feedback inmediato y explicación.
5. **Recomendaciones**: “Actualizar diagnóstico”; se crea o actualiza una recomendación.
6. **Progreso**: precisión observada vs. retención estimada; estado de cold-start si aplica.
7. **Login docente** (`ana.garcia@nexo.edu.pe`).
8. **Dashboard docente**: KPIs, estudiantes vulnerables, consolidación.
9. **Reportes**: heatmap, precisión por KC, trayectoria observada real, exportación CSV.
10. **System status**: health de API y Supabase.

---

## 7. Qué decir (y qué no) en la tesis

**Se puede afirmar:**

- El MVP funciona de punta a punta sobre PostgreSQL/Supabase con RLS y eventos inmutables.
- El modelo de datos es agnóstico a la asignatura.
- Existe un motor de adaptación por reglas y un contrato de inferencia listo para el modelo.
- DAS3H, PFA y BKT están implementados y evaluados con datos sintéticos.
- Hay un protocolo de evaluación definido (AUC-ROC, Brier, ECE, validación Group-K-Fold).

**No se debe afirmar todavía:**

- Que el modelo está entrenado con datos reales o validado.
- Que las curvas de retención son empíricas.
- Que hay resultados de AUC/Brier reales.
- Que se usa DKT con PyTorch (no está en el repo).
- Que las proyecciones docentes son predicciones del modelo.

**Narrativa recomendada:** “La plataforma y el pipeline de datos están operativos; el modelo predictivo es la siguiente fase de la investigación. El MVP demuestra el flujo pedagógico con un motor de reglas explícito y trazable, sin presentar resultados predictivos no validados.”

---

## 8. Migración y Conexión de Supabase Remoto

Se verificó el estado exacto de la instancia remota `https://oqjahhbqcethwgpufgnm.supabase.co`:
- **Esquema:** Cuenta únicamente con las 21 tablas de la migración inicial (M1) y 0 filas.
- **Faltantes:** 5 tablas (`content_generation_jobs`, `question_drafts`, `notifications`, `activity_sections`, `content_exposure_events`), columnas clave (`activities.status`, etc.) y políticas RLS/funciones de M2–M5.
- **Causa raíz del error HTTP 500 en Auth:** El GoTrue remoto (v2.197+) aborta porque el script inicial dejó valores `NULL` en campos de texto de `auth.users` (`confirmation_token`, `recovery_token`, etc.).

### Opciones preparadas para aplicar la migración:

1. **Opción A (Dashboard SQL Editor — Recomendada, sin exponer credenciales):**
   - Abrir el **SQL Editor** del proyecto en Supabase Dashboard.
   - Copiar y pegar el archivo [`supabase/remote_migration_and_seed.sql`](file:///root/PlataformaMicro/supabase/remote_migration_and_seed.sql).
   - Presionar **Run**.
   - Esto repara automáticamente `auth.users`, aplica las migraciones 2 a 8 y carga el dataset de demostración completo.

2. **Opción B (Línea de comandos con cadena de conexión):**
   ```bash
   SUPABASE_DB_URL='postgresql://postgres.<ref>:<password>@aws-0-...pooler.supabase.com:6543/postgres' \
     services/ml-api/.venv/bin/python scripts/migrate_remote.py --yes
   ```

---

## 9. Orden de ejecución inmediato

1. Aplicar `supabase/remote_migration_and_seed.sql` en Supabase remoto. **(script listo y validado)**
2. Probar login remoto de Lucía y Ana contra la URL remota. **(espera del paso 1)**
3. Corregir Dockerfile y modo demo. **(hecho)**
4. Corregir JWKS/ES256. **(hecho)**
5. Quitar mocks y trayectoria inventada. **(hecho)**
6. Probar el flujo completo local. **(hecho vía API y navegador)**
7. Desplegar API y frontend. **(pendiente)**
8. Capturas, video y documento final. **(capturas locales listas; faltan las de producción)**

---

## 10. Estado de ejecución al 2026-11-05

**Verificado en local:**

| Elemento | Estado | Evidencia |
|---|---|---|
| Migraciones 1–8 | Aplicadas en Supabase local | 26 tablas en `public` |
| Seed de demostración | Operativo e idempotente | `scripts/seed_demo.py` → 10 estudiantes, 5 KC, 15 preguntas, 120 intentos, 360 respuestas |
| Login Supabase Auth | Operativo en local | Lucía y Ana obtienen JWT ES256 |
| Backend con JWT ES256 | Operativo | `245 passed, 2 skipped`; endpoints autenticados responden 200 |
| Dashboard estudiante | Con datos | 5 cursos/actividades, 69.2 % de precisión observada, 2 repasos pendientes |
| Progreso estudiante | Con datos | 36 respuestas, desglose por KC, sin predicciones inventadas |
| Flujo de cuestionario | Operativo | inicio → 3 respuestas → envío (66.67 %) → resultados con explicación |
| Dashboard docente | Con datos | 10 estudiantes, 5 actividades, 121 intentos, 10 repasos completados |
| Reportes docentes | Con datos | heatmap 10×5, precisión por KC y trayectoria semanal observada |

**Pendiente para la entrega:**

1. Aplicar migraciones + seed en el proyecto remoto (requiere `SUPABASE_DB_URL` o service role).
2. Reparar o recrear Supabase Auth remoto.
3. Desplegar FastAPI y el frontend en Cloudflare.
4. Repetir las capturas contra la URL pública.
5. Redactar el documento de los 5 ítems del profesor.

**Nota de integridad:** el dataset es sintético y reproducible; se usa solo para
demostrar el flujo. No representa resultados de aprendizaje de estudiantes reales
ni métricas de un modelo entrenado.
