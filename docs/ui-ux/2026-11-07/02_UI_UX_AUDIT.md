# 02 — Auditoría UI/UX

**Proyecto:** Plataforma de Microaprendizaje Adaptativo
**Fecha:** 2026-11-07
**Commit:** `4150270`
**Alcance:** 18 rutas, shell global, estados de datos, flujos de estudiante y docente.
**Documentos relacionados:** `00_SCOPE_AND_METHOD.md`, `01_SCREEN_INVENTORY.md`, `03_REDESIGN_BACKLOG.md`, `04_DESIGN_DIRECTION.md`.

---

## 1. Resumen ejecutivo

La aplicación tiene una base visual coherente y un lenguaje de marca reconocible: verde azulado profundo, tarjetas blancas, tipografía compacta y una estructura de navegación consistente. El login de escritorio y los dashboards transmiten una imagen profesional y adulta, adecuada para estudiantes de 16–17 años. Sin embargo, la auditoría encontró un problema de fondo que condiciona todo lo demás: **la interfaz presenta como reales datos que son constantes de demostración o valores de reserva**, y lo hace con etiquetas que refuerzan la confianza (“Métricas reales”, “Telemetría objetiva”, “Insight de Aprendizaje Asistido”).

Ese problema no es solo estético. Un estudiante puede ver “12 actividades completadas” y “69.4 % de precisión” sin haber completado ninguna; un docente puede ver “10 estudiantes, 120 intentos, 69.2 %” y un insight sobre “Genética Molecular” mientras la página de estudiantes muestra 0. La recuperación de contraseña es una simulación que siempre declara éxito. Y el contenido de reserva está acoplado a Ciencias (Fotosíntesis, Genética Molecular), lo que contradice la restricción de una arquitectura agnóstica a la asignatura.

La segunda capa de problemas es de accesibilidad y interacción: etiquetas de formulario no asociadas, modales sin semántica de diálogo ni foco atrapado, gráficos sin alternativa textual, tablas sin `caption`/`scope`, foco visible ausente en controles personalizados, texto de 10–11 px y un gris `slate-400` con contraste de 2.56:1. La búsqueda y la campana del header son señuelos: se ven interactivas pero no hacen nada.

### Evaluación cualitativa por dimensión

> Escala 1–5, donde 1 es crítico y 5 es sólido. Es una evaluación heurística, no una métrica estadística.

| Dimensión | Nota | Justificación |
|---|---:|---|
| Confianza y honestidad de datos | **1** | Métricas y insights ficticios presentados como evidencia real. |
| Consistencia visual | **3** | Buena base de marca, pero 52 colores hex, tres radios y dos tipografías. |
| Usabilidad de flujos núcleo | **2** | Login y navegación funcionan; los estados vacíos/error bloquean o desinforman. |
| Accesibilidad WCAG 2.2 AA | **2** | Contraste, etiquetas, modales, foco, tablas y gráficos con brechas sistémicas. |
| Responsive | **3** | El layout refluye; móvil pierde densidad, trunca etiquetas y apila demasiado. |
| Claridad de contenido | **2** | Mezcla español/inglés, jerga técnica y afirmaciones no sustentadas. |
| Madurez de componentes | **2** | Primitivas mínimas; modales, tablas y formularios se reconstruyen por página. |

### Los cinco problemas de mayor impacto

1. **Datos fabricados presentados como reales** en dashboard y progreso del estudiante (`A-01`).
2. **Agregados e insights docentes ficticios** que contradicen la nómina real (`A-02`).
3. **Recuperación de contraseña simulada** que declara éxito sin cambiar nada (`A-03`).
4. **Acoplamiento semántico a Ciencias** en fallbacks y contenido de recomendaciones (`A-04`).
5. **Barreras de accesibilidad sistémicas**: contraste, etiquetas, modales, foco y gráficos (`C-01`, `D-01`, `D-02`, `E-01`, `E-02`).

### Conteo de hallazgos

| Prioridad | Cantidad |
|---|---:|
| P0 | 5 |
| P1 | 15 |
| P2 | 16 |
| P3 | 3 |
| **Total** | **39** |

| Tipo | Cantidad |
|---|---:|
| Defecto | 26 |
| Inconsistencia | 4 |
| Mejora | 9 |
| **Total** | **39** |

Además, se registran 4 hipótesis de validación en la sección 11, fuera del conteo de hallazgos confirmados.

---

## 2. Hallazgos P0 — Corregir antes de un piloto

### A-01 · P0 · Defecto — Métricas de estudiante fabricadas y rotuladas como reales

- **Pantallas:** `/dashboard`, `/progress`.
- **Descripción:** cuando no hay eventos, el cliente rellena métricas con constantes: `answers?.length || 36`, `correctAnswers || 25`, precisión `69.4`, `weekly_learning_minutes: 45`, `completed_activities_count: 12`, `consolidated_concepts_count: 3`, `reviewed_concepts_count: 5` y una evolución semanal fija. La UI las presenta como “Métricas reales de interacción y aprendizaje” y “Telemetría objetiva”. En la captura, el dashboard muestra **45 min, 12 actividades, 3/5 conceptos, 69.4 % y 5 repasados** mientras “Mis cursos” y “Próximos repasos” están vacíos; la página de progreso muestra los mismos valores y una tabla de KC vacía.
- **Evidencia:** `student-dashboard-desktop-1440.png`, `student-progress-desktop-1440.png`, `student-progress-mobile-390.png`; `src/lib/api/learning.ts:820-832`, `877-897`; `src/app/(student)/dashboard/page.tsx:198`; `src/app/(student)/progress/page.tsx:94`.
- **Archivos/componentes:** `lib/api/learning.ts` (`getStudentDashboardFromSupabase`, `getStudentProgressFromSupabase`), `dashboard/page.tsx`, `progress/page.tsx`.
- **Impacto en el usuario:** el estudiante cree que avanzó cuando no lo hizo; el docente y la familia reciben información falsa; se invalida la promesa de “telemetría objetiva”; un piloto con estos datos no es defendible.
- **Recomendación:** eliminar los `||` de relleno; devolver `null`/`0` y renderizar un estado “Aún no hay evidencia suficiente”; calcular todo desde `answer_events`; mostrar `n` y fecha de corte; si se necesita demo, usar un modo demo explícito con banner persistente y datos separados, nunca rotulados como reales.
- **Complejidad:** M (capa de datos + estados de UI + pruebas).

### A-02 · P0 · Defecto — Agregados e insights docentes ficticios que contradicen la nómina

- **Pantallas:** `/teacher/dashboard`, `/teacher/reports`, `/teacher/students`.
- **Descripción:** el fallback docente usa `profiles?.length || 10`, `attempts?.length || 120`, `answers?.length || 360`, `correct || 249`, `activeRecs || 10`, y una lista fija de estudiantes con nombres y precisiones. En reportes devuelve un insight fijo (“Repaso sugerido en Genética Molecular”, “disminuyó un 12 % tras 14 días”, “2 estudiantes en riesgo”), una sección de 10 estudiantes/120 intentos/69.2 % y una trayectoria semanal fija. La página de estudiantes, en cambio, muestra **0 estudiantes**. El docente ve dos verdades incompatibles en el mismo producto.
- **Evidencia:** `teacher-dashboard-desktop-1440.png`, `teacher-reports-desktop-1440.png`, `teacher-students-desktop-1440.png`; `src/lib/api/teacher.ts:233-259`, `267-302`, `531-547`; `src/app/teacher/reports/page.tsx:161-181`.
- **Archivos/componentes:** `lib/api/teacher.ts` (`getTeacherDashboardFromSupabase`, `getTeacherReportsFromSupabase`), `teacher/reports/page.tsx`, `teacher/dashboard/page.tsx`.
- **Impacto:** decisiones pedagógicas basadas en cohortes inexistentes; exposición de nombres seudónimos de demostración como si fueran reales; pérdida de confianza del docente; riesgo de que el “insight” se interprete como resultado científico.
- **Recomendación:** eliminar agregados y nombres de reserva; devolver estados vacíos con `n=0`; calcular el insight solo con datos reales y un mínimo de evidencia configurable; si no hay evidencia, mostrar “Insight no disponible” y explicar qué falta; unificar la fuente de conteo entre dashboard, nómina y reportes; marcar cualquier dato demo como demo.
- **Complejidad:** L (varias pantallas + contrato de datos + pruebas de consistencia).

