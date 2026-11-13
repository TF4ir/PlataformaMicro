# 00 — Alcance y método de auditoría UI/UX

**Proyecto:** Plataforma de Microaprendizaje Adaptativo (5.° de secundaria)
**Repositorio:** `/root/PlataformaMicro`
**Fecha de auditoría:** 2026-11-07
**Rama:** `main`
**Commit auditado:** `415027069981a5addd89b15de0fa828fdcc90e7b` (`4150270`, 2026-11-06 01:26:11 -0500)
**Mensaje del commit:** `fix(ci): isolate npm cache in .npmrc and synchronize typescript 5.9.3 dependency to fix EINTEGRITY`
**Naturaleza:** auditoría de solo lectura, basada en inspección de código, rutas reales y capturas de pantalla.
**Entregables:** cinco documentos en `docs/ui-ux/2026-11-07/` y evidencia PNG en `docs/ui-ux/2026-11-07/evidence/`.

---

## 1. Objetivo

Evaluar la calidad visual, la usabilidad, la accesibilidad y la coherencia de los flujos de estudiante y docente de la aplicación web existente, con el fin de producir un diagnóstico priorizado y una dirección de rediseño accionable para el Sprint 0.

La auditoría busca responder cinco preguntas:

1. ¿La interfaz permite completar los flujos núcleo de estudiante y docente sin bloqueos?
2. ¿La información que se muestra es comprensible, consistente y honesta respecto de su origen y certeza?
3. ¿La interfaz es usable en móvil (390 px) y escritorio (1440 px) para estudiantes de 16–17 años y docentes?
4. ¿Se cumplen los criterios relevantes de WCAG 2.2 AA y los estándares internos del proyecto?
5. ¿Qué cambios tienen mayor impacto y menor riesgo para las siguientes iteraciones?

---

## 2. Alcance

### Incluido

- Las 18 rutas del App Router de `apps/web/src/app/`.
- El shell global: `AppShell`, `Sidebar`, `Header`, contexto de rol y guardas de `middleware.ts`.
- Componentes compartidos de UI: `button`, `card`, `badge`, `progress`.
- Páginas de estudiante, docente, autenticación y estado del sistema.
- Estados de carga, vacío, error y datos de reserva (fallbacks).
- Revisión heurística de usabilidad, consistencia visual, jerarquía, copy y carga cognitiva.
- Revisión de accesibilidad basada en WCAG 2.2 AA, con verificación de código y evidencia visual.
- Comportamiento responsive a 390 × 844 px y 1440 × 1000 px.
- Flujos extremo a extremo de estudiante y docente.

### Excluido

- Modificación de código, configuración, dependencias, variables de entorno, autenticación, RLS, API o artefactos ML.
- Instalación de paquetes, Playwright, skills o herramientas.
- Pruebas de carga, rendimiento, seguridad ofensiva o penetration testing.
- Validación formal de accesibilidad con lectores de pantalla reales (NVDA, VoiceOver, TalkBack).
- Certificación legal de protección de datos o de la Ley N.° 29733.
- Evaluación de la exactitud estadística de DAS3H, PFA o BKT.
- Validación de datos productivos reales: el backend FastAPI no estaba disponible.
- Cambios en Supabase, migraciones, políticas RLS o datos.

---

## 3. Restricciones operativas respetadas

| Restricción | Cumplimiento |
|---|---|
| No modificar código de la aplicación | Sí. `git status` no muestra cambios en `apps/web/`. |
| No modificar configuración, paquetes ni entorno | Sí. Sin cambios en `package.json`, `next.config.mjs`, `.env.local` ni Tailwind. |
| No ejecutar escrituras git | Sí. No se usó `add`, `commit`, `checkout`, `switch`, `reset`, `clean`, `stash`, `merge`, `rebase` ni `push`. |
| No detener servidores o contenedores compartidos | Sí. Solo se detuvo, al final, el servidor de auditoría propio. |
| No instalar dependencias ni Playwright | Sí. Se usó un binario de Chrome headless ya presente en la máquina. |
| No usar mocks ni datos fabricados en la auditoría | Sí. No se crearon mocks de API ni datasets ficticios; las capturas usan los fallbacks reales del código y cookies sintéticas de sesión, documentadas en la sección 7. |
| No afirmar umbrales o resultados de modelo | Sí. No se emitieron juicios sobre AUC, Brier o calibración. |

