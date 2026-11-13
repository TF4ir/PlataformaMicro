# 01 — Inventario de pantallas

**Fecha:** 2026-11-07
**Commit:** `4150270`
**Total de rutas:** 18
**Total de capturas:** 21 (16 rutas; algunas con escritorio y móvil; 2 rutas solo por código)

---

## 1. Resumen

| Grupo | Rutas | Capturadas | Solo inspección de código |
|---|---:|---:|---:|
| Públicas / autenticación | 3 | 2 | 1 |
| Estudiante | 8 | 7 | 1 |
| Compartida | 1 | 1 | 0 |
| Docente | 6 | 6 | 0 |
| **Total** | **18** | **16** | **2** |

Rutas dinámicas: 4 (`/learn/[id]`, `/quiz/[id]`, `/quiz/[id]/results`, `/recommendations/[id]`). Se capturaron tres con identificadores de auditoría; `/quiz/[id]/results` solo se inspeccionó en código porque requiere un `attempt_id` válido.

### Distribución por rol

- **Público:** `/`, `/login`, `/recovery`.
- **Estudiante:** `/dashboard`, `/courses`, `/learn/[id]`, `/quiz/[id]`, `/quiz/[id]/results`, `/recommendations`, `/recommendations/[id]`, `/progress`.
- **Compartido autenticado:** `/system-status`.
- **Docente:** `/teacher/dashboard`, `/teacher/courses`, `/teacher/activities`, `/teacher/questions`, `/teacher/students`, `/teacher/reports`.

---

## 2. Shell global

| Elemento | Implementación | Observación |
|---|---|---|
| Layout raíz | `src/app/layout.tsx` | `RoleProvider` + `AppShell`; `lang="es"`; fondo `#f8fafc`. |
| Shell | `src/components/layout/app-shell.tsx` | Tres modos: autenticación (sin shell), aprendizaje inmersivo (`/learn`, `/quiz`, sin header/sidebar) y shell normal. |
| Sidebar | `src/components/layout/sidebar.tsx` | Fijo de 256 px en escritorio; drawer en móvil; navegación por rol; perfil y cierre de sesión. |
| Header | `src/components/layout/header.tsx` | 64 px, sticky; búsqueda global, chip de rol y campana. La búsqueda y la campana no tienen acción. |
| Guardas | `src/middleware.ts` | Cookies `nexo_session` y `nexo_role`; redirecciones por rol; `/system-status` compartida. |
| Contexto de rol | `src/lib/role-context.tsx` | Sesión Supabase o cookies; identidades demo; cambio de rol en cliente. |
| Primitivas | `src/components/ui/` | `Button`, `Card`, `Badge`, `Progress`; no hay paquete shadcn/ui. |
| Tokens | `src/app/globals.css`, `tailwind.config.ts` | Variables HSL + hex `#0A635F`, `#0B2D34`, `#69D7C9`; tipografía real `system-ui`. |

### Modos de navegación

1. **Autenticación:** `/login`, `/recovery`. Sin sidebar ni header. Diseño de dos columnas en escritorio y una columna en móvil.
2. **Inmersivo:** `/learn/*`, `/quiz/*`. Sin shell; el estudiante sale con enlaces explícitos. El quiz de resultados vuelve a mostrar el shell normal.
3. **Normal:** resto de rutas. Sidebar + header + contenido con `max-w-7xl`.

---

## 3. Pantallas públicas y de autenticación

### A-01 · `/` — Redirección raíz

| Campo | Valor |
|---|---|
| Rol | Público |
| Función | Redirige a `/login` o al dashboard según cookies. |
| Componentes | `src/app/page.tsx`; `middleware.ts`. |
| Datos | Cookies de sesión y rol. |
| Evidencia | No capturada; redirección verificada en código y en navegación. |
| Estado | Inspeccionada en código. |

### A-02 · `/login` — Inicio de sesión