### A-03 · P0 · Defecto — La recuperación de contraseña simula éxito sin cambiar la clave

- **Pantalla:** `/recovery`.
- **Descripción:** `handleRecoverySubmit` solo ejecuta `setTimeout(..., 700)` y luego `setIsSuccess(true)`. No llama a Supabase, no valida el PIN, no actualiza la contraseña y no registra nada. Cualquier combinación de tres campos no vacíos muestra “¡Contraseña actualizada con éxito!”.
- **Evidencia:** `recovery-desktop-1440.png`, `recovery-mobile-390.png`; `src/app/(auth)/recovery/page.tsx:26-35`, `118-170`.
- **Archivos/componentes:** `app/(auth)/recovery/page.tsx`.
- **Impacto:** el usuario cree que recuperó el acceso y queda bloqueado; falsa sensación de seguridad; contradice la promesa de autenticación institucional; un incidente de soporte se convierte en una pérdida de cuenta.
- **Recomendación:** implementar un flujo real verificable (OTP emitido por el docente/administración y validado en servidor, o `resetPasswordForEmail` si el modelo de datos lo permite) o deshabilitar la pantalla con un mensaje honesto de contacto; nunca mostrar éxito sin confirmación del backend; añadir rate limit y errores de PIN expirado.
- **Complejidad:** M–L (depende de backend y política de identidad).

### A-04 · P0 · Defecto — Contenido de reserva acoplado a Ciencias y a temas específicos

- **Pantallas:** `/recommendations/[id]`, `/learn/[id]`, `/teacher/reports`, `/recovery`, `/courses` (fallbacks), generación de contenido.
- **Descripción:** el detalle de recomendación sin datos muestra “Refuerzo de Fotosíntesis”, “Fotosíntesis: Fase luminosa y fijación de carbono”, “CIENCIAS · MICROAPRENDIZAJE ADAPTATIVO” y una ilustración de planta. El editor de microlecciones activa `PhotosynthesisDiagram` si el título/KC contiene “fotosíntesis”. El insight docente habla de “Genética Molecular” y “Herencia mendeliana”. Varios fallbacks usan `course_name: "Ciencias"` y la recuperación menciona “tu profesor de Ciencias”. La arquitectura debía ser agnóstica a la asignatura.
- **Evidencia:** `student-recommendation-detail-desktop-1440.png`, `teacher-reports-desktop-1440.png`, `recovery-desktop-1440.png`; `src/app/(student)/recommendations/[id]/page.tsx:43-46`, `119-125`; `src/app/(student)/learn/[id]/page.tsx:168-170`, `280-281`; `src/lib/api/teacher.ts:382`, `532-534`; `src/lib/api/learning.ts:797`, `892-897`, `1124`; `src/lib/api/content-generation.ts:195`.
- **Archivos/componentes:** páginas de recomendación/microlección, `components/student/photosynthesis-diagram.tsx`, clientes de API, `recovery/page.tsx`.
- **Impacto:** un estudiante de otra asignatura recibe contenido irrelevante; el producto no puede reutilizarse sin reescribir textos; se contamina el piloto; se incumple una restricción explícita del proyecto.
- **Recomendación:** sustituir todos los valores semánticos por datos de `courses`, `knowledge_components` y `microcontents`; usar un estado vacío genérico cuando falte contenido; mover diagramas específicos a un registro guiado por `content_type`/`kc` y no por texto; eliminar “Ciencias” de textos de UI y de la recuperación.
- **Complejidad:** M (búsqueda de literales + contratos + estados vacíos).

---

## 3. Hallazgos de confianza y estados (P0–P2)

### A-05 · P0 · Defecto — Estados del sistema afirma salud y seguridad no verificadas

- **Pantalla:** `/system-status`.
- **Descripción:** con FastAPI caída, el hero dice “Servicio de inferencia no disponible” y “API: sin conexión”, pero el pilar de latencia muestra **0 ms**; Supabase aparece como “RLS Enforced”, “Append-Only” y “100 % activa”; la seudonimización se declara “100 % activa / Cero exposición” sin consultar nada. Esos valores están fijados en el estado inicial y nunca se actualizan con una verificación real. “Última verificación” muestra solo hora, sin fecha ni zona horaria.
- **Evidencia:** `system-status-desktop-1440.png`; `src/app/system-status/page.tsx:18-27`, `48-56`, `193-236`.
- **Archivos/componentes:** `app/system-status/page.tsx`.
- **Impacto:** docentes y administradores reciben una falsa garantía de seguridad y operación; no se puede diagnosticar un cold-start; 0 ms se interpreta como “sin latencia” cuando significa “no medido”.
- **Recomendación:** usar estados `unknown`/`unverified`; consultar health real de Supabase/RLS si existe endpoint; mostrar `—` o “No medida” en vez de 0 ms; añadir fecha, hora y zona; separar “servicio” de “seguridad declarada”.
- **Complejidad:** S–M.

### A-06 · P1 · Defecto — Cuestionario con 0 preguntas ofrece un CTA deshabilitado sin explicación

- **Pantalla:** `/quiz/[id]`.
- **Descripción:** cuando la actividad llega sin preguntas, la tarjeta muestra “PREGUNTAS 0” y el botón “Comenzar cuestionario” queda deshabilitado con opacidad reducida. No hay mensaje de error, no se explica si es un problema de carga, una actividad vacía o una restricción del docente, y no hay acción de recuperación.
- **Evidencia:** `student-quiz-error-state-1440.png`; `src/app/(student)/quiz/[id]/page.tsx:251`, `281-292`.
- **Archivos/componentes:** `app/(student)/quiz/[id]/page.tsx`.
- **Impacto:** el estudiante no sabe si esperar, recargar o avisar; queda bloqueado en el flujo núcleo sin salida.
- **Recomendación:** separar `loading`, `error`, `actividad vacía` y `sin permiso`; en actividad vacía mostrar copy explicativo y CTA “Volver a mis cursos”/“Avisar a mi docente”; no renderizar el botón deshabilitado como única salida.
- **Complejidad:** S.

### A-07 · P1 · Defecto — Errores técnicos crudos y sin recuperación