---

## 4. Skills y capacidades

### Skills solicitadas

| Skill | Disponibilidad | Acción |
|---|---|---|
| UI/UX Pro Max | **No instalada** en el repositorio ni en el registro local de skills. | No se instaló. Se sustituyó por la skill local `ux-usability` y revisión heurística propia. |
| Vercel `web-design-guidelines` | **No instalada**. | No se instaló. Se usaron WCAG 2.2 AA y criterios de diseño propios. |
| Vercel `building-components` | **No instalada**. | No se instaló. La revisión de componentes se hizo por inspección directa. |

### Skills locales disponibles y usadas

| Skill | Uso en esta auditoría |
|---|---|
| `ux-usability` | Criterios de carga cognitiva, microlearning 3–5 min, microcopy empático, objetivos táctiles de 44 × 44 px y ergonomía docente. |
| `frontend-development` | Contexto de App Router, Server/Client Components, Tailwind y patrones de consumo de API. |
| `architecture-design` | Verificación de fronteras frontend/backend y coherencia de contratos. |
| `improve-animations` | Criterios de movimiento, animación decorativa y `prefers-reduced-motion`. |

No se cargaron skills de modelado, EDA, entrenamiento ni evaluación porque no forman parte del alcance de esta auditoría.

---

## 5. Entorno técnico observado

| Elemento | Valor observado |
|---|---|
| Framework | Next.js 14.2.x (14.2.35 en ejecución) |
| React | 18.3.1 |
| Tailwind CSS | 3.4.x (3.4.19 en ejecución) |
| Tipografía real | `system-ui`, `-apple-system`, `Segoe UI`, `Roboto`, `Helvetica Neue`, `Arial` |
| Tipografía documentada | Inter, según `docs/ux/design-specs.md` |
| Primitivas UI | Componentes locales en `apps/web/src/components/ui/`; no hay paquete shadcn/ui instalado |
| Iconografía | `lucide-react` |
| Gráficos | Recharts |
| Formularios | React Hook Form y Zod instalados, pero poco usados en las pantallas auditadas |
| Backend FastAPI | **No disponible** durante la auditoría (`http://127.0.0.1:8000` → conexión rechazada) |
| Supabase local | Disponible (`http://127.0.0.1:54321` → HTTP 200) |
| Autenticación demo | Habilitada en `.env.local`; no se usaron credenciales reales |
| Servidor de capturas | Copia aislada en `/tmp/opencode/nexo-audit`, puerto 3100 |

---

## 6. Método

La auditoría siguió siete pasos:

1. **Reconocimiento del repositorio.** Lectura de `AGENTS.md`, `apps/web/AGENTS.md`, `docs/ux/design-specs.md`, `package.json`, `tailwind.config.ts`, `globals.css` y `middleware.ts`.
2. **Inventario de rutas.** Identificación de las 18 páginas del App Router y de sus layouts, guardas y fuentes de datos.
3. **Lectura de código por pantalla.** Revisión de cada `page.tsx`, componentes compartidos, clientes de API y lógica de fallback.
4. **Auditoría heurística.** Evaluación con diez heurísticas de Nielsen adaptadas a un producto educativo: visibilidad del estado, correspondencia con el mundo real, control y libertad, consistencia, prevención de errores, reconocimiento, eficiencia, estética minimalista, recuperación de errores y ayuda.
5. **Auditoría de accesibilidad.** Contraste, jerarquía de encabezados, etiquetas de formulario, foco, semántica de tablas, modales, gráficos, movimiento y mensajes de estado, contrastados con WCAG 2.2 AA.
6. **Revisión responsive.** Capturas a 390 px y 1440 px; análisis de reflow, truncamiento, solapamientos, densidad y objetivos táctiles.
7. **Recorrido de flujos.** Simulación estática del recorrido completo de estudiante y docente, incluyendo estados de error y vacío.

### Criterios de severidad

