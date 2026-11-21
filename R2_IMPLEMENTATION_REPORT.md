# INFORME DE IMPLEMENTACIÓN — R2: CICLO FUNCIONAL DE APRENDIZAJE ADAPTATIVO & INTEGRIDAD DE EVALUACIÓN

**Repositorio:** `TF4ir/PlataformaMicro`  
**Rama:** `release/r1-2026-11`  
**Fecha:** 20/11/2026 (UTC)  
**Alcance:** Cierre de R1.2 (publicación controlada y validación CI/E2E) e implementación integral de fases R2.0 a R2.4 (Learning Loop & Assessment Integrity).

---

## 1. Resumen Ejecutivo y Estado de Entrega

PlataformaMicro ha cerrado el ciclo completo de aprendizaje adaptativo, transitando desde una infraestructura preparada pero desacoplada a un ciclo de retroalimentación pedagógica y probabilística activo y persistente basado en interacciones reales del estudiante.

El flujo implementado garantiza:
1. **Acceso Seguro a Evaluaciones:** Cuestionarios accesibles únicamente para estudiantes matriculados en secciones asignadas, con opciones y claves desensibilizadas del lado del cliente.
2. **Evaluación de Respuestas en Servidor:** Calificación rigurosa sin depender de cómputos del cliente, registrando eventos de respuesta inmutables (append-only) en `answer_events` con clave de idempotencia (`idempotency_key`) y tiempos de respuesta.
3. **Sellado Atómico de Sesión:** Cierre formal del intento (`quiz_attempts`), bloqueo de envíos posteriores (HTTP 409 Conflict) y cálculo estricto de puntaje.
4. **Actualización Predictiva Inmediata:** Desencadenamiento del motor predictivo (`RetentionInferenceService`), estimando retención probabilística por componente de conocimiento (KC), persistiendo estados en `predictions` y `student_knowledge_states` con límites `NUMERIC(4,3)` y ordenamiento canónico para prevenir interbloqueos (deadlocks).
5. **Motor Adaptativo y Recomendaciones:** Evaluación pedagógica (`AdaptationEngine`) frente al umbral configurable $\tau = 0.650$ (`settings.DEFAULT_TAU_THRESHOLD`), ventana anti-fatiga de 24 horas (`settings.ADAPTATION_COOLDOWN_HOURS`), bloqueo de serialización a nivel de estudiante (`pg_advisory_xact_lock`) y selección de microcontenidos publicados.
6. **Integración con Dashboard y Consumo:** Los repasos sugeridos se persisten en `recommendations` y se reflejan inmediatamente en el dashboard del estudiante; las consultas son idempotentes (no duplican recomendaciones) y la finalización de la lectura marca la recomendación como completada.

---

## 2. Fase R2.0 — Matriz Compacta de Auditoría

| Componente | Estado Previo Verificado en Código | Modificación Realizada |
|---|---|---|
| **Cuestionarios (Assessment)** | Modelos y repositorio `LearningRepository` existentes; sanitización de opciones implementada en `get_student_activity_detail`. | Verificada sanitización de alternativas; se garantizó bloqueo de respuestas a intentos ya sellados (HTTP 409 Conflict). |
| **Evaluación (Evaluation)** | Endpoint `/attempts/{id}/answers` persistía en `answer_events`, pero no desencadenaba recalificación ni inferencia. | Se integró el ciclo cerrado en `/students/me/attempts/{id}/submit` calculando puntaje y disparando inferencia y adaptación. |
| **Intentos (Attempts)** | Tabla `quiz_attempts` existía con bloqueo `FOR UPDATE` y estados de ciclo de vida (`in_progress`, `completed`). | Se consolidó la idempotencia de reenvíos y el sellado que rechaza respuestas tardías. |
| **answer_events** | Tabla inmutable append-only con `idempotency_key`, tiempos de respuesta y disparador RLS. | Se normalizó la causalidad temporal en `history_builder.py` con `event_timestamp <= reference_time` para evitar condiciones de carrera por microsegundos. |
| **Predicción (Prediction)** | `RetentionInferenceService` calculaba inferencias pero no actualizaba `student_knowledge_states` ni ordenaba KCs de forma determinista. | Implementado batch upsert atómico a `student_knowledge_states` con ordenamiento por `knowledge_component_id` para eliminar riesgo de interbloqueos y acotamiento a `NUMERIC(4,3)`. |
| **Adaptación (Adaptation)** | `AdaptationEngine` implementado de forma aislada; umbrales numéricos cableados en código sin configuración central. | Se parametrizó $\tau$ y `anti_fatigue_hours` en `Settings`, y se introdujo bloqueo transaccional `pg_advisory_xact_lock` por estudiante para impedir recomendaciones duplicadas concurrentes. |
| **Recomendaciones (Recommendations)** | Tabla `recommendations` soportaba estados pero no se poblaba tras finalizar una evaluación real. | Se conectó la persistencia de recomendaciones pendientes activas al finalizar el intento y se verificó el ciclo de vida hasta `completed`. |
| **Frontend (Dashboard & UI)** | Dashboard consumía endpoints pero mostraba listas vacías si no existían registros en `recommendations`. | Flujo validado: al finalizar el cuestionario, las recomendaciones persisten y son renderizadas en próximas consultas sin duplicarse. |