- **Pantallas:** `/learn/[id]`, `/quiz/[id]`, banners de error docentes.
- **Descripción:** la microlección muestra `Failed to fetch` debajo de “No se pudo cargar el contenido”; el botón único es “Regresar al panel”. Otras pantallas muestran el mensaje de error de la excepción sin traducirlo ni ofrecer reintento. No hay `error.tsx` global ni boundary de página.
- **Evidencia:** `student-learn-error-state-1440.png`; `src/app/(student)/learn/[id]/page.tsx:154-164`; `src/app/teacher/students/page.tsx:81-87`.
- **Archivos/componentes:** páginas de learn/quiz, banners de error, ausencia de `app/error.tsx`.
- **Impacto:** el estudiante ve un mensaje en inglés que no comprende; no puede reintentar; el docente no distingue fallo temporal de dato inexistente.
- **Recomendación:** taxonomía de errores con copy humano, botón “Reintentar”, preservación del contexto y `error.tsx` global; registrar un `correlation_id` visible solo en modo soporte.
- **Complejidad:** S–M.

### A-08 · P1 · Inconsistencia — “Retención Óptima” contradice los propios KPIs

- **Pantalla:** `/dashboard`.
- **Descripción:** el hero muestra “Retención Óptima” y “No tienes conceptos en riesgo de olvido hoy” cuando no existe `primaryReview`. Al mismo tiempo, los KPIs muestran 3/5 conceptos consolidados (es decir, 2/5 no consolidados), 5 repasados y ningún curso. La condición se basa en la ausencia de un elemento, no en el estado de retención.
- **Evidencia:** `student-dashboard-desktop-1440.png`; `src/app/(student)/dashboard/page.tsx:88-98`, `172-190`.
- **Archivos/componentes:** `dashboard/page.tsx`.
- **Impacto:** el estudiante recibe un mensaje tranquilizador que no se sostiene con sus datos; se refuerza la falsa sensación de dominio.
- **Recomendación:** derivar el hero de un estado explícito (`pending_reviews`, `retention_status`, `evidence_count`); si no hay evidencia, decir “Aún no podemos estimar tu retención”; si hay 2/5 por consolidar, mostrarlo con lenguaje empático.
- **Complejidad:** S.

### A-09 · P1 · Defecto — Fallo de carga presentado como “no tienes cursos”

- **Pantalla:** `/courses`.
- **Descripción:** `listStudentActivities().catch(() => [])` y `listStudentCourses().catch(() => [])` convierten cualquier error de red en una lista vacía. La UI muestra “No hay cuestionarios en este filtro” y “No tienes cursos matriculados”, que son afirmaciones sobre el estado académico del estudiante, no sobre la disponibilidad del servicio.
- **Evidencia:** `student-courses-desktop-1440.png`; `src/app/(student)/courses/page.tsx:25-41`.
- **Archivos/componentes:** `app/(student)/courses/page.tsx`.
- **Impacto:** el estudiante cree que no está matriculado; no reintenta; el soporte recibe un falso reporte de datos.
- **Recomendación:** conservar el error por sección, mostrar un banner “No pudimos cargar tus cursos” con reintento y distinguirlo de un vacío legítimo; no usar `[]` como sustituto de error.
- **Complejidad:** S.

### A-10 · P2 · Defecto — Umbral de retención `0.650` incrustado en la UI

- **Pantalla:** `/recommendations`.
- **Descripción:** la página llama `getStudentRetention(0.650)`. El umbral pedagógico queda fijado en el cliente y no es visible ni configurable; el AGENTS.md exige que todo umbral sea parametrizable por configuración.
- **Evidencia:** `src/app/(student)/recommendations/page.tsx:39`; `src/lib/api/recommendations.ts` (valor por defecto `0.650`).
- **Archivos/componentes:** `recommendations/page.tsx`, `lib/api/recommendations.ts`.
- **Impacto:** no se puede ajustar la política sin desplegar frontend; el estudiante no sabe qué significa el umbral; riesgo de inconsistencia con el backend.
- **Recomendación:** mover el umbral a configuración del backend o a variable de entorno pública solo si es un parámetro de presentación; documentarlo y no mostrarlo crudo al estudiante.
- **Complejidad:** S.

---

## 4. Hallazgos P1 — Navegación y arquitectura de información

### B-01 · P1 · Defecto — La búsqueda global es un señuelo

- **Pantalla:** shell global (header).
- **Descripción:** el input tiene placeholder por rol (“Buscar en mis cursos…”, “Buscar cursos, conceptos o estudiantes…”) pero no tiene `value`, `onChange`, formulario, `onKeyDown` ni acción. Escribir no filtra ni navega.
- **Evidencia:** `student-dashboard-desktop-1440.png`, `teacher-dashboard-desktop-1440.png`; `src/components/layout/header.tsx:40-50`.
- **Archivos/componentes:** `components/layout/header.tsx`.
- **Impacto:** el usuario pierde tiempo; en un producto con muchas preguntas y estudiantes, la búsqueda es una necesidad primaria; un control visible que no funciona erosiona la confianza.
- **Recomendación:** implementar búsqueda real por rol (cursos/actividades para estudiante; cursos/KC/estudiantes para docente) con resultados, teclado y estado vacío; o retirarla del header hasta que exista.
- **Complejidad:** M.

### B-02 · P1 · Defecto — Campana de notificaciones inerte con punto permanente

- **Pantalla:** shell global (header).
- **Descripción:** el botón tiene `aria-label="Notificaciones"` y un punto teal permanente, pero no tiene `onClick`, panel ni datos. El punto sugiere notificaciones no leídas que nunca existen.
- **Evidencia:** todas las capturas con shell; `src/components/layout/header.tsx:60-67`.
- **Archivos/componentes:** `components/layout/header.tsx`.
- **Impacto:** el usuario busca una bandeja que no existe; el indicador permanente genera ansiedad y desconfianza.
- **Recomendación:** implementar bandeja con estado leído/no leído o eliminar el punto y el botón; si se deja como “próximamente”, deshabilitarlo con explicación, no simularlo.
- **Complejidad:** M (si se implementa) / S (si se retira).

### B-03 · P2 · Mejora — “Estados del sistema” ocupa un lugar principal en la navegación del estudiante

- **Pantalla:** sidebar de estudiante; `/system-status`.
- **Descripción:** el estudiante tiene “Estados del sistema” al mismo nivel que “Inicio”, “Mis cursos”, “Recomendaciones” y “Mi progreso”. La página usa jerga de arquitectura (FastAPI, cold-start, RLS, `auth.uid()`, Append-Only) y no ofrece una traducción a lenguaje de estudiante.
- **Evidencia:** `student-dashboard-desktop-1440.png`, `system-status-desktop-1440.png`; `src/components/layout/sidebar.tsx:29-33`.
- **Archivos/componentes:** `sidebar.tsx`, `system-status/page.tsx`.
- **Impacto:** ruido cognitivo; el estudiante puede interpretar “Sin conexión” o “RLS” como un problema de su cuenta; se desvía la atención del aprendizaje.
- **Recomendación:** mover la página a un área de soporte/admin o a un enlace secundario “Estado del servicio” con copy simple; conservar la vista técnica para docentes/admin; no mostrarla en la navegación principal del estudiante.
- **Complejidad:** S.

### B-04 · P3 · Inconsistencia — Terminología de rol y navegación

- **Pantalla:** sidebar, header, login.
- **Descripción:** conviven “Estudiante”, “Alumno”, “Estudiante Demo”, “Mi espacio” y “Dashboard”/“Inicio”. El chip del header dice “Estudiante”, el badge de la sidebar dice “Alumno”. En docente, “Dashboard” y “Gestión docente” se mezclan con “Panel docente”.
- **Evidencia:** `login-desktop-1440.png`, `student-dashboard-desktop-1440.png`, `teacher-dashboard-desktop-1440.png`; `src/components/layout/sidebar.tsx:117-129`; `src/components/layout/header.tsx:54-57`.
- **Archivos/componentes:** `sidebar.tsx`, `header.tsx`, páginas de dashboard.
- **Impacto:** pequeña fricción de orientación; no bloquea.
- **Recomendación:** glosario mínimo: “Estudiante”, “Docente”, “Inicio”, “Panel”; aplicarlo en toda la UI y en los textos de error.
- **Complejidad:** S.

