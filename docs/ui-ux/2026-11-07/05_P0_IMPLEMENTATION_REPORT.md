# 05 — Informe de implementación P0 (UI/UX)

**Proyecto:** Plataforma de Microaprendizaje Adaptativo
**Fecha:** 2026-11-08
**Base de auditoría:** `02_UI_UX_AUDIT.md` (39 hallazgos) y `03_REDESIGN_BACKLOG.md`
**Alcance ejecutado:** únicamente BL-01, BL-02, BL-03 y BL-04
**Estado:** implementado y validado localmente; **pendiente de revisión y aprobación**

---

## 0. Resumen ejecutivo

Se corrigieron los cinco defectos P0 de confianza y veracidad de datos:

| Hallazgo | Descripción | Estado |
|---|---|---|
| `A-01` | Métricas de estudiante fabricadas presentadas como reales | Corregido |
| `A-02` | Agregados e insights docentes ficticios | Corregido |
| `A-03` | Recuperación de contraseña simulada | Corregido (estado honesto de coordinación) |
| `A-04` | Contenido de reserva acoplado a Ciencias / Fotosíntesis | Corregido |
| `A-05` | Estado del sistema afirmaba salud y seguridad no verificadas | Corregido |

Resultados de validación local:

- `npm test`: **52 pruebas, 0 fallos** (incluye 15 pruebas nuevas de integridad de datos).
- `npm run type-check`: **sin errores**.
- `npm run build`: **compilación exitosa**, 17 páginas estáticas generadas.
- `npm run lint`: **no ejecutable** en este entorno (falta configuración de ESLint y `next lint` es interactivo). No se modificó configuración ni dependencias.
- Verificación responsive: 7 rutas × 3 anchos (390/768/1440 px), **21 capturas**, sin desbordamiento horizontal del documento.
- La verificación con datos vivos y el restablecimiento nativo de Supabase **no pudieron comprobarse** en este entorno. Ver `06_BACKEND_DATA_CONTRACT_GAPS.md`.

---

## 1. Alcance y restricciones respetadas

### 1.1 Permitido y utilizado

- `apps/web/**`: componentes, páginas, clientes de datos y pruebas.
- `docs/ui-ux/**`: documentación y evidencias nuevas.

### 1.2 No modificado

- Backend `services/ml-api/**` (los cambios existentes de Antigravity permanecen intactos).
- `ml/**`, migraciones SQL, RLS, configuración de Supabase, Docker, Cloud Run, variables de entorno y secretos.
- `packages/contracts/openapi/openapi.json` (no se cambió ningún contrato de backend).
- Dependencias, lockfiles, librerías de UI y gestores de estado.
- No se ejecutó ninguna operación Git de escritura (checkout/switch/reset/clean/stash/add/commit/push).
- No se borraron ni sobrescribieron los documentos de auditoría previos.

### 1.3 Fuera de alcance (no implementado)

BL-05 a BL-20, búsqueda global, notificaciones, rediseño completo, modales/tablas/gráficos genéricos, reestructuración de navegación, gamificación, nuevas métricas, endpoints, tablas o migraciones.

---

## 2. BL-01 — Datos veraces y procedencia explícita

### 2.1 Causa raíz

Los clientes de datos devolvían valores numéricos de reserva (por ejemplo `69.4 %`, `80 %`, `2/3 aciertos`, nombres y cursos fijos) cuando Supabase no devolvía filas o fallaba. Las vistas no distinguían entre:

1. una consulta exitosa con cero observaciones,
2. una consulta exitosa sin denominador suficiente,
3. una consulta fallida o no disponible.

### 2.2 Módulo compartido de procedencia

Se creó `apps/web/src/lib/data-provenance.ts`, sin dependencias de React/Next, con:

- Tipos `DataProvenance` (`observed | estimated | synthetic | demo | unavailable`) y `MetricStatus`.
- `observedCount`, `formatCountMetric`, `observedPercentage`, `observedPercentageValue`, `formatMetricValue`, `formatMetricWithMeta`.
- `classifyMastery`, `buildProficiencyDistribution`, `summarizeAttempt`.
- `resolveCourseName`, `resolveKnowledgeComponentName`, `resolveContentTitle`, `selectContentRenderer`.
- `formatLatency`, `formatVerificationTimestamp`.
- `isDemoModeEnabled`, `DEMO_BANNER_TEXT`.
- Umbrales configurables: `NEXT_PUBLIC_MASTERY_CONSOLIDATED_THRESHOLD` (80), `NEXT_PUBLIC_MASTERY_IN_PROGRESS_THRESHOLD` (55), `NEXT_PUBLIC_MASTERY_MIN_SAMPLE` (1).

