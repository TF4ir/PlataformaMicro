# 06 — Brechas de contrato backend / datos (post-P0)

**Proyecto:** Plataforma de Microaprendizaje Adaptativo
**Fecha:** 2026-11-08
**Origen:** implementación UI/UX P0 (BL-01 a BL-04)
**Estado:** documento de análisis; **no se modificó backend, SQL, RLS ni contratos**

---

## 1. Propósito

Registrar las brechas detectadas entre lo que la UI necesita para ser veraz y lo que hoy exponen:

- el esquema de Supabase,
- la API FastAPI,
- `packages/contracts/openapi/openapi.json`,
- la configuración de Supabase Auth.

Este documento **no implementa** cambios. Sirve para priorizar el trabajo backend posterior y evitar que la UI vuelva a inventar datos para cubrir ausencias.

---

## 2. Resumen priorizado

| # | Brecha | Impacto | Prioridad sugerida |
|---|---|---|---|
| G-01 | `metric_meta` y métricas anulables no existen en contrato backend | La UI calcula procedencia localmente; consumidores externos no la reciben | Alta |
| G-02 | `/api/v1/health` no reporta modelo activo, cold start ni latencia | `/system-status` debe mostrar «No reportado» / «No medida» | Alta |
| G-03 | `WarmupResponse` del OpenAPI no coincide con la implementación | Contrato roto; clientes tipados fallarían | Alta |
| G-04 | No existe callback ni redirect de producción para reset de contraseña | Recuperación real imposible; solo estado honesto de coordinación | Alta |
| G-05 | `auth_recovery_pins` existe en SQL pero no tiene endpoint/Server Action | Tabla muerta; no se puede validar PIN ni cambiar clave | Alta |
| G-06 | Middleware confía en cookies `nexo_session`/`nexo_role` puestas por el cliente | Puerta de rutas no valida el JWT de Supabase | Crítica (seguridad) |
| G-07 | `recommendations.scheduled_for` existe en SQL pero no en OpenAPI | El frontend lo lee de Supabase; clientes de API no lo ven | Media |
| G-08 | `content_body.diagram_key` no está en ningún contrato | El renderizado especializado depende de un campo no documentado | Media |
| G-09 | No hay verificación real de RLS ni de seudonimización | `/system-status` debe mostrar «No verificado» | Media |
| G-10 | Los endpoints de analítica estudiante/docente no están en OpenAPI | Los tipos viven solo en TypeScript del frontend | Media |
| G-11 | Contrato de intento vacío no está definido | La UI lo trata como «sin resultado»; el backend podría devolver otra cosa | Media |
| G-12 | `ai_insight` no tiene procedencia ni modelo validado | La UI lo muestra como `null`; falta contrato si se habilita | Baja |

---

## 3. Detalle de brechas

### G-01 · Métricas anulables y `metric_meta`

**Situación actual**

La UI usa `MetricMeta` (definido en `apps/web/src/lib/data-provenance.ts`):

```ts
interface MetricMeta {
  status: "observed" | "insufficient_evidence" | "unavailable";
  provenance: "observed" | "estimated" | "synthetic" | "demo" | "unavailable";
  sample_size: number | null;
}
```

Las respuestas de analítica se calculan en el cliente a partir de filas de Supabase. No existe un contrato backend que entregue:

- valores `null` para métricas sin evidencia,
- `sample_size`,
- procedencia (`observed`, `estimated`, etc.).

**Riesgo**

Cada consumidor (web, futuras apps, reportes) puede volver a convertir `null` en `0` o inventar un fallback.

**Propuesta de contrato (no implementada)**

```json
{
  "observed_accuracy_percentage": null,
  "metric_meta": {
    "observed_accuracy_percentage": {
      "status": "insufficient_evidence",
      "provenance": "observed",
      "sample_size": 0
    }
  }
}
```

**Criterio de aceptación futuro**

- Ninguna métrica numérica es obligatoria si no tiene evidencia.
- `metric_meta` viaja junto al valor, no se deduce en el cliente.
- `sample_size` es explícito y verificable.

---

### G-02 · Health endpoint incompleto

**Situación actual**

`GET /api/v1/health` devuelve:

```json
{ "status": "ok", "service": "ml-api" }
```

No incluye:

- modelo activo (`DAS3H`, `PFA`, `BKT`, `rule_based_fallback`),
- tiempo de cold start,
- versión del artefacto,
- timestamp del servidor,
- estado de carga de artefactos.

**Impacto en UI**

`/system-status` muestra:

- «Modelo activo: No reportado por el servicio».
- «Cold start: No reportado».
- Latencia medida solo en el navegador, no reportada por el backend.

**Propuesta de contrato**