---

## 5. Hallazgos de sistema visual, tipografía y contenido

### C-01 · P1 · Defecto — Texto demasiado pequeño y con contraste insuficiente

- **Pantallas:** progreso, nómina docente, reportes, banco de preguntas, estados vacíos.
- **Descripción:** hay **101** usos de `text-[10px]` y **104** de `text-[11px]`; **138** usos de `text-slate-400`. El gris `#94a3b8` sobre blanco tiene **2.56:1** y sobre `#f8fafc`, **2.45:1**, por debajo del 4.5:1 de WCAG AA para texto normal. Se usa en encabezados de tabla, ayudas, timestamps, estados vacíos y metadatos.
- **Evidencia:** `student-progress-desktop-1440.png`, `teacher-students-desktop-1440.png`, `teacher-reports-desktop-1440.png`; `src/app/(student)/progress/page.tsx:136-166`, `234-246`, `315-335`; `src/app/teacher/students/page.tsx:93-111`, `150`.
- **Archivos/componentes:** tokens de `globals.css`, páginas de progreso/nómina/reportes, `Card`, `Badge`.
- **Impacto:** estudiantes y docentes con baja visión o pantallas de baja calidad no pueden leer metadatos; la densidad de 10 px fatiga; se incumple 1.4.3 y 1.4.4.
- **Recomendación:** mínimo 12 px para metadatos y 14 px para cuerpo; reemplazar `slate-400` por `slate-500`/`slate-600`; definir un token `text-muted` con contraste ≥ 4.5:1; auditar contraste en CI.
- **Complejidad:** M (barrido de clases + tokens + verificación visual).

### C-02 · P1 · Inconsistencia — Mezcla de español e inglés y de registros

- **Pantallas:** `/teacher/reports`, `/teacher/questions`, `/system-status`, `/recovery`.
- **Descripción:** títulos como “Student Mastery Heat Map”, “Class Performance Overview”, “Insight de Aprendizaje Asistido”, “RLS Enforced”, “Append-Only”, “auth.uid()”, “PIN de Docente (OTP)” y “Dashboard” conviven con una interfaz mayoritariamente en español. En el editor de preguntas, los niveles de Bloom aparecen como “Recuerdo (Remember)”, “Comprensión (Understand)”, etc.
- **Evidencia:** `teacher-reports-desktop-1440.png`, `teacher-questions-desktop-1440.png`, `system-status-desktop-1440.png`, `recovery-desktop-1440.png`; `src/app/teacher/reports/page.tsx:213`, `284`; `src/app/teacher/questions/components/QuestionEditorModal.tsx:48-53`.
- **Archivos/componentes:** páginas de reportes/questions/system-status/recovery, modal de preguntas.
- **Impacto:** el docente debe traducir mentalmente; se percibe como producto inacabado; la jerga técnica no es accesible para todos.
- **Recomendación:** español consistente; si se conserva el término inglés, añadir entre paréntesis una vez; traducir “Heat Map” a “Mapa de dominio”, “Class Performance Overview” a “Rendimiento por grupo”; reservar RLS/Append-Only para una vista técnica.
- **Complejidad:** S–M.

### C-03 · P2 · Defecto — Deriva de tokens: 310 colores hex y tres radios

- **Pantallas:** todas.
- **Descripción:** hay **310** literales hex en `src` con **52** valores únicos; conviven `#0A635F`, `#0f766e`, `#0d9488`, `#0B2D34`, `#123E45`, `#69D7C9`, `#39BEAD`, `#65D7C9`, etc. Los radios se reparten entre **147** `rounded-xl`, **114** `rounded-2xl` y **44** `rounded-3xl`, sin una regla visible por tipo de componente.
- **Evidencia:** inspección de código (`grep` sobre `apps/web/src`); `teacher-dashboard-desktop-1440.png`, `student-dashboard-desktop-1440.png`.
- **Archivos/componentes:** `globals.css`, `tailwind.config.ts`, páginas y primitivas.
- **Impacto:** cambios de marca costosos; inconsistencias difíciles de detectar; riesgo de contraste y de jerarquía.
- **Recomendación:** tokens semánticos en `globals.css`/Tailwind (`--primary`, `--surface`, `--text-muted`, `--border`, `--radius-card`, `--radius-control`); prohibir hex en páginas; mapear radios a control/card/hero.
- **Complejidad:** M (refactor mecánico + revisión visual).

### C-04 · P2 · Inconsistencia — La tipografía real no es Inter

- **Pantallas:** todas.
- **Descripción:** `docs/ux/design-specs.md` declara Inter, pero `globals.css` usa `system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, ...`. El resultado varía por sistema operativo y no coincide con la especificación.
- **Evidencia:** `src/app/globals.css:54-57`; `docs/ux/design-specs.md:10`; capturas en Linux con fuente por defecto.
- **Archivos/componentes:** `globals.css`, `layout.tsx`, `tailwind.config.ts`.
- **Impacto:** jerarquía y métricas impredecibles; la marca se ve distinta en cada equipo; los tamaños pequeños se leen peor.
- **Recomendación:** adoptar Inter con `next/font` (autohospedada o Google Fonts) y fallback explícito; definir escala y pesos; o actualizar la especificación si se decide system-ui.
- **Complejidad:** S.

### C-05 · P2 · Mejora — Estados vacíos inconsistentes y, a veces, sin salida

- **Pantallas:** `/teacher/courses`, `/courses`, `/recommendations`, `/teacher/students`, `/teacher/questions`.
- **Descripción:** algunos vacíos tienen icono, título, explicación y CTA (“Crear primer cuestionario”); otros son una línea de texto centrada (“No se encontraron cursos asignados”) o una tabla vacía; otros remiten a contactar a un tercero. No comparten componente ni estructura.
- **Evidencia:** `teacher-courses-desktop-1440.png`, `student-courses-desktop-1440.png`, `teacher-students-desktop-1440.png`, `teacher-questions-desktop-1440.png`.
- **Archivos/componentes:** páginas listadas; no existe `EmptyState` compartido.
- **Impacto:** el usuario no sabe si el vacío es normal, si debe actuar o si algo falló; se pierden oportunidades de onboarding.
- **Recomendación:** crear `EmptyState` con icono, título, explicación, acción primaria, acción secundaria y nota de origen de datos; diferenciar “sin datos”, “sin resultados de filtro”, “error” y “sin permiso”.
- **Complejidad:** S–M.

### C-06 · P2 · Mejora — El login de escritorio está dominado por la ilustración

- **Pantalla:** `/login`.
- **Descripción:** la mitad izquierda es una composición orbital animada con un mensaje grande; la mitad derecha concentra el formulario. La ilustración es atractiva pero compite con la tarea; el CTA deshabilitado se ve pálido y no explica por qué. En móvil, la ilustración se convierte en pestaña, lo que funciona mejor.
- **Evidencia:** `login-desktop-1440.png`, `login-mobile-390.png`.
- **Archivos/componentes:** `app/(auth)/login/page.tsx`, `components/auth/solar-system-orbit.tsx`.
- **Impacto:** en escritorio, el ojo va primero a la decoración; el formulario queda en segundo plano; el estado deshabilitado no guía.
- **Recomendación:** reducir la ilustración a un panel de marca más contenido; dar al formulario un ancho y una jerarquía más claros; explicar el estado deshabilitado (“Completa correo y contraseña”); conservar la animación solo si respeta `prefers-reduced-motion`.
- **Complejidad:** S.