Regla central: **ningún valor numérico de reserva**. Un `null` nunca se convierte en `0`.

### 2.3 Comportamiento resultante

| Situación | Antes | Después |
|---|---|---|
| Consulta exitosa con 0 filas | `0` o valor inventado | `0` observado (válido) |
| Métrica sin denominador | `0 %` / `69.4 %` | «Sin evidencia suficiente» |
| Consulta fallida | `0` o dato fijo | «No disponible» + aviso de error |
| Intento con 0 aciertos de N | Podía fabricar aciertos | `0` real conservado |
| Intento sin respuestas | Generaba resultado | No genera resultado |
| Curso/KC/contenido ausente | «Ciencias» / «Fotosíntesis» | «Curso sin nombre» / metadatos o «No disponible» |
| Distribución docente | 3 categorías, suma incoherente | 4 categorías; cada fila en exactamente una |

### 2.4 Cambios por archivo

- `src/lib/api/learning.ts`
  - Eliminados nombres, cursos, KC, puntajes y métricas de reserva.
  - `getDashboard`, `getProgress`, `startActivity`, `submitAnswer`, `submitAttempt` y resultados usan datos reales de Supabase.
  - Si no hay sesión autenticada, se lanza un error honesto en lugar de usar UUID de demostración.
  - Los intentos vacíos no generan resultados.
- `src/lib/api/teacher.ts`
  - Nómina, dashboard, mapa de calor, resumen por sección y trayectoria de 6 semanas calculados desde Supabase.
  - `average_accuracy` y `observed_accuracy` son `number | null`.
  - `ai_insight: null` cuando no existe un modelo validado.
  - Distribución coherente con bucket `insufficient_evidence`.
  - Exportación CSV usa `student_code` o `sin_codigo`; el botón ya no afirma «seudonimizado» sin verificación.
- `src/lib/api/content-generation.ts`
  - `getCourses` y `getCourseKnowledgeComponents` devuelven `[]` ante fallo, sin fixtures de Ciencias.
- `src/app/(student)/dashboard/page.tsx`
  - KPIs con `metric_meta`; sin «Métricas reales» ni «Retención Óptima».
  - Estados de error no se presentan como «no tienes repasos/cursos».
  - Duración y puntaje nulos se muestran como «Duración no reportada» / «—».
- `src/app/(student)/progress/page.tsx`
  - KPIs y tabla KC con valores nulos seguros.
  - Umbral mostrado desde configuración, no «Retención > 80 %».
  - Estados vacíos distinguen fallo de consulta de ausencia real de datos.
- `src/app/(student)/quiz/[id]/results/page.tsx`
  - Guarda para intentos sin respuestas (`total_questions <= 0`).
  - Umbrales de dominio desde configuración.
  - Copy ajustado a evidencia observada.
- `src/app/teacher/dashboard/page.tsx`
  - KPIs `No disponible` cuando no hay datos.
  - Distribución de 4 buckets con porcentajes coherentes.
  - Listas con estado de error explícito.
- `src/app/teacher/reports/page.tsx`
  - Métricas nulas, mapa de calor vacío honesto, insights ausentes explicados.
  - Títulos en español y sin proyecciones inventadas.
- `src/app/teacher/students/page.tsx`
  - Precisión nula segura y contadores `—` cuando la consulta falla.
- `src/components/layout/app-shell.tsx`
  - `DemoBanner` persistente solo si `isDemoModeEnabled()`.
- `src/lib/role-context.tsx`, `src/components/layout/sidebar.tsx`, `src/app/(auth)/login/page.tsx`
  - Eliminados nombres/códigos/UUID de reserva; el código ausente se muestra como «Sin código».
- `src/types/ui.ts`
  - Tipos de estado del sistema con nulos explícitos y estados de seguridad `verified | unverified | failed`.

### 2.5 Pruebas de BL-01 (10 comportamientos requeridos)