| Campo | Valor |
|---|---|
| Rol | Público |
| Función | Autenticación con Supabase; selección de portal Estudiante/Docente; acceso demo. |
| Componentes | `SolarSystemOrbit`, tarjetas de rol, formulario, tabs móviles, botón de ayuda flotante, enlace “Ver presentación”. |
| Datos | Supabase Auth (`signInWithPassword`) y fallback demo condicionado por `NEXT_PUBLIC_ENABLE_DEMO_AUTH`. |
| Evidencia | `login-desktop-1440.png`, `login-mobile-390.png`. |
| Estado | Capturada en escritorio y móvil. Formulario no enviado. |

**Observaciones de inventario:** el formulario tiene etiquetas asociadas (`htmlFor`/`id`) y `aria-label` en el toggle de contraseña. No tiene `autocomplete`. La tarjeta de rol activa cambia el portal. En móvil, el panel de presentación se convierte en una pestaña.

### A-03 · `/recovery` — Recuperación de acceso

| Campo | Valor |
|---|---|
| Rol | Público |
| Función | Restablecer contraseña con PIN escolar o clave de respaldo. |
| Componentes | Tabs PIN/Clave, formulario de tres campos, caja de ayuda, estado de éxito. |
| Datos | **Ninguno.** `handleRecoverySubmit` usa `setTimeout` de 700 ms y muestra éxito sin llamar a Supabase ni a FastAPI. |
| Evidencia | `recovery-desktop-1440.png`, `recovery-mobile-390.png`. |
| Estado | Capturada; comportamiento verificado en código. |

**Observaciones de inventario:** el copy dice “PIN de Docente (OTP)” y “tu profesor de Ciencias”, aunque el usuario que recupera es un estudiante. El formulario no tiene `htmlFor`.

---

## 4. Pantallas de estudiante

### S-01 · `/dashboard` — Inicio del estudiante

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Saludo, estado adaptativo, KPIs semanales, cursos, próximos repasos y actividades. |
| Componentes | Hero con gradiente, tarjetas KPI, listas de cursos/repasos/actividades, badges, botones. |
| Datos | `learningApi.getStudentDashboard()` → FastAPI `/api/v1/learning/student/dashboard` → Supabase → constantes demo. |
| Evidencia | `student-dashboard-desktop-1440.png`, `student-dashboard-mobile-390.png`. |
| Estado | Capturada en escritorio y móvil. |

**Observaciones de inventario:** el hero cambia a “Retención Óptima” cuando no hay `primaryReview`, aunque los KPIs muestren 3/5 conceptos. Los KPIs se rotulan como “Métricas reales”. El nombre del saludo viene de la API; el de la sidebar, del contexto de rol.

### S-02 · `/courses` — Mis cursos y actividades

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Explorar cuestionarios asignados y cursos matriculados; filtrar por estado. |
| Componentes | Tabs de filtro, tarjetas de actividad, tarjetas de curso, estados vacíos, bloque “Tu aprendizaje se adapta contigo”. |
| Datos | `listStudentActivities()` y `listStudentCourses()`; los errores de cada llamada se convierten en `[]` con `console.warn`. |
| Evidencia | `student-courses-desktop-1440.png`. |
| Estado | Capturada en escritorio; móvil revisada en código. |

**Observaciones de inventario:** hay dos estados vacíos distintos en la misma página (“No hay cuestionarios en este filtro” y “No tienes cursos matriculados”). Ninguno ofrece una acción primaria; el segundo remite a hablar con el docente o administración.

### S-03 · `/learn/[id]` — Microlección

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Leer una microlección por pasos, registrar exposición y avanzar a verificación. |
| Componentes | Stepper lateral, contenido, barra de progreso, botón “Completar lección”, diagrama de fotosíntesis condicional, botón de ayuda. |
| Datos | `getMicrocontent(id)`, `recordExposure(...)`; fallback de contenido y diagrama según título/KC. |
| Evidencia | `student-learn-error-state-1440.png` (error con ID de auditoría). |
| Estado | Capturada en estado de error; contenido exitoso no capturado por falta de ID/backend. |

**Observaciones de inventario:** el modo inmersivo no muestra sidebar ni header. El error muestra `Failed to fetch` y un único botón “Regresar al panel”. El componente `PhotosynthesisDiagram` se activa si el título o KC contiene “fotosíntesis”.