### C-07 · P3 · Defecto — Errores de concordancia y copy

- **Pantallas:** `/teacher/questions`, `/teacher/dashboard`, `/progress`.
- **Descripción:** “1 cursos asignados”, “1 secciones asignadas”, “En 36 respuestas analizadas” cuando el número es un fallback. También “5 repasados oportunamente” sin contexto.
- **Evidencia:** `teacher-questions-desktop-1440.png`, `teacher-dashboard-mobile-390.png`, `student-progress-desktop-1440.png`; `src/app/teacher/questions/page.tsx:342`; `src/app/teacher/dashboard/page.tsx:126`.
- **Archivos/componentes:** páginas listadas.
- **Impacto:** percepción de descuido; en un producto educativo, el copy es parte de la credibilidad.
- **Recomendación:** pluralización con `Intl.PluralRules` o utilidad `pluralize`; revisar textos con datos variables; evitar frases que afirmen algo sin datos.
- **Complejidad:** S.

---

## 6. Hallazgos de formularios y componentes

### D-01 · P1 · Defecto — Etiquetas visuales sin asociación programática

- **Pantallas:** `/recovery`, `/teacher/activities`, `/teacher/courses`, `/teacher/questions`, modales.
- **Descripción:** en `src` hay **29** etiquetas `<label>` y solo **2** `htmlFor`; el login es la excepción. En recuperación, los tres campos tienen etiqueta visual sin `htmlFor`/`id`. En el modal de actividad y en el de microcontenido ocurre lo mismo. Un lector de pantalla anuncia “cuadro de edición” sin nombre.
- **Evidencia:** `recovery-desktop-1440.png`, `teacher-activities-desktop-1440.png`; `src/app/(auth)/recovery/page.tsx:119-160`; `src/app/teacher/activities/page.tsx:515-584`; `src/app/teacher/courses/page.tsx:430-469`.
- **Archivos/componentes:** páginas de formularios y modales.
- **Impacto:** usuarios de lector de pantalla no pueden completar formularios; también afecta a dictado por voz y autofill; incumple 1.3.1 y 3.3.2.
- **Recomendación:** usar `id`/`htmlFor` o envolver el input en el label; añadir `aria-describedby` para ayudas y errores; crear un `Field` compartido que lo garantice.
- **Complejidad:** M (barrido de formularios).

### D-02 · P1 · Defecto — Modales sin semántica de diálogo, foco atrapado ni Escape

- **Pantallas:** editor de preguntas, generación con IA, rechazo, creación de actividad, creación de microcontenido, drawer móvil.
- **Descripción:** los overlays usan `fixed inset-0` y un `div`, sin `role="dialog"`, `aria-modal="true"`, `aria-labelledby`, trampa de foco, foco inicial ni cierre con Escape. El botón de cerrar usa `title` y un icono, sin `aria-label`. Al abrir, el foco permanece detrás del overlay.
- **Evidencia:** `teacher-questions-desktop-1440.png`; `src/app/teacher/questions/components/QuestionEditorModal.tsx:277`; `GenerateQuestionsModal.tsx:127`; `RejectReasonDialog.tsx:47`; `teacher/activities/page.tsx`; `teacher/courses/page.tsx`; `components/layout/sidebar.tsx`.
- **Archivos/componentes:** todos los overlays listados.
- **Impacto:** teclado y lector de pantalla quedan atrapados o salen del modal; el usuario puede editar la página de fondo; incumple 2.1.1, 2.4.3 y 4.1.2.
- **Recomendación:** crear un `Modal` compartido con portal, `role="dialog"`, `aria-modal`, `aria-labelledby`, foco inicial, trampa de foco, Escape, retorno de foco y bloqueo de scroll; en móvil, usar `bottom sheet` accesible.
- **Complejidad:** M.

### D-03 · P2 · Defecto — Objetivos táctiles por debajo del estándar interno de 44 px

- **Pantallas:** header, tablas, editor de preguntas, acciones secundarias.
- **Descripción:** `Button` define `default: h-10` (40 px), `sm: h-8` (32 px), `icon: h-9` (36 px). El estándar interno de `ux-usability` pide 44 × 44 px. Muchos botones de tabla y tabs usan `sm` o `text-[10px]` con padding reducido.
- **Evidencia:** `src/components/ui/button.tsx:20-26`; `teacher-students-desktop-1440.png`, `student-progress-desktop-1440.png`.
- **Archivos/componentes:** `components/ui/button.tsx`, tablas y barras de acciones.
- **Impacto:** usuarios con motricidad fina o en móvil fallan al tocar; incumple el estándar del proyecto (aunque supera el mínimo WCAG 2.2 de 24 px en la mayoría de casos).
- **Recomendación:** `min-h-11` (44 px) para acciones primarias y de tabla; `icon` de 44 px; si se necesita densidad, aumentar el área de hit con padding invisible; documentar excepciones.
- **Complejidad:** S–M.

### D-04 · P2 · Defecto — Campos de autenticación sin `autocomplete`

- **Pantalla:** `/login`, `/recovery`.
- **Descripción:** los inputs de identificador, contraseña y nueva contraseña no tienen `autoComplete` (`username`, `current-password`, `new-password`), ni `inputMode`/`autoCapitalize` adecuados. Esto dificulta gestores de contraseñas y autofill.
- **Evidencia:** `login-desktop-1440.png`, `recovery-desktop-1440.png`; `src/app/(auth)/login/page.tsx:531-575`; `src/app/(auth)/recovery/page.tsx:122-160`.
- **Archivos/componentes:** páginas de autenticación.
- **Impacto:** más errores de tecleo y fricción en móvil; relevante para 3.3.8 (autenticación accesible).
- **Recomendación:** añadir `autoComplete` correcto, `inputMode="email"` cuando corresponda, `spellCheck={false}` y `autoCapitalize="none"` en identificadores.
- **Complejidad:** S.

### D-05 · P2 · Defecto — Notificaciones transitorias sin `aria-live`

- **Pantallas:** `/teacher/activities`, `/teacher/questions`, modales.
- **Descripción:** los toasts de éxito/error se renderizan como `div` condicionales sin `role="status"`, `role="alert"` ni `aria-live`. Un usuario de lector de pantalla no se entera de que guardó, publicó o falló.
- **Evidencia:** `src/app/teacher/activities/page.tsx:139-152`; `src/app/teacher/questions/page.tsx:269-282`; `QuestionEditorModal.tsx:331-343`.
- **Archivos/componentes:** páginas y modales docentes.
- **Impacto:** el usuario repite acciones o cree que no se guardó; incumple 4.1.3.
- **Recomendación:** componente `Toast` con `role="status"` para éxito y `role="alert"` para error, `aria-live` y cierre accesible; no depender solo del color.
- **Complejidad:** S.

### D-06 · P2 · Mejora — El editor de preguntas es demasiado denso para su importancia