| # | Comportamiento | Prueba |
|---|---|---|
| 1 | Cero observado ≠ sin datos | `data-integrity.test.mjs` #1 |
| 2 | Sin evidencia ≠ 0 | #2, #8 |
| 3 | Error/no disponible ≠ 0 | #3 |
| 4 | 0 aciertos de N se conserva | #4 |
| 5 | Intento vacío no genera resultado | #5 |
| 6 | Clasificación de dominio coherente | #6 |
| 7 | Distribución docente coherente (4 buckets) | #7 |
| 8 | `metric_meta` prevalece sobre el valor | #8 |
| 9 | Denominador vacío nunca produce porcentaje | #9 |
| 10 | Modo demo solo con bandera explícita + banner | #15 |

---

## 3. BL-02 — Recuperación de contraseña real u honesta

### 3.1 Decisión

No existe en el repositorio un flujo nativo completo de restablecimiento:

- No hay ruta de callback (`/auth/reset` o equivalente).
- `supabase/config.toml` solo declara `site_url = "http://localhost:3000"` y `additional_redirect_urls = ["https://localhost:3000"]`.
- `enable_signup = false`.
- La tabla `auth_recovery_pins` existe en SQL, pero **no hay endpoint ni Server Action** que valide el PIN o actualice la contraseña.

Por tanto, se implementó el estado honesto de **coordinación con la institución**, sin formulario, sin PIN y sin simulación de éxito.

### 3.2 Cambios

`src/app/(auth)/recovery/page.tsx` fue reescrito:

- Explica que la pantalla **no** restablece contraseñas automáticamente.
- Declara que no se envían mensajes ni se simulan cambios.
- Presenta tres pasos de coordinación: contacto, verificación de identidad e indicaciones.
- Sin `setTimeout`, sin `isSuccess`, sin campos de PIN/contraseña.

### 3.3 Limitación documentada

El flujo nativo de Supabase Auth (`resetPasswordForEmail` + callback + `updateUser`) queda como trabajo futuro y depende de backend/configuración. Ver `06_BACKEND_DATA_CONTRACT_GAPS.md`.

---

## 4. BL-03 — Contenido agnóstico a la asignatura

### 4.1 Causa raíz

Los fallbacks incluían Ciencias, Fotosíntesis, Genética y textos asociados. Además, `/learn/[id]` elegía un diagrama especializado mediante `title.includes("fotosíntesis")`.

### 4.2 Cambios

- Eliminados los fixtures de Ciencias en `content-generation.ts`, `recommendations/[id]`, `quiz/[id]` y textos de ejemplo de docentes.
- `MicrocontentBody` ahora admite `diagram_key?: string`.
- `selectContentRenderer` decide únicamente por:
  1. `content_body.diagram_key`, o
  2. `content_type`.
  Nunca por el título.
- Títulos, cursos, KC y duración provienen de los metadatos del microcontenido.
- Si falta la duración, se muestra «Duración no reportada» (no `2 min` ni `3 min`).
- Placeholders de docentes cambiados a «Concepto central de la unidad/actividad».

### 4.3 Prueba de Historia

`data-integrity.test.mjs` #10 crea un curso «Historia», un KC «Revolución Industrial» y un contenido «Causas de la Revolución Industrial», y verifica que la UI resuelve esos nombres sin sustituirlos por Ciencias. La prueba #11 verifica que un título con «Fotosíntesis» **no** activa el diagrama si `content_type`/`diagram_key` no lo indican.

---

## 5. BL-04 — Estado del sistema honesto

### 5.1 Cambios en `/system-status`

- `INITIAL_STATUS` ya no afirma salud ni seguridad: `apiStatus: "unavailable"`, latencia `null`, modelo `null`, RLS/seudonimización `unverified`.
- La latencia solo se muestra si la petición HTTP terminó y fue cronometrada; si no, «No medida».
- El modelo activo solo se muestra si el servicio lo reporta; si no, «No reportado por el servicio».
- Cold start solo si el servicio lo reporta; si no, «No reportado».
- RLS, multi-tenancy, seudonimización y exposición de PII: «No verificado».
- Certificación: «No emitida».
- Fecha y hora de verificación con fecha, hora y zona `America/Lima`.
- Eliminada la afirmación de certificación de seguridad.

### 5.2 Nota de verificación

El endpoint real `GET /api/v1/health` devuelve únicamente:

```json
{ "status": "ok", "service": "ml-api" }
```

No reporta modelo activo, cold start ni latencia. Por eso la UI no puede mostrar esos datos y lo declara explícitamente.

---

## 6. Pruebas automatizadas

### 6.1 Archivo nuevo