```json
{
  "status": "ok",
  "service": "ml-api",
  "model": {
    "active": "DAS3H",
    "artifact_version": "2026-11-01",
    "loaded": true
  },
  "cold_start_seconds": 12.4,
  "server_timestamp": "2026-11-08T06:00:00Z"
}
```

**Nota:** no se debe inventar `cold_start_seconds`; si no se mide, debe ser `null` u omitirse.

---

### G-03 · `WarmupResponse` no coincide con la implementación

**Contrato OpenAPI**

```json
{
  "required": ["status", "warmed", "models_loaded", "timestamp"],
  "properties": {
    "status": "string",
    "warmed": "boolean",
    "models_loaded": "array<string>",
    "timestamp": "date-time"
  }
}
```

**Implementación actual**

```json
{ "status": "ready", "warmed": "true" }
```

Discrepancias:

- `warmed` es `string` en la implementación y `boolean` en el contrato.
- Faltan `models_loaded` y `timestamp`.
- `status` devuelve `"ready"`, mientras el ejemplo del contrato usa `"healthy"`.

**Riesgo**

Cualquier cliente generado desde OpenAPI fallará al validar la respuesta.

---

### G-04 · Reset de contraseña sin callback ni redirect de producción

**Situación actual**

- No existe ruta frontend de callback (por ejemplo `/auth/reset` o `/auth/confirm`).
- `supabase/config.toml`:
  - `site_url = "http://localhost:3000"`
  - `additional_redirect_urls = ["https://localhost:3000"]`
  - `enable_signup = false`
- No se demostró entrega de correo institucional.

**Consecuencia**

No es posible implementar `supabase.auth.resetPasswordForEmail()` de extremo a extremo. La UI usa el estado honesto de coordinación con la institución.

**Trabajo backend/config requerido**

1. Definir URL de producción en `site_url` y `additional_redirect_urls`.
2. Crear ruta de callback que intercambie el token y permita `updateUser({ password })`.
3. Verificar entrega de correo y expiración de enlaces.
4. Definir rate limiting y auditoría del evento.

---

### G-05 · `auth_recovery_pins` sin API

**Situación actual**

La tabla existe con:

- `pin_hash`, `expires_at`, `used_at`, `created_by`, `student_id`, `tenant_id`.

Pero no hay:

- endpoint para crear un PIN,
- endpoint para validarlo,
- Server Action,
- función RPC documentada.

**Riesgo**

La tabla sugiere un flujo que no existe. La UI no debe exponer un formulario de PIN hasta que haya validación real.

**Decisión requerida**

- Eliminar la tabla si el flujo será Supabase Auth nativo, o
- implementar endpoints/RPC con hash, expiración, un solo uso y auditoría.

---

### G-06 · Middleware basado en cookies de cliente

**Situación actual**

`src/middleware.ts` protege rutas comprobando:

- `nexo_session` existe,
- `nexo_role` es `student` o `teacher`.

`role-context.tsx` crea `nexo_session` en el navegador:

```ts
setCookie("nexo_session", "session_active_" + Date.now(), 7);
```

**Riesgo**

La cookie no es un JWT de Supabase ni está firmada. Cualquier cliente puede crearla y atravesar el middleware. La autorización real de datos depende de RLS y de la sesión de Supabase, pero la navegación y el rol de UI no están criptográficamente validados.

**Trabajo requerido**

- Usar cookies de sesión de `@supabase/ssr` y validarlas en middleware/servidor.
- Derivar el rol de `profiles`/`user_metadata` verificado, no de una cookie editable.
- Mantener `nexo_role` solo como pista de UI, nunca como control de acceso.

**Nota:** este documento no modifica el middleware porque el alcance P0 era UI/UX y el cambio afecta autenticación.

**Actualización 2026-11-09 (P0.1):** G-06 queda resuelto. El middleware usa
`auth.getUser()` + `public.profiles.role`, las cookies `nexo_*` ya no se leen ni
se escriben, y se añadió una migración que impide la auto-escalada de
`profiles.role`. Ver `docs/security/2026-11-09/P0.1_AUTH_SECURITY_AUDIT.md`.

---

### G-07 · `recommendations.scheduled_for` fuera de OpenAPI

**Situación actual**

- La migración `20261103050000_recommendations_and_predictions_m53.sql` agrega `scheduled_for`.
- `RecommendationItem` en OpenAPI **no** incluye `scheduled_for`.
- El frontend lee `recommendations.scheduled_for` directamente de Supabase.

**Riesgo**

Clientes de la API no pueden ordenar ni mostrar repasos programados con el contrato actual.

**Propuesta**

Agregar `scheduled_for: string | null` (`format: date-time`) a `RecommendationItem` y a la respuesta de recomendaciones.