| Prioridad | Definición | Criterio de acción |
|---|---|---|
| **P0** | Bloquea un flujo núcleo, genera una afirmación falsa sobre datos o incumple una restricción arquitectónica crítica. | Corregir antes de cualquier piloto o demostración con usuarios. |
| **P1** | Dificulta seriamente la tarea, excluye a usuarios o erosiona la confianza de forma sistemática. | Corregir en el Sprint 1. |
| **P2** | Genera fricción, inconsistencia o deuda de diseño con impacto moderado. | Planificar en Sprints 1–2. |
| **P3** | Detalle de pulido, copy menor o mejora incremental. | Backlog de pulido. |

### Tipos de hallazgo

| Tipo | Definición |
|---|---|
| **Defecto** | Comportamiento incorrecto, roto o engañoso respecto de lo que la interfaz afirma. |
| **Inconsistencia** | Dos partes del producto dicen o hacen cosas distintas para el mismo concepto. |
| **Mejora** | La interfaz funciona, pero puede ser más clara, rápida o accesible. |
| **Hipótesis** | Observación que requiere validación con usuarios o con datos productivos; no se afirma como defecto. |

---

## 7. Captura de evidencia

### Método

Las capturas se obtuvieron de una **copia aislada** de `apps/web` en `/tmp/opencode/nexo-audit`, no del árbol de trabajo compartido. La copia recibió únicamente `distDir: ".next-audit"` para no tocar el directorio `.next` del repositorio.

- Servidor: `next dev -p 3100`.
- Navegador: `chrome-headless-shell` ya instalado en `~/.cache/ms-playwright/chromium_headless_shell-1243/`.
- Automatización: script Node propio sobre Chrome DevTools Protocol (`/tmp/opencode/shoot.mjs` y `/tmp/opencode/shoot2.mjs`).
- Resoluciones: 1440 × 1000 px (escritorio) y 390 × 844 px (móvil), `deviceScaleFactor: 1`.
- Espera: evento `Page.loadEventFired` + 4.5 s para permitir fallos de red y fallbacks.
- Cookies sintéticas para rutas autenticadas: `nexo_session=session_active_audit`, `nexo_role=student|teacher`, `nexo_user_name=Estudiante Demo|Docente Demo`.
- Las rutas públicas (`/recovery`) se capturaron sin cookies.
- No se inició sesión real, no se enviaron formularios y no se escribió en Supabase.

### Por qué una copia aislada

El repositorio compartido no tenía un servidor de desarrollo propio en ejecución; el único `next-server` visible pertenecía a otro proceso (`v16.4.3`) y no al proyecto. Levantar el servidor dentro del repositorio habría creado `.next` y podría haber interferido con el trabajo de otro agente. La copia aislada permitió capturar la aplicación real sin tocar configuración ni artefactos compartidos.

### Limitaciones de la captura

- El backend FastAPI estaba caído; por tanto, varias pantallas muestran datos de fallback de Supabase o constantes de demostración. Esto **no invalida** los hallazgos sobre estados vacíos, errores y honestidad de datos; de hecho, los hace visibles.
- Las cookies sintéticas permiten entrar a las rutas, pero no representan una sesión Supabase real. La identidad mostrada en la barra lateral es la de la cookie (`Estudiante Demo` / `Docente Demo`), no la del usuario de Supabase. Esto se documenta como limitación y no se trata como defecto de producto salvo cuando la inconsistencia también existe en el código.
- Las capturas son de viewport, no de página completa. Las secciones inferiores se revisaron en código cuando no aparecen en la imagen.
- No se probó con lector de pantalla real ni con teclado físico; los hallazgos de accesibilidad se basan en semántica, contraste calculado y patrones de código.
- No se probó con datos productivos ni con un backend en frío real.

---

## 8. Procedencia de los datos observados

La aplicación usa una cadena de tres niveles:

1. **FastAPI** (`NEXT_PUBLIC_API_URL`, por defecto `http://localhost:8000`).
2. **Supabase** local o remoto, consultado desde el cliente cuando FastAPI falla.
3. **Constantes de demostración** embebidas en `src/lib/api/learning.ts`, `src/lib/api/teacher.ts` y `src/lib/api/content-generation.ts`.