### S-04 · `/quiz/[id]` — Cuestionario activo

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Iniciar intento, responder preguntas, recibir retroalimentación inmediata y avanzar. |
| Componentes | Tarjeta de prelanzamiento, barra de progreso, opciones, feedback, botones de navegación, ayuda. |
| Datos | `getStudentActivity`, `startAttempt`, `submitAnswer`; fallback local. |
| Evidencia | `student-quiz-error-state-1440.png` (actividad sin preguntas). |
| Estado | Capturada en estado de cero preguntas; flujo interactivo no ejercitado. |

**Observaciones de inventario:** el prelanzamiento muestra “PREGUNTAS 0” y un botón deshabilitado sin explicar la causa. Una vez iniciado, el encabezado muestra “Pregunta X de Y” y una barra de progreso.

### S-05 · `/quiz/[id]/results` — Resultados del cuestionario

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Mostrar puntaje, aciertos, desglose por KC, revisión de respuestas y siguientes pasos. |
| Componentes | Tarjeta de puntaje, badges por KC, lista de preguntas, `EmpatheticCallout`, botones “Volver a mis cursos” y “Ver mi progreso”. |
| Datos | Resultados por `attempt_id`; fallback con `correct_answers: correctCount || 2`, `total: items.length || 3`, `score: 80.0`. |
| Evidencia | No capturada (requiere intento válido). |
| Estado | Inspeccionada en código. |

**Observaciones de inventario:** el estado sin resultados es explícito (“Resultados no disponibles”). El fallback puede convertir 0 respuestas correctas en 2 y 0 preguntas en 3, lo que produce un resultado ficticio.

### S-06 · `/recommendations` — Recomendaciones de repaso

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Ver repasos pendientes y completados; actualizar diagnóstico. |
| Componentes | Tabs Pendientes/Todas, estado vacío, tarjetas de recomendación, botón “Actualizar diagnóstico”. |
| Datos | `getStudentRecommendations()`, `getStudentRetention(0.650)`; el umbral `0.650` está incrustado en la página. |
| Evidencia | `student-recommendations-desktop-1440.png`. |
| Estado | Capturada en escritorio. |

**Observaciones de inventario:** el estado vacío es claro y ofrece “Ver mi progreso”. No explica qué hace “Actualizar diagnóstico” ni muestra resultado/confirmación visible en la captura.

### S-07 · `/recommendations/[id]` — Detalle de recomendación

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Presentar el refuerzo recomendado, duración, pasos y CTA para comenzar. |
| Componentes | Tarjeta de dos columnas, ilustración SVG, pasos, caja empática, CTA. |
| Datos | `getStudentRecommendations(true)` y búsqueda por ID; si no hay coincidencia, usa título/KC/ilustración de Fotosíntesis. |
| Evidencia | `student-recommendation-detail-desktop-1440.png`. |
| Estado | Capturada con ID de auditoría; mostró el fallback de Fotosíntesis. |

**Observaciones de inventario:** la página presenta “Refuerzo de Fotosíntesis” y “CIENCIAS · MICROAPRENDIZAJE ADAPTATIVO” aunque no exista una recomendación real. Es el ejemplo más claro de acoplamiento semántico en la UI.

### S-08 · `/progress` — Mi progreso y retención

| Campo | Valor |
|---|---|
| Rol | Estudiante |
| Función | Mostrar precisión observada, conceptos consolidados, tiempo de estudio, evolución y detalle por KC. |
| Componentes | Cuatro KPI, gráfico de área Recharts, tabla de KC, historial de intentos, CTA a recomendaciones. |
| Datos | `getStudentProgress()` → FastAPI → Supabase → constantes demo (`12`, `45`, `3/5`, `69.4`, evolución semanal fija). |
| Evidencia | `student-progress-desktop-1440.png`, `student-progress-mobile-390.png`. |
| Estado | Capturada en escritorio y móvil. |

**Observaciones de inventario:** los KPIs dicen “Telemetría objetiva” y “Métricas reales”, pero la tabla de KC aparece vacía. El gráfico no tiene resumen textual ni tabla alternativa. En móvil, los KPI se apilan en una columna larga y el gráfico queda debajo del pliegue.

---