---

## 3. Arquitectura y Módulos Modificados

### 3.1. `services/ml-api/app/core/config.py`
- Se incorporaron las variables de configuración de umbrales requeridas por la Regla 5.1 de `AGENTS.md`:
  - `DEFAULT_TAU_THRESHOLD: float = 0.650` (umbral crítico de consolidación).
  - `ADAPTATION_COOLDOWN_HOURS: int = 24` (ventana anti-fatiga para deduplicación de recomendaciones).

### 3.2. `services/ml-api/app/prediction/inference_service.py`
- Se conectó `_persist_knowledge_states_batch` para realizar upsert atómico de `student_knowledge_states` (`p_mastery`, `confidence`, `total_interactions`, `last_updated_at`).
- Se introdujo ordenamiento determinista canónico de los registros por `knowledge_component_id` antes del batch insert, eliminando de forma definitiva cualquier condición de interbloqueo (`deadlock detected`) en concurrencia.
- Se implementó acotamiento numérico estricto `round(max(0.0, min(1.0, val)), 3)` para cumplir con la restricción DDL de PostgreSQL `NUMERIC(4,3) CHECK (value >= 0.0 AND value <= 1.0)`.

### 3.3. `services/ml-api/app/prediction/history_builder.py`
- Se sincronizó la cláusula de consulta causal a `event_timestamp <= reference_time`, previniendo la pérdida de eventos contemporáneos al intento recién enviado y manteniendo estricta causalidad temporal (sin fuga hacia el futuro).
- Se añadió ordenamiento determinista canónico `ORDER BY kc.name ASC, kc.id ASC` en la resolución de KCs accesibles.

### 3.4. `services/ml-api/app/adaptation/adaptation_engine.py`
- Se parametrizó el umbral $\tau$ y el tiempo anti-fatiga mediante inyección de `settings`.
- Se introdujo serialización a nivel de estudiante dentro de una transacción única utilizando `SELECT pg_advisory_xact_lock(hashtext($1))` con clave `adaptation_{student_id}`. Esto garantiza que evaluaciones concurrentes no emitan recomendaciones redundantes para el mismo componente.

### 3.5. `services/ml-api/app/api/v1/learning.py`
- El controlador `submit_attempt` ahora coordina el ciclo cerrado:
  1. Sellado del intento y calificación en base de datos.
  2. Actualización de perfiles predictivos y de estados de dominio (`student_knowledge_states`).
  3. Ejecución del motor adaptativo y generación de recomendaciones persistentes.
  4. Resiliencia ante fallos transitorios de red o timeouts para evitar abortar la respuesta HTTP del estudiante.
- El controlador `record_answer` valida que el intento no se encuentre completado; de lo contrario, responde con HTTP 409 Conflict.

### 3.6. `services/ml-api/tests/test_r2_adaptive_learning_loop.py`
Suite exhaustiva de pruebas de integración que valida:
1. `test_full_closed_loop_execution`: Ciclo completo (acceso sanitizado -> inicio con clave de idempotencia -> envío de respuesta incorrecta -> persistencia append-only en `answer_events` -> finalización de intento -> cálculo de puntaje -> persistencia en `student_knowledge_states` y `predictions` -> generación de recomendación adaptativa -> visualización en dashboard -> consulta idempotente -> estudio de microcontenido y transición de estado a `completed` -> aislamiento de datos entre estudiantes).
2. `test_attempt_completed_blocks_subsequent_answers`: Rechazo con HTTP 409 de respuestas enviadas a un intento completado.
3. `test_no_published_content_available_fallback`: Degradación controlada cuando no existe microcontenido publicado en catálogo (`no_content_available` sin errores).
4. `test_concurrent_attempt_submissions_no_deadlock_or_duplicate_recommendations`: Envío simultáneo de intentos mediante `asyncio.gather` demostrando ausencia de deadlocks y cero duplicaciones de recomendación.
5. `test_cold_start_initial_practice_and_anti_fatigue_cooldown`: Transición desde cero interacción a consolidación inicial por regla pedagógica y respeto de la ventana de enfriamiento de 24 horas ante evaluaciones subsecuentes.