En la auditoría, el nivel 1 falló. Algunas consultas al nivel 2 devolvieron datos; otras devolvieron vacío y activaron el nivel 3. Por eso conviven en la misma sesión:

- Una página de estudiantes con **0 estudiantes**.
- Un reporte docente con **10 estudiantes**, **120 intentos** y **69.2 %**.
- Un dashboard estudiantil con **12 actividades**, **45 min**, **3/5** conceptos y **69.4 %**, aunque no haya cursos ni repasos.
- Una recomendación de **Fotosíntesis** aunque no exista recomendación real.

Estas contradicciones se documentan como hallazgos P0/P1 porque el código las produce también con datos vacíos en producción, no solo porque el backend estuviera caído.

---

## 9. Índice de evidencia

| # | Archivo | Pantalla | Viewport |
|---|---|---|---|
| 1 | `evidence/login-desktop-1440.png` | Inicio de sesión | 1440 |
| 2 | `evidence/login-mobile-390.png` | Inicio de sesión | 390 |
| 3 | `evidence/recovery-desktop-1440.png` | Recuperación de acceso | 1440 |
| 4 | `evidence/recovery-mobile-390.png` | Recuperación de acceso | 390 |
| 5 | `evidence/student-dashboard-desktop-1440.png` | Dashboard estudiante | 1440 |
| 6 | `evidence/student-dashboard-mobile-390.png` | Dashboard estudiante | 390 |
| 7 | `evidence/student-courses-desktop-1440.png` | Mis cursos | 1440 |
| 8 | `evidence/student-progress-desktop-1440.png` | Mi progreso | 1440 |
| 9 | `evidence/student-progress-mobile-390.png` | Mi progreso | 390 |
| 10 | `evidence/student-recommendations-desktop-1440.png` | Recomendaciones | 1440 |
| 11 | `evidence/student-recommendation-detail-desktop-1440.png` | Detalle de recomendación | 1440 |
| 12 | `evidence/student-learn-error-state-1440.png` | Microlección (error) | 1440 |
| 13 | `evidence/student-quiz-error-state-1440.png` | Cuestionario (sin preguntas) | 1440 |
| 14 | `evidence/system-status-desktop-1440.png` | Estados del sistema | 1440 |
| 15 | `evidence/teacher-dashboard-desktop-1440.png` | Dashboard docente | 1440 |
| 16 | `evidence/teacher-dashboard-mobile-390.png` | Dashboard docente | 390 |
| 17 | `evidence/teacher-courses-desktop-1440.png` | Gestión de cursos | 1440 |
| 18 | `evidence/teacher-activities-desktop-1440.png` | Cuestionarios y actividades | 1440 |
| 19 | `evidence/teacher-questions-desktop-1440.png` | Banco de preguntas | 1440 |
| 20 | `evidence/teacher-students-desktop-1440.png` | Estudiantes | 1440 |
| 21 | `evidence/teacher-reports-desktop-1440.png` | Reportes | 1440 |

---

## 10. Estado del repositorio al cierre

```text
Rama: main
Commit: 4150270
Cambios rastreados: ninguno
Archivos no rastreados previos:
  ?? .dockerignore
  ?? docs/CLOUD_RUN_DEPLOYMENT_READINESS.md
Archivos nuevos de esta auditoría:
  ?? docs/ui-ux/
```

No se modificó ningún archivo de `apps/web/`, `services/`, `ml/`, `packages/`, `supabase/` ni configuración raíz. La única escritura en el repositorio fue la creación de `docs/ui-ux/2026-11-07/` y sus evidencias, dentro del alcance autorizado.

---

## 11. Declaración de integridad

- No se inventaron hallazgos: cada uno se vincula a una captura, a una ruta y/o a líneas de código concretas.
- No se presentaron datos de demostración como datos productivos.
- No se afirmó que un umbral, una probabilidad o una métrica de modelo fueran correctos.
- No se recomienda eliminar funcionalidades existentes; las propuestas buscan aclararlas, hacerlas verificables o sustituir simulaciones por estados honestos.
- Las estimaciones de complejidad son orientativas y deberán reestimarse con el equipo de implementación.