## 5. Pantalla compartida

### C-01 · `/system-status` — Estados del sistema

| Campo | Valor |
|---|---|
| Rol | Estudiante y docente (compartida) |
| Función | Mostrar salud de FastAPI, cold-start, Supabase/RLS, privacidad y modelo activo. |
| Componentes | Hero de estado, cuatro pilares, badges, botón “Actualizar telemetría”. |
| Datos | `fetch(API_BASE_URL/api/v1/health)`; los estados de RLS, seudonimización y modo demo están fijados en el código. |
| Evidencia | `system-status-desktop-1440.png`. |
| Estado | Capturada como docente. |

**Observaciones de inventario:** con la API caída, la latencia muestra `0 ms`, el estado dice “Sin conexión” y el pilar de Supabase afirma “RLS Enforced” y “100% activa” sin verificar Supabase. La página usa vocabulario técnico y aparece en la navegación del estudiante.

---

## 6. Pantallas de docente

### T-01 · `/teacher/dashboard` — Dashboard docente

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Resumen de sección, KPIs, distribución de dominio, estudiantes que requieren refuerzo y actividad reciente. |
| Componentes | Filtro de sección, cuatro KPI, barra de distribución, listas de estudiantes, tarjetas de actividad. |
| Datos | `getTeacherDashboard()` → FastAPI → Supabase → constantes demo (`10` estudiantes, `69.2 %`, `120` intentos). |
| Evidencia | `teacher-dashboard-desktop-1440.png`, `teacher-dashboard-mobile-390.png`. |
| Estado | Capturada en escritorio y móvil. |

**Observaciones de inventario:** el saludo “Dra. Ana García” y los estudiantes provienen del fallback. La distribución tiene leyenda textual con conteos y porcentajes, además de una barra. En móvil, los cuatro KPI se apilan en una columna y el título ocupa dos líneas.

### T-02 · `/teacher/courses` — Gestión de cursos y microcontenidos

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Ver cursos, estructura curricular y microcontenidos; crear y publicar. |
| Componentes | Tabs “Cursos”/“Microcontenidos”, buscador, botón “Nuevo microcontenido”, tarjetas de curso, modal de creación. |
| Datos | `getCourses()`, `listMicrocontents()`, mutaciones de creación/publicación. |
| Evidencia | `teacher-courses-desktop-1440.png`. |
| Estado | Capturada en escritorio; modal no abierto. |

**Observaciones de inventario:** con 0 cursos, el estado es una línea de texto centrada sin CTA ni guía. El botón “Nuevo microcontenido” sigue disponible. No se probó la creación.

### T-03 · `/teacher/activities` — Cuestionarios y actividades

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Crear cuestionarios, filtrar por curso/estado, publicar y supervisar intentos. |
| Componentes | Filtros, tabs de estado, buscador, estado vacío con CTA, modal de creación con selección de preguntas y secciones. |
| Datos | `listActivities()`, `getCourses()`, `createActivity()`. |
| Evidencia | `teacher-activities-desktop-1440.png`. |
| Estado | Capturada en escritorio; modal no abierto. |

**Observaciones de inventario:** el estado vacío sí incluye CTA (“Crear primer cuestionario”). El modal tiene etiquetas visuales sin asociación programática y no se probó el envío.

### T-04 · `/teacher/questions` — Editor y banco de preguntas

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Generar preguntas con IA, revisar borradores, aprobar, publicar y consultar historial. |
| Componentes | Cuatro KPIs, carpeta por asignatura, buscador, filtros por KC, tabs, tarjetas de borrador, modales de generación/edición/rechazo. |
| Datos | FastAPI de generación de contenido, Supabase y fallback de “Ciencias”. |
| Evidencia | `teacher-questions-desktop-1440.png`. |
| Estado | Capturada en escritorio; modales no abiertos. |

**Observaciones de inventario:** la pantalla más densa del producto. Muestra “0” en los cuatro KPIs y “1 cursos asignados”. Combina filtros, tabs, estados y acciones en una sola vista. Los modales no tienen semántica de diálogo.