- **Pantalla:** `/teacher/questions` y `QuestionEditorModal`.
- **Descripción:** el modal usa un layout de dos columnas a 94vh con texto de 10–11 px, múltiples selectores, pestañas y validación. En pantallas pequeñas el split se apila y el contenido compite por el scroll. Es la superficie más compleja del producto y la que más texto pequeño concentra.
- **Evidencia:** `teacher-questions-desktop-1440.png`; `QuestionEditorModal.tsx:277-380`.
- **Archivos/componentes:** `teacher/questions/page.tsx`, `components/QuestionEditorModal.tsx`.
- **Impacto:** fatiga cognitiva y errores de edición; el docente puede publicar un reactivo con una opción mal marcada.
- **Recomendación:** simplificar el modal en pasos (enunciado → opciones → metadatos → vista previa), aumentar cuerpo a 14 px, mostrar un resumen persistente y reservar el split para escritorio ancho.
- **Complejidad:** M.

---

## 7. Hallazgos de accesibilidad estructural

### E-01 · P1 · Defecto — Foco visible solo en la primitiva `Button`

- **Pantallas:** todas.
- **Descripción:** el único `focus-visible` del código está en `button.tsx`. Hay **50** `<button>` nativos y numerosos `<Link>` con estilos `hover` pero sin `focus-visible`. Los tabs, tarjetas clicables, cierres de modal y acciones de tabla no muestran dónde está el foco.
- **Evidencia:** inspección de código (`grep`); `src/components/ui/button.tsx:6`; `sidebar.tsx:150-166`; `header.tsx:22-27`, `60-67`.
- **Archivos/componentes:** `globals.css`, `button.tsx`, `sidebar.tsx`, `header.tsx`, páginas.
- **Impacto:** navegación por teclado imposible de seguir; incumple 2.4.7.
- **Recomendación:** estilo global `:focus-visible` con anillo de 2 px y offset; aplicarlo a `a`, `button`, `input`, `select`, `textarea`, `[tabindex]`; probar con Tab en cada pantalla.
- **Complejidad:** S.

### E-02 · P1 · Defecto — Gráficos sin nombre accesible ni alternativa textual

- **Pantallas:** `/progress`, `/teacher/reports`.
- **Descripción:** los `ResponsiveContainer` de Recharts no tienen `aria-label`, `role="img"`, descripción ni tabla de datos alternativa. El gráfico de área de precisión y los gráficos de barras/línea solo existen como SVG. La información equivalente no está disponible para lectores de pantalla.
- **Evidencia:** `student-progress-desktop-1440.png`, `teacher-reports-desktop-1440.png`; `src/app/(student)/progress/page.tsx:191-215`; `src/app/teacher/reports/page.tsx:291-315`.
- **Archivos/componentes:** páginas de progreso/reportes.
- **Impacto:** un estudiante ciego no puede acceder a su evolución; un docente con baja visión no puede interpretar la tendencia; incumple 1.1.1 y 1.3.1.
- **Recomendación:** envolver cada gráfico con `figure`/`figcaption`, `aria-label` con resumen, y un botón “Ver datos” que muestre una tabla accesible; mantener la tabla siempre en el DOM si es posible.
- **Complejidad:** M.

### E-03 · P1 · Defecto — Tablas sin `caption`, `scope` ni adaptación móvil

- **Pantallas:** `/progress`, `/teacher/students`, `/teacher/reports`.
- **Descripción:** las tablas usan `overflow-x-auto` y `text-xs`, sin `<caption>`, `scope="col"` ni `scope="row"`. En móvil, la tabla de progreso y la nómina dependen de scroll horizontal; la columna de estudiante puede quedar fuera de vista.
- **Evidencia:** `student-progress-mobile-390.png`, `teacher-students-desktop-1440.png`, `teacher-reports-desktop-1440.png`; `progress/page.tsx:231-299`; `teacher/students/page.tsx:147-254`; `teacher/reports/page.tsx:221-269`.
- **Archivos/componentes:** páginas listadas.
- **Impacto:** lectores de pantalla no asocian encabezados y celdas; usuarios móviles pierden columnas; incumple 1.3.1.
- **Recomendación:** añadir `caption` visible o `sr-only`, `scope`, y una vista de tarjetas para móvil; indicar visualmente el scroll horizontal y fijar la primera columna.
- **Complejidad:** M.

### E-04 · P2 · Defecto — Jerarquía de encabezados inconsistente

- **Pantallas:** login, resultados, tarjetas.
- **Descripción:** el login usa `h1` para la marca “Nexo” y `h2` para el título de la página; `CardTitle` siempre renderiza `h3`, aunque la tarjeta cuelgue directamente de un `h1`; la página de resultados usa `h2` para “Resultados no disponibles” sin `h1` previo. La jerarquía visual y la semántica no siempre coinciden.
- **Evidencia:** `login-desktop-1440.png`; `src/components/ui/card.tsx:31-44`; `src/app/(student)/quiz/[id]/results/page.tsx:89`.
- **Archivos/componentes:** `card.tsx`, login, resultados.
- **Impacto:** navegación por encabezados confusa para lectores de pantalla; incumple 1.3.1 y 2.4.6.
- **Recomendación:** un `h1` por página; `h2` para secciones; `CardTitle` configurable (`as` prop) o `h2` por defecto; revisar mapas de encabezados.
- **Complejidad:** S–M.

### E-05 · P2 · Defecto — No hay enlace “Saltar al contenido” ni landmarks consistentes

- **Pantallas:** todas las rutas con shell.
- **Descripción:** no existe skip link; el contenido principal es un `<main>` dentro del shell, pero la navegación lateral y el header preceden al contenido en el orden de tabulación. No se usan `aria-current` en los enlaces activos del sidebar.
- **Evidencia:** `src/components/layout/app-shell.tsx`; `sidebar.tsx:150-166`; inspección de código.
- **Archivos/componentes:** `app-shell.tsx`, `sidebar.tsx`.
- **Impacto:** usuarios de teclado deben tabular por toda la navegación en cada página; no saben qué enlace está activo.
- **Recomendación:** skip link visible al foco, `main id="contenido"`, `aria-current="page"` en el enlace activo y landmarks `nav`/`main`.
- **Complejidad:** S.

### E-06 · P2 · Defecto — Animaciones infinitas sin `prefers-reduced-motion`

- **Pantalla:** `/login` y shell.
- **Descripción:** el sistema orbital del login usa animaciones infinitas (`orbit-clockwise` 22–34 s, `pulse-glow`) sin `@media (prefers-reduced-motion: reduce)`. Los `animate-pulse` de carga también se ejecutan sin control.
- **Evidencia:** `src/app/globals.css:88-150`; `components/auth/solar-system-orbit.tsx:46-141`.
- **Archivos/componentes:** `globals.css`, `solar-system-orbit.tsx`.
- **Impacto:** usuarios con sensibilidad vestibular o atención reducida reciben movimiento continuo; consume CPU en equipos modestos.
- **Recomendación:** desactivar o reducir animaciones con `prefers-reduced-motion`; limitar la animación al primer render o a una interacción; usar transiciones de 150–200 ms.
- **Complejidad:** S.

---

## 8. Hallazgos responsive y de flujo

### F-01 · P1 · Defecto — El login móvil trunca roles y superpone ayuda con un enlace

- **Pantalla:** `/login` a 390 px.
- **Descripción:** las tarjetas de rol muestran “Estudiant…” y “Aprender…” / “Gestiona…” por `truncate`; el botón flotante “?” se superpone a “Ver presentación”, que queda parcialmente debajo. El CTA deshabilitado es pálido y no explica la causa.
- **Evidencia:** `login-mobile-390.png`; `src/app/(auth)/login/page.tsx:384-465`, `654-661`.
- **Archivos/componentes:** `login/page.tsx`.
- **Impacto:** el estudiante no distingue bien los portales en el primer contacto; el enlace de presentación es difícil de tocar; la primera impresión es de descuido.
- **Recomendación:** permitir dos líneas o acortar el copy (“Estudiante / Aprende y repasa”); mover el botón de ayuda a un lugar que no tape enlaces; separar el CTA del borde inferior; mostrar un texto de ayuda cuando esté deshabilitado.
- **Complejidad:** S.