---

## 4. Evidencia de Validación y Ejecución de Pruebas

Todas las suites automatizadas fueron ejecutadas sobre el código y base de datos local y en CI:

### Backend (`pytest` + `mypy` + `ruff`)
```bash
$ pytest services/ml-api/tests/test_r2_adaptive_learning_loop.py -v
============================== 5 passed in 2.10s ===============================

$ pytest services/ml-api/tests -q
334 passed, 2 skipped in 174.63s

$ ruff check services/ml-api scripts/sync_openapi.py
All checks passed!

$ mypy --config-file services/ml-api/pyproject.toml services/ml-api/app
Success: no issues found in 73 source files

$ python3 scripts/sync_openapi.py --check
OK: OpenAPI contract is up to date with canonical FastAPI application.
```

### Frontend (`node --test` + `tsc` + `eslint`)
```bash
$ npm test
ℹ tests 139
ℹ suites 32
ℹ pass 139
ℹ fail 0
ℹ duration_ms 210.54

$ npm run type-check
> tsc --noEmit
Exit code: 0

$ npm run lint
✔ No ESLint warnings or errors
Exit code: 0
```

### Verificación de Artefactos de Release
```bash
$ node scripts/verify-release-artifact.mjs --max-age-minutes 180
✓ RELEASE ARTIFACT VERIFICATION PASSED
  Commit:   17150204b476bd3a7ef6bfd1f69b829b5f61cd8b (release/r1-2026-11)
  Build ID: zpQIiKWfgsUZEW7tHsyyd
  Size:     2.2 KB
  Date:     2026-11-20T04:33:23.439Z
```

---

## 5. Decisiones Arquitectónicas Relevantes

1. **Gobernanza de Umbrales (Rule 5.1):** Ningún umbral predictivo ($\tau$) ni parámetro adaptativo (cooldown de 24 horas) permanece cableado en controladores. Se cargan de forma desacoplada desde `Settings`.
2. **Serialización Concurrente por Estudiante (Advisory Locks):** Para evitar condiciones de carrera donde dos intentos simultáneos emitan recomendaciones idénticas, se implementó `pg_advisory_xact_lock(hashtext('adaptation_' || student_id))` a nivel de transacción de PostgreSQL. Esta técnica previene bloqueos de tabla completos, no altera el esquema DDL y se libera automáticamente al terminar la transacción.
3. **Ordenamiento Canónico Anti-Deadlock:** Al persistir lotes de estados de dominio en `student_knowledge_states` mediante `INSERT ... ON CONFLICT DO UPDATE`, los registros se ordenan lexicográficamente por `knowledge_component_id`, eliminando el riesgo de que dos transacciones concurrentes compitan por filas en orden inverso.
4. **Append-Only y Causalidad Temporal:** Los registros de `answer_events` continúan siendo de solo inserción. La extracción histórica respeta la frontera causal $t \le t_{\text{ref}}$, garantizando que el modelo predictivo opere sin fuga temporal de datos.

---

## 6. Estado del Pull Request y CI en GitHub

- **Pull Request Activo:** PR #1 (`https://github.com/TF4ir/PlataformaMicro/pull/1`), rama `release/r1-2026-11` hacia `main`.
- **GitHub Actions (Workflow Run `44673867178`):**
  - Contracts & OpenAPI Drift Check: **Exitoso (39s)**
  - Frontend Quality & Security Verification: **Exitoso (31s)**
  - Backend Code Quality & Typing: **Exitoso (49s)**
- **Limitación Externa Documentada:** El check externo `Workers Builds: plataformamicro` reporta fallo en Cloudflare Dashboard debido a que los secretos de enlace a Cloudflare Pages/Workers residen en la infraestructura del proveedor y no en GitHub Actions. La verificación local del artefacto OpenNext pasa al 100% mediante `verify-release-artifact.mjs`.

---

## 7. Siguiente Tarea Recomendada

- **Fase R3 / M3.2:** Integración del editor de preguntas del docente con persistencia directa en base de datos PostgreSQL, unificando la generación asistida por LLM con la asignación a unidades didácticas y componentes de conocimiento canónicos.