### T-05 · `/teacher/students` — Nómina y rendimiento

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Buscar estudiantes seudonimizados, filtrar por sección y revisar precisión, estado y recomendaciones. |
| Componentes | Cuatro KPI, buscador, selector de sección, tabla de siete columnas. |
| Datos | `getTeacherStudents()`; Supabase/FastAPI. |
| Evidencia | `teacher-students-desktop-1440.png`. |
| Estado | Capturada en escritorio. |

**Observaciones de inventario:** muestra 0 estudiantes y una tabla vacía, mientras el dashboard y los reportes muestran 10. La tabla depende de `overflow-x-auto` y no tiene `caption` ni `scope`.

### T-06 · `/teacher/reports` — Reportes y seguimiento

| Campo | Valor |
|---|---|
| Rol | Docente |
| Función | Ver insight asistido, resumen por sección, mapa de calor de KC, rendimiento por KC y trayectoria semanal; exportar dataset. |
| Componentes | Tarjeta de insight, tarjeta de sección, tabla de mapa de calor, dos gráficos Recharts, botón de exportación. |
| Datos | `getTeacherReports()` → FastAPI → Supabase → fallback con 10 estudiantes, 120 intentos, 69.2 %, insight de Genética Molecular y trayectoria fija. |
| Evidencia | `teacher-reports-desktop-1440.png`. |
| Estado | Capturada en escritorio. |

**Observaciones de inventario:** mezcla español e inglés en títulos (“Student Mastery Heat Map”, “Class Performance Overview”). El insight afirma una caída del 12 % y 2 estudiantes en riesgo sin evidencia. El mapa de calor aparece vacío. Los gráficos no tienen tabla alternativa.

---

## 7. Matriz de procedencia de datos

| Pantalla | FastAPI | Supabase | Constantes demo | Estado observado |
|---|---|---|---|---|
| `/login` | — | Auth | Identidades demo | Formulario visible |
| `/recovery` | — | — | — | Simulación local |
| `/dashboard` | Falló | Parcial | Sí | KPIs demo con cursos vacíos |
| `/courses` | Falló | Parcial | No | Dos estados vacíos |
| `/learn/[id]` | Falló | — | Posible | Error `Failed to fetch` |
| `/quiz/[id]` | Falló | — | Posible | Actividad con 0 preguntas |
| `/quiz/[id]/results` | Falló | — | Sí | No capturada |
| `/recommendations` | Falló | Parcial | No | 0 pendientes |
| `/recommendations/[id]` | Falló | — | Sí | Fotosíntesis ficticia |
| `/progress` | Falló | Parcial | Sí | KPIs demo, tabla KC vacía |
| `/system-status` | Falló | Fijado | Parcial | “Sin conexión”, 0 ms, RLS “enforced” |
| `/teacher/dashboard` | Falló | Parcial | Sí | 10 estudiantes, 69.2 % |
| `/teacher/courses` | Falló | Parcial | Sí | 0 cursos |
| `/teacher/activities` | Falló | Parcial | No | 0 cuestionarios |
| `/teacher/questions` | Falló | Parcial | Sí | 0 preguntas, 1 curso |
| `/teacher/students` | Falló | Parcial | No | 0 estudiantes |
| `/teacher/reports` | Falló | Parcial | Sí | 10 estudiantes, insight ficticio |

**Lectura:** la combinación de fuentes produce contradicciones visibles entre pantallas. La matriz se usa en `02_UI_UX_AUDIT.md` para separar problemas de datos de problemas puramente visuales.

---

## 8. Cobertura no ejercitada

No se ejecutaron las siguientes interacciones por la restricción de solo lectura:

- Envío real de login con credenciales Supabase.
- Restablecimiento real de contraseña.
- Inicio y respuesta de un cuestionario.
- Registro de exposición de una microlección.
- Creación, edición, aprobación o publicación de preguntas.
- Generación de preguntas con IA.
- Creación o publicación de actividades y microcontenidos.
- Exportación de dataset.
- Cambio de rol desde la interfaz.
- Navegación con teclado y lector de pantalla.

Estas interacciones se evaluaron por código y por los estados visibles que producen. Se recomienda una segunda pasada con datos sembrados y backend activo antes de cerrar el Sprint 1.