---

### G-08 · `diagram_key` no documentado

**Situación actual**

El frontend extendió `MicrocontentBody` con:

```ts
diagram_key?: string;
```

`selectContentRenderer` lo usa para elegir un renderizador especializado, junto con `content_type`. El campo vive dentro del JSONB `content_body` de Supabase y no aparece en OpenAPI.

**Riesgo**

- Contenido nuevo puede no saber qué clave usar.
- Un cambio de nombre rompe el renderizado sin error de contrato.

**Propuesta**

- Documentar `diagram_key` y los valores admitidos.
- Validar `content_type`/`diagram_key` al publicar microcontenido.
- Mantener la regla: **nunca** inferir el renderizador desde el título.

---

### G-09 · Sin verificación real de RLS ni seudonimización

**Situación actual**

No existe endpoint, script o comprobación en tiempo de ejecución que confirme:

- que RLS está habilitado en todas las tablas,
- que las políticas bloquean accesos cruzados,
- que los datos exportados están seudonimizados.

**Impacto en UI**

`/system-status` muestra «No verificado» en RLS, multi-tenancy, seudonimización y PII. Es correcto, pero deja al docente sin una verificación accionable.

**Propuesta**

- Endpoint de solo lectura con resultado de comprobaciones (o job programado).
- Salida con `verified_at`, `checks[]`, `status` y `evidence`.
- La UI solo debe mostrar «Verificado» si recibe esa evidencia.

---

### G-10 · Analítica sin contrato OpenAPI

**Situación actual**

`StudentDashboardResponse`, `StudentProgressDetailResponse`, `TeacherDashboardResponse`, `TeacherReportsResponse`, `TeacherStudentRecord` y `ProficiencyDistributionItem` son tipos TypeScript locales. No hay endpoints equivalentes en `openapi.json` (no existen rutas con `dashboard`).

**Riesgo**

- El contrato real es el esquema de Supabase + el código del frontend.
- Cambios de columnas rompen la UI sin una validación de contrato previa.

**Propuesta**

- Si la analítica se moverá a FastAPI, definir esquemas Pydantic y rutas primero.
- Si seguirá en Supabase, documentar las vistas/RPC y sus columnas como contrato estable.
- En ambos casos, incluir `metric_meta` (G-01).

---

### G-11 · Contrato de intento vacío

**Situación actual**

La UI asume:

- `total_questions === 0` ⇒ no hay resultado válido,
- `score` puede ser `0` y debe conservarse,
- un intento sin respuestas no genera desglose.

No está documentado si el backend:

- rechaza el envío,
- devuelve `total_questions: 0`,
- devuelve `score: null`,
- o genera un error de validación.

**Propuesta**

Definir explícitamente en OpenAPI:

```json
{
  "total_questions": 0,
  "correct_answers": 0,
  "score": null,
  "result_available": false
}
```

o un error `422` documentado. La UI ya tolera ambos, pero el contrato debe elegir uno.

---

### G-12 · `ai_insight` sin procedencia

**Situación actual**

`TeacherReportsResponse.ai_insight` es `TeacherAiInsight | null` y la implementación devuelve `null`. No existe modelo validado que respalde un insight.

**Riesgo**

Si en el futuro se agrega un texto generado o heurístico, la UI podría presentarlo como hallazgo validado.

**Propuesta**

Agregar a `ai_insight`:

- `provenance` (`observed | estimated | synthetic | demo | unavailable`),
- `model_version`,
- `validated_at`,
- `sample_size`,
- `limitations`.

Mientras no exista, mantener `null` y el estado «Sin insight validado por ahora».

---

## 4. Orden sugerido de trabajo backend

1. **G-06** (seguridad de sesión) — antes de cualquier piloto real.
2. **G-04 + G-05** (recuperación de contraseña) — desbloquea BL-02 nativo.
3. **G-02 + G-03** (health/warmup) — desbloquea un `/system-status` completo y contratos válidos.
4. **G-01 + G-10** (métricas y `metric_meta`) — evita que la UI vuelva a calcular procedencia localmente.
5. **G-09** (verificación RLS/seudonimización) — permite pasar de «No verificado» a evidencia real.
6. **G-07, G-08, G-11, G-12** — consistencia de contratos y contenido.

---

## 5. Confirmación de no cambio

Este documento no modificó:

- `services/ml-api/**`,
- `ml/**`,
- migraciones ni políticas RLS,
- `packages/contracts/openapi/openapi.json`,
- configuración de Supabase, Docker o Cloud Run,
- variables de entorno ni secretos.

Los cambios de backend que aparecen en `git status` son trabajo previo de Antigravity y no fueron tocados por este sprint.