`apps/web/src/tests/data-integrity.test.mjs`: 15 pruebas, importando directamente `src/lib/data-provenance.ts` mediante type stripping de Node 22.

| Bloque | Pruebas |
|---|---|
| BL-01 | 1–9 y 15 |
| BL-03 | 10–11 |
| BL-04 | 12–14 |

### 6.2 Resultado

```text
# tests 52
# suites 6
# pass 52
# fail 0
# cancelled 0
# skipped 0
```

Comando: `npm test` dentro de `apps/web/`.

---

## 7. Validación técnica

### 7.1 TypeScript

```text
> tsc --noEmit
(sin errores)
```

### 7.2 Build de producción

```text
▲ Next.js 14.2.35
✓ Compiled successfully
✓ Generating static pages (17/17)
```

Rutas generadas: 19 (17 estáticas + `/learn/[id]`, `/quiz/[id]`, `/quiz/[id]/results`, `/recommendations/[id]` dinámicas).

### 7.3 Lint — limitación

`npm run lint` ejecuta `next lint`, que abre un asistente interactivo porque no existe configuración de ESLint:

```text
? How would you like to configure ESLint?
❯ Strict (recommended)
  Base
  Cancel
```

No se creó configuración ni se instalaron dependencias porque el alcance lo prohíbe. **No se declara lint como aprobado.**

---

## 8. Verificación responsive

### 8.1 Método

- Build de producción servido con `next start -p 3200`.
- Chrome headless del caché de Playwright, controlado por CDP.
- Cookies sintéticas `nexo_session` y `nexo_role` para atravesar el middleware.
- Anchos: **390, 768 y 1440 px**.
- Rutas: `/dashboard`, `/progress`, `/teacher/dashboard`, `/teacher/reports`, `/teacher/students`, `/system-status`, `/recovery`.

### 8.2 Resultado

- **21 capturas** en `docs/ui-ux/2026-11-07/evidence-p0/`.
- `responsive-results.json` con ancho, scrollWidth, scrollHeight, H1 y elementos desbordados.
- **Ninguna ruta presentó desbordamiento horizontal del documento** (`scrollWidth === innerWidth` en los 21 casos).
- Las tablas anchas usan `overflow-x-auto` interno (scroll horizontal localizado, no de página).

### 8.3 Advertencia de interpretación

Las capturas se tomaron **sin una sesión real de Supabase** y con FastAPI detenido. Por diseño, muestran los estados honestos de error/no disponible, no el camino feliz con datos productivos. Sirven para verificar:

- que no aparecen cifras inventadas,
- que los estados de error son legibles,
- que el layout no se rompe en 390/768/1440 px.

No demuestran el renderizado de datos reales; eso requiere credenciales y backend activos.

---

## 9. Estado de Git y archivos

- Rama: `main`.
- Commit base: `415027069981a5addd89b15de0fa828fdcc90e7b`.
- Todos los cambios del sprint permanecen **sin commit**.
- No se revirtieron ni modificaron los archivos de backend que Antigravity tenía en curso.

Archivos frontend modificados: 22 (ver `git diff --stat -- apps/web`).
Archivos nuevos relevantes:

- `apps/web/src/lib/data-provenance.ts`
- `apps/web/src/tests/data-integrity.test.mjs`
- `docs/ui-ux/2026-11-07/05_P0_IMPLEMENTATION_REPORT.md`
- `docs/ui-ux/2026-11-07/06_BACKEND_DATA_CONTRACT_GAPS.md`
- `docs/ui-ux/2026-11-07/evidence-p0/` (21 PNG + JSON)

---

## 10. Pendientes, bloqueos y decisión solicitada

### 10.1 Bloqueos de verificación

1. **Datos vivos:** no se pudo validar el camino feliz porque no hay sesión Supabase real ni FastAPI disponible.
2. **Restablecimiento nativo:** no hay callback, redirect de producción ni entrega de correo institucional demostrada.
3. **Lint:** no hay configuración de ESLint y no se permite crearla en este alcance.

### 10.2 Recomendación

Aprobar los cambios P0 como corrección de veracidad y resiliencia, con la salvedad de que la validación con datos productivos y el flujo nativo de recuperación quedan pendientes de infraestructura.

### 10.3 Detención

Este informe cierra el alcance autorizado. **No se continúa con BL-05 ni con ningún otro ítem hasta recibir aprobación explícita.**