### F-02 · P2 · Mejora — Dashboard docente móvil: cuatro KPI en una columna muy larga

- **Pantalla:** `/teacher/dashboard` a 390 px.
- **Descripción:** los KPIs se apilan uno por uno; el título “Bienvenida, Dra. Ana García” ocupa dos líneas y el filtro de sección queda entre el título y las tarjetas. La información esencial (estudiantes, precisión, repasos) exige un scroll largo antes de llegar a las listas.
- **Evidencia:** `teacher-dashboard-mobile-390.png`.
- **Impacto:** el docente no puede escanear el estado de la sección de un vistazo; se pierde la ventaja del dashboard.
- **Recomendación:** grid 2×2 de KPIs en móvil, título más corto, filtro colapsable y un resumen fijo de 2 métricas; mantener la densidad solo en escritorio.
- **Complejidad:** S.

### F-03 · P2 · Mejora — Progreso móvil: KPI largos y gráfico/tabla fuera del pliegue

- **Pantalla:** `/progress` a 390 px.
- **Descripción:** los cuatro KPI ocupan casi dos pantallas; el gráfico y la tabla quedan muy abajo. La tabla requiere scroll horizontal y el texto de 10 px se vuelve ilegible.
- **Evidencia:** `student-progress-mobile-390.png`.
- **Impacto:** el estudiante no ve su evolución sin desplazarse mucho; la tabla es difícil de usar.
- **Recomendación:** resumen compacto 2×2, gráfico antes de los KPIs secundarios, tabla convertida en tarjetas o acordeón por KC.
- **Complejidad:** M.

### F-04 · P1 · Mejora — Cold start y estados vacíos sin onboarding

- **Pantallas:** `/courses`, `/dashboard`, `/teacher/courses`, `/teacher/questions`.
- **Descripción:** un estudiante nuevo ve “Sin cursos asignados aún” sin acción más allá de esperar; un docente nuevo ve “No se encontraron cursos asignados” sin guía; el banco de preguntas muestra 0 y un CTA de generación, pero no explica el flujo mínimo (crear curso → generar pregunta → aprobar → publicar). El sistema está diseñado para microlearning de 3–5 min, pero la primera sesión puede durar más en configuración.
- **Evidencia:** `student-courses-desktop-1440.png`, `teacher-courses-desktop-1440.png`, `teacher-questions-desktop-1440.png`.
- **Archivos/componentes:** páginas listadas.
- **Impacto:** abandono en la primera sesión; el docente no sabe por dónde empezar; el piloto depende de soporte manual.
- **Recomendación:** checklist de primeros pasos contextual por rol; CTA “Crear mi primer curso” para docente; para estudiante, “Explorar actividades de práctica” o “Avisar a mi docente”; estados vacíos con explicación del siguiente paso.
- **Complejidad:** M.

### F-05 · P2 · Mejora — Sobrecarga cognitiva en el banco de preguntas

- **Pantalla:** `/teacher/questions`.
- **Descripción:** una sola vista combina cuatro KPIs, carpeta de asignatura, buscador, filtro de KC, tres tabs, cinco filtros de estado, lista de borradores y acciones. El docente debe mantener el contexto de todo mientras edita.
- **Evidencia:** `teacher-questions-desktop-1440.png`.
- **Impacto:** errores de filtro, acciones sobre el borrador equivocado, fatiga.
- **Recomendación:** separar “Banco” y “Cola de revisión”; mostrar filtros activos como chips; reducir tabs; un panel lateral de detalle en lugar de múltiples modales.
- **Complejidad:** L.

### F-06 · P3 · Mejora — Header móvil comprimido

- **Pantalla:** shell a 390 px.
- **Descripción:** el header combina hamburguesa, marca, búsqueda truncada, chip de rol oculto y campana. La búsqueda queda en ~180 px y el placeholder se corta.
- **Evidencia:** `student-progress-mobile-390.png`, `teacher-dashboard-mobile-390.png`.
- **Impacto:** la búsqueda es aún menos útil; el header se siente apretado.
- **Recomendación:** colapsar la búsqueda en un icono que abra un campo a pantalla completa; ocultar la marca duplicada; priorizar acciones.
- **Complejidad:** S.

---

## 9. Evaluación de flujos extremo a extremo

### 9.1 Flujo del estudiante

| Paso | Pantalla | Qué ocurre | Fricción / riesgo | Severidad |
|---|---|---|---|---|
| 1 | `/login` | Elige portal, ingresa credenciales o usa demo. | En móvil, roles truncados y ayuda superpuesta; CTA deshabilitado sin explicación. | P1 (`F-01`) |
| 2 | `/dashboard` | Ve saludo, hero adaptativo y KPIs. | Métricas ficticias; “Retención Óptima” contradice 3/5; sin cursos. | P0 (`A-01`), P1 (`A-08`) |
| 3 | `/courses` | Busca actividades y cursos. | Dos vacíos sin acción; fallo de red se disfraza de “no matriculado”. | P1 (`A-09`, `F-04`) |
| 4 | `/learn/[id]` | Lee microlección. | Si falla, `Failed to fetch` y solo “Regresar”; contenido de reserva acoplado a Fotosíntesis. | P1 (`A-07`), P0 (`A-04`) |
| 5 | `/quiz/[id]` | Inicia intento y responde. | Con 0 preguntas, CTA deshabilitado sin causa; sin salida clara. | P1 (`A-06`) |
| 6 | `/quiz/[id]/results` | Ve puntaje y desglose. | El fallback puede fabricar 2/3 aciertos; no capturado con datos reales. | P0 (`A-01` relacionado) |
| 7 | `/recommendations` | Ve repasos pendientes. | Estado vacío correcto; “Actualizar diagnóstico” no explica ni confirma. | P2 |
| 8 | `/recommendations/[id]` | Abre un refuerzo. | Sin datos, muestra Fotosíntesis ficticia. | P0 (`A-04`) |
| 9 | `/progress` | Revisa evolución y KC. | KPIs ficticios, tabla vacía, gráfico sin alternativa, móvil muy largo. | P0 (`A-01`), P1 (`E-02`, `E-03`) |

**Conclusión del flujo estudiantil:** el camino feliz existe, pero no es verificable. El estudiante puede completar pasos, pero la interfaz le devuelve datos que no corresponden a su actividad. El primer contacto en móvil tiene fricción y los estados de error no ofrecen recuperación.

### 9.2 Flujo del docente

| Paso | Pantalla | Qué ocurre | Fricción / riesgo | Severidad |
|---|---|---|---|---|
| 1 | `/login` | Elige portal docente. | Mismo login; demo visible solo en desarrollo. | P2 |
| 2 | `/teacher/dashboard` | Ve 10 estudiantes, 69.2 %, distribución. | Agregados ficticios; móvil apila cuatro KPI. | P0 (`A-02`), P2 (`F-02`) |
| 3 | `/teacher/courses` | Revisa cursos y microcontenidos. | 0 cursos y estado vacío sin CTA contextual. | P1 (`F-04`) |
| 4 | `/teacher/activities` | Crea cuestionario. | Estado vacío con CTA; modal denso y sin semántica. | P1 (`D-02`), P2 (`D-06`) |
| 5 | `/teacher/questions` | Genera, revisa y aprueba preguntas. | 0 preguntas, “1 cursos”, múltiples filtros; modales inaccesibles. | P1 (`D-02`), P2 (`F-05`) |
| 6 | `/teacher/students` | Consulta nómina. | 0 estudiantes, contradice dashboard/reportes. | P0 (`A-02`) |
| 7 | `/teacher/reports` | Ve insight, mapa de calor y trayectoria. | Insight ficticio, inglés mezclado, mapa vacío; exportación sin provenance. | P0 (`A-02`), P1 (`C-02`) |
| 8 | `/system-status` | Verifica API/Supabase. | 0 ms con API caída; RLS “enforced” sin verificación. | P1 (`A-05`) |

**Conclusión del flujo docente:** el docente no puede confiar en el panel para tomar decisiones. La nómina, el dashboard y los reportes no comparten una única fuente de verdad, y el insight principal es una constante. La creación de contenido existe, pero la superficie es densa y los modales no son accesibles.

---

## 10. Checklist WCAG 2.2 AA

| Criterio | Resultado | Evidencia / nota |
|---|---|---|
| 1.1.1 Contenido no textual | **Parcial** | Gráficos sin alternativa; iconos decorativos sin `aria-hidden` explícito. |
| 1.3.1 Información y relaciones | **Falla** | Etiquetas sin asociación; tablas sin `scope`/`caption`; jerarquía de encabezados. |
| 1.4.3 Contraste (mínimo) | **Falla** | `slate-400` 2.56:1; textos de 10 px. |
| 1.4.4 Redimensionar texto | **Parcial** | Tamaños fijos en px; 10–11 px no escalan con preferencias. |
| 1.4.10 Reflow | **Parcial** | Tablas con scroll horizontal; dashboard móvil muy largo. |
| 1.4.11 Contraste no textual | **Parcial** | Bordes muy claros; estados deshabilitados dependen de opacidad. |
| 2.1.1 Teclado | **Parcial** | Controles son botones/enlaces, pero modales no atrapan foco. |
| 2.1.2 Sin trampas de teclado | **Parcial** | No se detectó trampa, pero el foco puede escapar del modal. |
| 2.2.2 Pausar, detener, ocultar | **Falla** | Animación orbital infinita sin control. |
| 2.3.1 Tres destellos | **Pasa** | No se observaron destellos. |
| 2.4.3 Orden del foco | **Parcial** | Modales y drawer sin gestión de foco. |
| 2.4.6 Encabezados y etiquetas | **Parcial** | `h1` de marca en login; `CardTitle` fijo en `h3`. |
| 2.4.7 Foco visible | **Falla** | Solo la primitiva `Button` tiene anillo. |
| 2.4.11 Foco no oscurecido | **Parcial** | Header sticky; no se probó con teclado. |
| 2.5.7 Movimientos de arrastre | **Pasa** | No se identificaron acciones de arrastre. |
| 2.5.8 Tamaño mínimo del objetivo | **Pasa** | La mayoría ≥ 24 px; el estándar interno de 44 px falla. |
| 3.2.3 Navegación consistente | **Parcial** | Shell consistente; terminología de rol inconsistente. |
| 3.2.6 Ayuda consistente | **Parcial** | Botón de ayuda solo en algunas pantallas. |
| 3.3.1 Identificación de errores | **Parcial** | Errores crudos o ausentes; sin asociación a campos. |
| 3.3.2 Etiquetas o instrucciones | **Falla** | 29 labels, 2 `htmlFor`. |
| 3.3.8 Autenticación accesible | **Parcial** | Sin `autocomplete`; recuperación simulada. |
| 4.1.2 Nombre, rol, valor | **Parcial** | Modales sin `role="dialog"`; tabs sin semántica. |
| 4.1.3 Mensajes de estado | **Falla** | Toasts sin `aria-live`. |

**Conclusión:** la aplicación no cumple WCAG 2.2 AA. Las brechas más graves son de semántica (etiquetas, tablas, modales) y de percepción (contraste, foco visible, movimiento). La buena noticia es que muchas se resuelven con componentes compartidos y tokens, no con rediseños completos.

---

## 11. Hipótesis a validar

| ID | Hipótesis | Cómo validarla |
|---|---|---|
| H-01 | Los estudiantes de 16–17 años interpretan “Retención Óptima” como una garantía de que no olvidarán el contenido. | Prueba de comprensión de 5–8 estudiantes con el hero actual y una versión con “Sin datos suficientes”. |
| H-02 | Los docentes confían más en el panel cuando ven el tamaño de muestra y la fecha de corte. | Entrevistas y prueba A/B con 5 docentes. |
| H-03 | La densidad del banco de preguntas aumenta el tiempo de revisión y los errores de filtro. | Medir tiempo de tarea y errores en 5 docentes con el diseño actual y un prototipo simplificado. |
| H-04 | El texto de 10 px es legible en el aula pero no en móvil ni en pantallas proyectadas. | Prueba de lectura en dispositivo real con docentes y estudiantes. |

No se presentan como hallazgos confirmados; requieren evidencia de usuarios.

---

## 12. Fortalezas que deben conservarse

- **Identidad visual:** el verde azulado profundo (`#0B2D34` / `#0A635F`) y el acento menta (`#69D7C9`) transmiten calma y rigor; no son infantiles.
- **Diferenciación de rol:** el sidebar y el header cambian de color/contenido entre estudiante y docente; la estructura es predecible.
- **Modo inmersivo:** `/learn` y `/quiz` eliminan la navegación para reducir distracciones; es la decisión correcta para microlearning.
- **Microcopy empático:** “refuerzo sugerido”, “por consolidar” y “aprende a tu ritmo” evitan etiquetas alarmistas.
- **Estados vacíos en recomendaciones y actividades:** cuando están bien hechos, explican el siguiente paso y ofrecen CTA.
- **Uso de Recharts y Lucide:** base técnica suficiente para una capa de visualización más accesible.
- **Login móvil con tabs:** la adaptación de la presentación a pestaña es una buena decisión responsive.

---

## 13. Limitaciones del diagnóstico

- El backend FastAPI no estaba disponible; los estados observados son una mezcla de Supabase local y constantes demo.
- Las cookies sintéticas no representan una sesión real; la identidad de la sidebar es la de la cookie.
- No se probó con lector de pantalla real ni con teclado físico.
- No se validaron flujos de escritura (crear, publicar, aprobar) ni la exportación.
- Las notas por dimensión son heurísticas y deben contrastarse con pruebas de usuario.
- No se evaluó la exactitud de los modelos ni la calidad psicométrica de las preguntas.

---

## 14. Cierre

La aplicación no necesita un rediseño total. Necesita, en este orden:

1. **Decir la verdad sobre los datos.** Sin esto, cualquier mejora visual es cosmética.
2. **Reparar la recuperación de contraseña.** Sin esto, el acceso no es confiable.
3. **Desacoplar el contenido de Ciencias.** Sin esto, el producto no es reutilizable.
4. **Construir primitivas accesibles** (formulario, modal, tabla, gráfico, foco, botón).
5. **Ordenar los estados vacíos y de error** para que el estudiante y el docente sepan qué hacer.

El detalle accionable, con criterios de aceptación y secuencia, está en `03_REDESIGN_BACKLOG.md`. La propuesta visual y de sistema de diseño está en `04_DESIGN_DIRECTION.md`.
