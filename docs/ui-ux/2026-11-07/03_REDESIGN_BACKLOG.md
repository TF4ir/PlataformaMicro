# 03 — Backlog de rediseño

**Proyecto:** Plataforma de Microaprendizaje Adaptativo
**Fecha:** 2026-11-07
**Base:** hallazgos de `02_UI_UX_AUDIT.md` (39 hallazgos: 5 P0, 15 P1, 16 P2, 3 P3)
**Objetivo:** convertir el diagnóstico en trabajo ejecutable, priorizado y verificable, sin ampliar el alcance funcional del producto.

---

## 1. Cómo usar este backlog

- Cada ítem tiene un identificador `BL-xx`, prioridad, hallazgos cubiertos, objetivo, problema, pantallas, archivos, beneficio, complejidad, dependencias y criterios de aceptación.
- Los identificadores `A-xx`, `B-xx`, `C-xx`, `D-xx`, `E-xx` y `F-xx` (sin la `L`) son hallazgos de `02_UI_UX_AUDIT.md`; los `BL-xx` son ítems de este backlog.
- Los ítems P0 son **bloqueantes**: no se debe iniciar un piloto ni una demostración con usuarios mientras estén abiertos.
- Los ítems P1 son **Sprint 1**. Los P2 se distribuyen entre Sprint 1 y 2. Los P3 son pulido.
- Los criterios de aceptación están redactados para poder verificarse con pruebas manuales, pruebas automatizadas o revisión de código.
- Las estimaciones son orientativas: `S` = 1–2 días, `M` = 3–5 días, `L` = 6–10 días, `XL` = más de 10 días de una persona.

### Principios de secuencia

1. **Primero la verdad, después la estética.** Ninguna mejora visual debe ocultar que los datos son de demostración.
2. **Primero los primitivos, después las pantallas.** Un `Field`, un `Modal`, una `DataTable` y un `ChartFrame` accesibles evitan repetir el mismo defecto 20 veces.
3. **No eliminar funcionalidades para “limpiar” la UI.** Si una acción no está implementada, se implementa o se retira con un mensaje honesto; no se deja como señuelo.
4. **No introducir métricas nuevas sin procedencia.** Toda cifra debe tener `n`, fecha de corte y fuente.
5. **No usar rojo para el olvido ni etiquetas alarmistas.** El lenguaje del proyecto es “por consolidar”, “refuerzo sugerido”, “sin evidencia suficiente”.

---

## 2. Resumen del backlog

| ID | Prioridad | Ítem | Complejidad | Dependencias |
|---|---|---|---|---|
| BL-01 | P0 | Capa de datos veraces y procedencia | L | Contratos API / Supabase |
| BL-02 | P0 | Recuperación de contraseña real | M–L | Backend de identidad |
| BL-03 | P0 | Contenido agnóstico a la asignatura | M | Contratos de contenido |
| BL-04 | P0 | Estados del sistema honestos | S–M | Endpoint de health |
| BL-05 | P1 | Marco de estados vacíos, error y reintento | M | BL-01 |
| BL-06 | P1 | Formularios accesibles | M | — |
| BL-07 | P1 | Modales y hojas accesibles | M | — |
| BL-08 | P1 | Tablas y gráficos accesibles | M | — |
| BL-09 | P1 | Foco, teclado y objetivos táctiles | S–M | BL-06, BL-07 |
| BL-10 | P1 | Legibilidad: tipografía y contraste | M | Tokens |
| BL-11 | P1 | Navegación íntegra: búsqueda y notificaciones | M | Producto |
| BL-12 | P1 | Login móvil sin truncamiento ni solapamiento | S | — |
| BL-13 | P1 | Lenguaje y terminología consistentes | S–M | — |
| BL-14 | P2 | Tokens y consolidación del sistema visual | M | Aprobación de dirección |
| BL-15 | P2 | Densidad responsive de dashboards | S–M | BL-14 |
| BL-16 | P2 | Simplificación del flujo de preguntas | L | BL-07 |
| BL-17 | P2 | Movimiento accesible | S | — |
| BL-18 | P2 | Encabezados, landmarks y skip link | S | — |
| BL-19 | P2 | Ubicación de “Estados del sistema” para estudiantes | S | BL-04 |
| BL-20 | P3 | Pulido de copy y pluralización | S | — |

---

## 3. Ítems P0

### BL-01 · P0 · Capa de datos veraces y procedencia

**Hallazgos cubiertos (auditoría):** A-01, A-02, A-08, A-09, A-10, C-07 (parcial), H-01, H-02.

**Objetivo:** que ninguna pantalla presente como real una cifra que no proviene de eventos del estudiante o de una consulta verificada; que todo dato de demostración sea explícito.

**Problema:** los clientes de API rellenan métricas con `||` y constantes; los dashboards las rotulan como “Métricas reales” y “Telemetría objetiva”; la nómina y los reportes muestran cohortes distintas.

**Pantallas:** `/dashboard`, `/progress`, `/teacher/dashboard`, `/teacher/reports`, `/teacher/students`, `/quiz/[id]/results`.

**Archivos:**
- `src/lib/api/learning.ts`
- `src/lib/api/teacher.ts`
- `src/lib/api/recommendations.ts`
- `src/app/(student)/dashboard/page.tsx`
- `src/app/(student)/progress/page.tsx`
- `src/app/teacher/dashboard/page.tsx`
- `src/app/teacher/reports/page.tsx`
- `src/app/teacher/students/page.tsx`
- `src/app/(student)/quiz/[id]/results/page.tsx`

**Beneficio:** restaura la confianza; permite un piloto defendible; evita decisiones pedagógicas basadas en ficciones; reduce el riesgo reputacional y ético.

**Complejidad:** L.

**Dependencias:** contratos de respuesta de FastAPI/Supabase; definición de `data_provenance` y `sample_size`; coordinación con backend para no romper tipos.

**Criterios de aceptación:**
- [ ] No queda ningún `|| <número>` que sustituya un conteo de eventos, estudiantes, intentos o precisión en las rutas listadas.
- [ ] Con 0 eventos, el dashboard muestra “Aún no hay evidencia suficiente” y no cifras de progreso.
- [ ] Cada KPI muestra `n` y fecha de corte, o un estado “sin datos”.
- [ ] La nómina, el dashboard y los reportes muestran el mismo `total_students` para la misma sección.
- [ ] El modo demo se activa solo con una bandera explícita y muestra un banner persistente “Datos de demostración” en todas las pantallas afectadas.
- [ ] El resultado de un cuestionario con 0 respuestas correctas muestra 0, no 2.
- [ ] Existe una prueba automatizada que falla si una respuesta vacía produce un número distinto de 0/null.

---

### BL-02 · P0 · Recuperación de contraseña real

**Hallazgos cubiertos (auditoría):** A-03.

**Objetivo:** que el restablecimiento de acceso sea verificable o que la pantalla no prometa una acción que no existe.

**Problema:** `handleRecoverySubmit` simula éxito con `setTimeout(700)`; no valida PIN ni actualiza la contraseña.

**Pantallas:** `/recovery`.

**Archivos:** `src/app/(auth)/recovery/page.tsx`; backend de identidad/OTP; posibles endpoints en `services/ml-api` o Supabase Auth.

**Beneficio:** evita bloqueos de cuenta y falsas expectativas; cumple la promesa de acceso institucional; reduce soporte manual.

**Complejidad:** M–L (depende de la decisión de identidad).

**Dependencias:** definir si el PIN lo emite el docente, la administración o Supabase; endpoint de validación; rate limiting; plantilla de errores.

**Criterios de aceptación:**
- [ ] El formulario no muestra éxito si el backend no confirma el cambio.
- [ ] Un PIN inválido, expirado o usado muestra un error claro y no permite continuar.
- [ ] Un PIN válido actualiza la contraseña y permite iniciar sesión con la nueva clave.
- [ ] Hay límite de intentos y mensaje de espera.
- [ ] Si el flujo no se implementa en este sprint, la ruta muestra un estado “Recuperación disponible a través de coordinación” y no un formulario funcional falso.
- [ ] Prueba E2E: solicitar → validar → cambiar → iniciar sesión.

---

### BL-03 · P0 · Contenido agnóstico a la asignatura

**Hallazgos cubiertos (auditoría):** A-04, C-02 (parcial).

**Objetivo:** eliminar todo texto, título, diagrama o nombre de curso hardcodeado que ate la UI a Ciencias o a un tema específico.

**Problema:** el detalle de recomendación sin datos muestra Fotosíntesis; el editor activa un diagrama de fotosíntesis por coincidencia de texto; el insight docente habla de Genética Molecular; varios fallbacks usan “Ciencias”.

**Pantallas:** `/recommendations/[id]`, `/learn/[id]`, `/teacher/reports`, `/recovery`, `/courses`, generación de contenido.

**Archivos:**
- `src/app/(student)/recommendations/[id]/page.tsx`
- `src/app/(student)/learn/[id]/page.tsx`
- `src/components/student/photosynthesis-diagram.tsx`
- `src/lib/api/learning.ts`
- `src/lib/api/teacher.ts`
- `src/lib/api/content-generation.ts`
- `src/app/(auth)/recovery/page.tsx`

**Beneficio:** permite reutilizar la plataforma en cualquier asignatura; evita contenido irrelevante; cumple una restricción arquitectónica del proyecto.

**Complejidad:** M.

**Dependencias:** contratos de `course`, `knowledge_component`, `microcontent`; registro de componentes por `content_type` si se conservan diagramas.

**Criterios de aceptación:**
- [ ] `grep` de “Ciencias”, “Fotosíntesis”, “Genética”, “Herencia mendeliana” en `src/app` y `src/lib/api` no devuelve literales de UI ni fallbacks.
- [ ] Sin recomendación, el detalle muestra un estado vacío genérico, no una lección de Fotosíntesis.
- [ ] El diagrama se elige por un campo de datos (`content_type`, `diagram_key`), no por `title.includes("fotosíntesis")`.
- [ ] El nombre del curso siempre proviene de `course.name`; si falta, se muestra “Curso” o “Sin asignatura”.
- [ ] La recuperación no menciona una asignatura concreta.
- [ ] Prueba con un curso ficticio de “Historia” que renderiza sin textos de Ciencias.

---

### BL-04 · P0 · Estados del sistema honestos

**Hallazgos cubiertos (auditoría):** A-05.

**Objetivo:** que la página de estado distinga “verificado”, “no verificado”, “no disponible” y “no medido”.

**Problema:** con la API caída muestra 0 ms y declara RLS/seudonimización “100 % activa” sin consultar; “última verificación” no tiene fecha.

**Pantallas:** `/system-status`.

**Archivos:** `src/app/system-status/page.tsx`; endpoint `/api/v1/health`; posible endpoint de estado de Supabase.

**Beneficio:** evita falsas garantías de seguridad; permite diagnosticar cold-start; mejora la confianza técnica.

**Complejidad:** S–M.

**Dependencias:** BL-01 para el concepto de procedencia; endpoint de health estable.

**Criterios de aceptación:**
- [ ] Si la API no responde, la latencia muestra “—” o “No medida”, nunca “0 ms”.
- [ ] RLS y seudonimización muestran “No verificado” si no hay una comprobación real.
- [ ] “Última verificación” incluye fecha, hora y zona.
- [ ] El estado “Modo demo” solo aparece si la bandera demo está activa.
- [ ] La página no afirma “100 %” sin una fuente verificable.
- [ ] Prueba con API arriba y abajo: los estados cambian correctamente.

---

## 4. Ítems P1 — Sprint 1

### BL-05 · P1 · Marco de estados vacíos, error y reintento

**Hallazgos cubiertos (auditoría):** A-06, A-07, A-09, C-05, F-04; refuerza A-01/A-02.

**Objetivo:** unificar cómo se muestran “cargando”, “vacío legítimo”, “sin resultados de filtro”, “error de red”, “sin permiso” y “sin datos suficientes”, con acciones claras.

**Problema:** los estados se construyen por página; algunos vacíos son una línea de texto; los errores muestran `Failed to fetch`; un fallo de red se disfraza de “no tienes cursos”; un quiz con 0 preguntas deja un botón deshabilitado.

**Pantallas:** `/courses`, `/learn/[id]`, `/quiz/[id]`, `/recommendations`, `/teacher/courses`, `/teacher/questions`, `/teacher/students`, `/dashboard`.

**Archivos:** páginas listadas; nuevo `components/ui/empty-state.tsx`, `components/ui/error-state.tsx`, `app/error.tsx`.

**Beneficio:** reduce abandono y soporte; el usuario siempre sabe qué pasó y qué hacer; elimina mensajes técnicos.

**Complejidad:** M.

**Dependencias:** BL-01 para distinguir datos vacíos de fallbacks; BL-03 para los textos genéricos.

**Criterios de aceptación:**
- [ ] Existe un componente `EmptyState` con icono, título, explicación, acción primaria, acción secundaria y nota de origen.
- [ ] Existe un componente `ErrorState` con copy humano, “Reintentar” y código de correlación solo en modo soporte.
- [ ] El quiz sin preguntas muestra una explicación y una salida, no un CTA deshabilitado como única opción.
- [ ] `/courses` distingue “no hay cursos” de “no pudimos cargar tus cursos”.
- [ ] Cada página tiene un estado de error de página (`error.tsx`) o usa el global.
- [ ] Prueba con red bloqueada: ninguna pantalla muestra `Failed to fetch` al usuario.

---

### BL-06 · P1 · Formularios accesibles

**Hallazgos cubiertos (auditoría):** D-01, D-04, D-05; refuerza C-01.

**Objetivo:** que todos los campos tengan nombre accesible, ayuda, error asociado y autofill correcto.

**Problema:** 29 `<label>` y solo 2 `htmlFor`; recuperación y formularios docentes sin asociación; inputs de auth sin `autocomplete`; toasts sin `aria-live`.

**Pantallas:** `/login`, `/recovery`, `/teacher/activities`, `/teacher/courses`, `/teacher/questions`, modales.

**Archivos:** nuevo `components/ui/field.tsx`; páginas de formularios; `login/page.tsx`; `recovery/page.tsx`.

**Beneficio:** permite completar formularios con lector de pantalla, dictado y autofill; reduce errores.

**Complejidad:** M.

**Dependencias:** BL-07 para los formularios dentro de modales.

**Criterios de aceptación:**
- [ ] Todo `<input>`, `<select>` y `<textarea>` tiene `id` y `htmlFor` (o está envuelto por `<label>`).
- [ ] Los errores usan `aria-describedby` y `aria-invalid`.
- [ ] Los campos de login tienen `autoComplete="username"` y `"current-password"`; recuperación usa `"new-password"`.
- [ ] Los toasts usan `role="status"`/`role="alert"` y `aria-live`.
- [ ] Prueba con lector de pantalla: cada campo anuncia su nombre, ayuda y error.
- [ ] Prueba de teclado: se puede completar y enviar sin ratón.

---

### BL-07 · P1 · Modales y hojas accesibles

**Hallazgos cubiertos (auditoría):** D-02, D-06.

**Objetivo:** que todos los overlays se comporten como diálogos accesibles y no pierdan el foco.

**Problema:** siete overlays con `fixed inset-0` sin `role="dialog"`, `aria-modal`, foco inicial, trampa de foco, Escape ni retorno de foco; el editor es denso y usa 10–11 px.

**Pantallas:** editor de preguntas, generación IA, rechazo, creación de actividad, creación de microcontenido, drawer móvil.

**Archivos:** nuevo `components/ui/modal.tsx`; `QuestionEditorModal.tsx`; `GenerateQuestionsModal.tsx`; `RejectReasonDialog.tsx`; `teacher/activities/page.tsx`; `teacher/courses/page.tsx`; `sidebar.tsx`.

**Beneficio:** desbloquea el uso con teclado y lector de pantalla; reduce errores de edición; mejora la percepción de calidad.

**Complejidad:** M.

**Dependencias:** BL-06 para los campos internos; BL-09 para el foco global.

**Criterios de aceptación:**
- [ ] Cada modal tiene `role="dialog"`, `aria-modal="true"` y `aria-labelledby`.
- [ ] Al abrir, el foco va al primer campo o al título; al cerrar, vuelve al disparador.
- [ ] Tab y Shift+Tab quedan atrapados dentro del modal.
- [ ] Escape cierra el modal (salvo confirmación destructiva con confirmación explícita).
- [ ] El fondo no recibe foco ni scroll.
- [ ] En móvil, el modal se presenta como hoja a pantalla completa o bottom sheet usable.
- [ ] Prueba manual con teclado en los seis overlays.

---

### BL-08 · P1 · Tablas y gráficos accesibles

**Hallazgos cubiertos (auditoría):** E-02, E-03.

**Objetivo:** que la información de tablas y gráficos sea accesible sin depender del color ni del SVG.

**Problema:** tablas sin `caption`/`scope`; gráficos Recharts sin nombre ni tabla alternativa; móvil con scroll horizontal.

**Pantallas:** `/progress`, `/teacher/students`, `/teacher/reports`.

**Archivos:** nuevo `components/ui/data-table.tsx`, `components/ui/chart-frame.tsx`; páginas listadas.

**Beneficio:** permite a estudiantes y docentes con baja visión o lectores de pantalla acceder a la evidencia; mejora la interpretación en móvil.

**Complejidad:** M.

**Dependencias:** BL-14 para tokens de color.

**Criterios de aceptación:**
- [ ] Cada tabla tiene `caption` (visible o `sr-only`) y `scope="col"`/`scope="row"`.
- [ ] Cada gráfico tiene `figure`/`figcaption` y un resumen textual.
- [ ] Cada gráfico ofrece “Ver datos” con una tabla equivalente.
- [ ] En móvil, la tabla se convierte en tarjetas o mantiene la primera columna fija con indicador de scroll.
- [ ] Los estados no dependen solo del color: incluyen texto o icono.
- [ ] Prueba con `axe` o revisión manual: 0 violaciones críticas en estas pantallas.

---

### BL-09 · P1 · Foco, teclado y objetivos táctiles

**Hallazgos cubiertos (auditoría):** E-01, E-05, D-03.

**Objetivo:** que toda la aplicación sea navegable con teclado y que los controles tengan un tamaño usable.

**Problema:** foco visible solo en `Button`; 50 botones nativos sin anillo; no hay skip link; botones `sm` de 32 px e `icon` de 36 px frente al estándar interno de 44 px.

**Pantallas:** todas.

**Archivos:** `globals.css`, `button.tsx`, `sidebar.tsx`, `header.tsx`, `app-shell.tsx`.

**Beneficio:** accesibilidad básica; reduce errores en móvil; mejora la percepción de calidad.

**Complejidad:** S–M.

**Dependencias:** BL-07 para el foco en modales.

**Criterios de aceptación:**
- [ ] `:focus-visible` global con anillo de 2 px y offset visible en `a`, `button`, `input`, `select`, `textarea`, `[tabindex]`.
- [ ] Skip link “Saltar al contenido” visible al foco.
- [ ] `aria-current="page"` en el enlace activo del sidebar.
- [ ] Acciones primarias y de tabla con `min-h-11` (44 px); iconos con área de 44 px.
- [ ] Prueba de Tab en login, dashboard, cursos, progreso, banco de preguntas y reportes.
- [ ] Sin cambios de layout que rompan la densidad de escritorio.

---

### BL-10 · P1 · Legibilidad: tipografía y contraste

**Hallazgos cubiertos (auditoría):** C-01, C-04.

**Objetivo:** que todo texto cumpla contraste AA y que la escala tipográfica sea legible para 16–17 años.

**Problema:** 101 usos de 10 px, 104 de 11 px, 138 de `text-slate-400` (2.56:1); la fuente real no es Inter.

**Pantallas:** todas, con foco en progreso, nómina y reportes.

**Archivos:** `globals.css`, `tailwind.config.ts`, `layout.tsx`, páginas con clases pequeñas.

**Beneficio:** mejora la lectura en móvil, aulas proyectadas y baja visión; reduce fatiga.

**Complejidad:** M.

**Dependencias:** BL-14 para tokens.

**Criterios de aceptación:**
- [ ] No hay texto de UI por debajo de 12 px; el cuerpo mínimo es 14 px y el texto principal 16 px.
- [ ] `text-muted` tiene contraste ≥ 4.5:1 sobre `surface` y `card`.
- [ ] Inter (o la fuente elegida) se carga de forma consistente y coincide con la especificación.
- [ ] Los números de métricas usan `font-variant-numeric: tabular-nums`.
- [ ] Auditoría de contraste en las 10 pantallas principales: 0 fallos AA.
- [ ] Prueba visual a 390 px y 1440 px.

---

### BL-11 · P1 · Navegación íntegra: búsqueda y notificaciones

**Hallazgos cubiertos (auditoría):** B-01, B-02.

**Objetivo:** que ningún control visible sea un señuelo; o funciona, o se retira con honestidad.

**Problema:** la búsqueda global no tiene handler; la campana no tiene onClick y muestra un punto permanente.

**Pantallas:** shell global.

**Archivos:** `header.tsx`; posible página/panel de resultados; API de búsqueda.

**Beneficio:** recupera una necesidad primaria (encontrar cursos/preguntas/estudiantes) y elimina frustración.

**Complejidad:** M.

**Dependencias:** decisión de producto sobre alcance de búsqueda; API o filtro local.

**Criterios de aceptación:**
- [ ] La búsqueda filtra o navega con Enter y muestra resultados/estado vacío.
- [ ] La búsqueda tiene `aria-label`, `role="search"` y resultados anunciados.
- [ ] La campana abre un panel con notificaciones reales o se elimina.
- [ ] El punto de no leídas solo aparece si hay notificaciones no leídas.
- [ ] Prueba de teclado y de móvil.

---

### BL-12 · P1 · Login móvil sin truncamiento ni solapamiento

**Hallazgos cubiertos (auditoría):** F-01, F-06.

**Objetivo:** que el primer contacto en móvil sea claro, táctil y sin elementos superpuestos.

**Problema:** tarjetas de rol truncadas (“Estudiant…”, “Aprender…”, “Gestiona…”); botón “?” sobre “Ver presentación”; CTA deshabilitado pálido sin explicación; header comprimido.

**Pantallas:** `/login` a 390 px; header móvil.

**Archivos:** `login/page.tsx`, `header.tsx`.

**Beneficio:** mejora la conversión y la percepción de calidad en el dispositivo más usado por estudiantes.

**Complejidad:** S.

**Dependencias:** ninguna.

**Criterios de aceptación:**
- [ ] Las tarjetas de rol muestran el texto completo o una versión corta aprobada, sin `…`.
- [ ] El botón de ayuda no se superpone a ningún enlace ni CTA.
- [ ] El CTA deshabilitado explica qué falta (“Ingresa tu correo y contraseña”).
- [ ] El header móvil no trunca la búsqueda de forma que parezca rota; si se colapsa, abre un campo completo.
- [ ] Prueba en 320, 390 y 430 px.

---

### BL-13 · P1 · Lenguaje y terminología consistentes

**Hallazgos cubiertos (auditoría):** C-02, B-04; refuerza C-07.

**Objetivo:** español consistente, sin jerga innecesaria y con un glosario único de roles y navegación.

**Problema:** “Student Mastery Heat Map”, “Class Performance Overview”, “RLS Enforced”, “PIN de Docente (OTP)”, “Alumno”/“Estudiante”, “Dashboard”/“Inicio”.

**Pantallas:** reportes, preguntas, system status, recuperación, shell.

**Archivos:** páginas listadas; posible archivo `src/lib/copy.ts` o diccionario.

**Beneficio:** reduce carga cognitiva; mejora la percepción de producto cuidado; facilita la traducción futura.

**Complejidad:** S–M.

**Dependencias:** BL-19 para la separación de audiencias.

**Criterios de aceptación:**
- [ ] Glosario aplicado: “Estudiante”, “Docente”, “Inicio”, “Panel”, “Curso”, “Componente de conocimiento”.
- [ ] Títulos de reportes en español: “Mapa de dominio por componente”, “Rendimiento del grupo”.
- [ ] La jerga técnica (RLS, Append-Only, `auth.uid()`) solo aparece en una vista técnica o con explicación.
- [ ] El copy de recuperación no dice “PIN de Docente” si el usuario es estudiante.
- [ ] Revisión de copy con una persona del equipo pedagógico.

---

## 5. Ítems P2

### BL-14 · P2 · Tokens y consolidación del sistema visual

**Hallazgos cubiertos (auditoría):** C-03, C-05, C-06.

**Objetivo:** reducir la deriva visual y facilitar cambios futuros.

**Problema:** 310 literales hex, 52 colores únicos, tres radios sin regla, estados vacíos y tarjetas reconstruidos por página.

**Pantallas:** todas.

**Archivos:** `globals.css`, `tailwind.config.ts`, `components/ui/*`, páginas.

**Beneficio:** consistencia, menor costo de mantenimiento, base para modo oscuro futuro.

**Complejidad:** M.

**Dependencias:** aprobación de `04_DESIGN_DIRECTION.md`.

**Criterios de aceptación:**
- [ ] Tokens semánticos para color, superficie, texto, borde, radio y sombra.
- [ ] Las páginas no contienen hex de marca; solo tokens o clases Tailwind semánticas.
- [ ] Radios: control 10 px, input 12 px, card 16 px, hero 20 px.
- [ ] `EmptyState`, `Card`, `Badge` y `Button` son las únicas implementaciones base.
- [ ] Revisión visual de las 10 pantallas principales.

---

### BL-15 · P2 · Densidad responsive de dashboards

**Hallazgos cubiertos (auditoría):** F-02, F-03.

**Objetivo:** que el estudiante y el docente puedan escanear lo esencial en el primer viewport móvil.

**Problema:** cuatro KPI en una columna larga; título de dos líneas; gráfico y tabla fuera del pliegue.

**Pantallas:** `/teacher/dashboard`, `/progress` a 390 px.

**Archivos:** páginas listadas.

**Beneficio:** mejor toma de decisiones en móvil; menos scroll; mayor percepción de utilidad.

**Complejidad:** S–M.

**Dependencias:** BL-14, BL-08.

**Criterios de aceptación:**
- [ ] KPIs en 2×2 en móvil, con una métrica principal destacada.
- [ ] El gráfico de progreso aparece antes de los KPIs secundarios o en un resumen compacto.
- [ ] La tabla de KC se convierte en tarjetas/acordeón en móvil.
- [ ] El primer viewport muestra al menos una acción y una métrica clave.
- [ ] Prueba en 390 px y 430 px.

---

### BL-16 · P2 · Simplificación del flujo de preguntas

**Hallazgos cubiertos (auditoría):** F-05, D-06.

**Objetivo:** reducir la carga cognitiva del docente al revisar y editar preguntas.

**Problema:** una sola vista con KPIs, carpeta, buscador, filtro de KC, tabs y cinco filtros; modal de dos columnas con 10–11 px.

**Pantallas:** `/teacher/questions` y modales.

**Archivos:** `teacher/questions/page.tsx`, `QuestionEditorModal.tsx`, `GenerateQuestionsModal.tsx`.

**Beneficio:** menos errores de filtro y de edición; revisiones más rápidas.

**Complejidad:** L.

**Dependencias:** BL-07, BL-13.

**Criterios de aceptación:**
- [ ] Separar “Banco publicado” y “Cola de revisión” en dos vistas o tabs claros.
- [ ] Mostrar filtros activos como chips removibles.
- [ ] El editor se divide en pasos: enunciado → opciones → metadatos → vista previa.
- [ ] Texto del editor ≥ 14 px.
- [ ] Prueba con 5 docentes: reducción del tiempo de revisión y de errores.

---

### BL-17 · P2 · Movimiento accesible

**Hallazgos cubiertos (auditoría):** E-06.

**Objetivo:** respetar las preferencias de movimiento y reducir distracciones.

**Problema:** animaciones orbitales infinitas y `animate-pulse` sin `prefers-reduced-motion`.

**Pantallas:** login, cargas, shell.

**Archivos:** `globals.css`, `solar-system-orbit.tsx`.

**Beneficio:** accesibilidad vestibular; menos consumo; interfaz más tranquila.

**Complejidad:** S.

**Dependencias:** ninguna.

**Criterios de aceptación:**
- [ ] `@media (prefers-reduced-motion: reduce)` desactiva animaciones infinitas y reduce transiciones.
- [ ] La animación orbital no es necesaria para comprender la página.
- [ ] Las transiciones de UI duran 150–200 ms.
- [ ] Prueba con la preferencia activada en el sistema operativo.

---

### BL-18 · P2 · Encabezados, landmarks y skip link

**Hallazgos cubiertos (auditoría):** E-04, E-05.

**Objetivo:** una estructura semántica predecible en todas las páginas.

**Problema:** `h1` de marca en login; `CardTitle` fijo en `h3`; sin skip link; sin `aria-current`.

**Pantallas:** todas.

**Archivos:** `card.tsx`, `app-shell.tsx`, `sidebar.tsx`, `login/page.tsx`, páginas.

**Beneficio:** navegación por encabezados y landmarks; mejor experiencia con lector de pantalla.

**Complejidad:** S.

**Dependencias:** BL-09.

**Criterios de aceptación:**
- [ ] Un `h1` por página, con el título de la tarea.
- [ ] `CardTitle` acepta `as` y por defecto es `h2` cuando cuelga de `h1`.
- [ ] Skip link funcional y visible al foco.
- [ ] `aria-current="page"` en la navegación activa.
- [ ] Revisión con un árbol de accesibilidad.

---

### BL-19 · P2 · Ubicación de “Estados del sistema” para estudiantes

**Hallazgos cubiertos (auditoría):** B-03.

**Objetivo:** que el estudiante no vea jerga de infraestructura en su navegación principal.

**Problema:** “Estados del sistema” está al mismo nivel que “Mis cursos”; la página usa FastAPI, RLS y cold-start.

**Pantallas:** sidebar de estudiante, `/system-status`.

**Archivos:** `sidebar.tsx`, `system-status/page.tsx`.

**Beneficio:** reduce ruido cognitivo y evita interpretaciones erróneas de problemas técnicos.

**Complejidad:** S.

**Dependencias:** BL-04, BL-13.

**Criterios de aceptación:**
- [ ] La página sale de la navegación principal del estudiante o se renombra “Estado del servicio”.
- [ ] Si se conserva, muestra un resumen simple (“Todo funciona”, “Estamos revisando”) y un enlace “Detalle técnico”.
- [ ] La vista técnica queda para docentes/administradores.
- [ ] Prueba con un estudiante: puede explicar qué significa el estado.

---

## 6. Ítems P3

### BL-20 · P3 · Pulido de copy y pluralización

**Hallazgos cubiertos (auditoría):** C-07, B-04 (resto).

**Objetivo:** eliminar errores de concordancia y frases que afirmen más de lo que los datos permiten.

**Problema:** “1 cursos asignados”, “1 secciones asignadas”, “5 repasados oportunamente”.

**Pantallas:** preguntas, dashboard docente, progreso.

**Archivos:** páginas listadas; utilidad de pluralización.

**Beneficio:** credibilidad y cuidado percibido.

**Complejidad:** S.

**Dependencias:** BL-01, BL-13.

**Criterios de aceptación:**
- [ ] “1 curso asignado” / “2 cursos asignados”; “1 sección asignada” / “2 secciones asignadas”.
- [ ] Las frases con números usan una utilidad de pluralización.
- [ ] No se afirma “repasado oportunamente” sin un evento que lo respalde.
- [ ] Revisión de copy en las 10 pantallas principales.

---

## 7. Roadmap sugerido

### Semana 1 — Verdad y acceso (P0)

| Día | Trabajo | Entregable |
|---|---|---|
| 1–2 | BL-01: eliminar defaults, definir procedencia, estados “sin datos” | Contratos + dashboard/progreso honestos |
| 2–3 | BL-02: flujo real de recuperación o deshabilitación honesta | Pantalla de recuperación verificable |
| 3–4 | BL-03: barrido de contenido específico de Ciencias | Fallbacks genéricos |
| 4–5 | BL-04: estados del sistema honestos | Página de estado con “no verificado” |

**Gate:** no se pasa a la semana 2 sin una prueba que demuestre que 0 eventos producen 0/null y no cifras demo.

### Semana 2 — Accesibilidad estructural (P1)

| Día | Trabajo | Entregable |
|---|---|---|
| 1–2 | BL-06 + BL-07: `Field` y `Modal` accesibles | Formularios y modales con foco/etiquetas |
| 2–3 | BL-09: foco global, skip link, targets | Navegación por teclado |
| 3–4 | BL-08: `DataTable` y `ChartFrame` | Tablas/gráficos con alternativa |
| 4–5 | BL-05: `EmptyState`/`ErrorState` + `error.tsx` | Estados unificados |

**Gate:** prueba de teclado y lector de pantalla en login, dashboard, cursos, quiz, preguntas y reportes.

### Semana 3 — Legibilidad y navegación (P1–P2)

| Trabajo | Entregable |
|---|---|
| BL-10: tipografía/contraste | Escala y tokens AA |
| BL-11: búsqueda y notificaciones | Control funcional o retirado |
| BL-12: login móvil | Primer contacto sin truncamiento |
| BL-13: lenguaje | Glosario aplicado |
| BL-14: tokens | Sistema visual consolidado |

### Semana 4 — Densidad y pulido (P2–P3)

| Trabajo | Entregable |
|---|---|
| BL-15: dashboards responsive | 2×2 móvil, tabla en tarjetas |
| BL-16: flujo de preguntas | Editor por pasos |
| BL-17: movimiento | Reduced motion |
| BL-18: encabezados | Jerarquía y landmarks |
| BL-19/BL-20: ubicación de estado y copy | Navegación y copy final |

---

## 8. Métricas de éxito del rediseño

| Métrica | Línea base | Meta |
|---|---|---|
| Cifras de UI sin `n`/fecha/fuente | Dashboard, progreso, reportes con múltiples cifras sin contexto | 0 |
| Contradicciones de conteo entre pantallas | Docente: 0 vs 10 estudiantes | 0 |
| Estados de error que muestran texto técnico | `Failed to fetch` visible | 0 |
| Formularios con etiqueta asociada | 2 de 29 labels | 100 % |
| Contraste AA en texto normal | `slate-400` 2.56:1 | 100 % |
| Modales con foco atrapado/Escape | 0 de 7 | 7 de 7 |
| Tablas con `caption`/`scope` | 0 de 3 principales | 3 de 3 |
| Gráficos con alternativa textual | 0 de 3 | 3 de 3 |
| Login móvil sin truncamiento/solapamiento | Truncado y superpuesto | 0 defectos |
| Tiempo de revisión de una pregunta (docente) | Línea base a medir | −20 % |
| Comprensión de “Retención Óptima” | Línea base a medir | ≥ 80 % interpreta correctamente |

Las metas de tiempo y comprensión requieren prueba con usuarios; no deben presentarse como resultados hasta medirlas.

---

## 9. Dependencias y riesgos

| Riesgo | Impacto | Mitigación |
|---|---|---|
| El backend no expone `n`/fecha de corte | BL-01 no se puede cerrar | Acordar contrato antes de tocar la UI; usar `null` mientras tanto. |
| El flujo de recuperación depende de una decisión de identidad | BL-02 se retrasa | Deshabilitar honestamente la pantalla en el interino. |
| Cambiar tokens rompe pantallas no auditadas | Regresiones visuales | Hacer el barrido con búsqueda de clases y revisión visual de las 18 rutas. |
| Los docentes prefieren la densidad actual | BL-16 no se adopta | Probar prototipo con 5 docentes antes de implementar. |
| El contenido agnóstico requiere cambios de datos | BL-03 se limita a la UI | Empezar por eliminar literales; luego mover diagramas a datos. |
| El equipo no tiene lector de pantalla | BL-06/BL-07 no se validan | Usar `axe`, árbol de accesibilidad y una prueba manual con NVDA/VoiceOver. |

---

## 10. Definición de “terminado” para el Sprint 0/1

Un ítem se considera terminado cuando:

1. Cumple todos sus criterios de aceptación.
2. Tiene prueba automatizada o evidencia manual registrada.
3. No introduce literales hex nuevos ni textos hardcodeados de asignatura.
4. No degrada el contraste ni el tamaño mínimo de texto.
5. Fue revisado en 390 px y 1440 px.
6. Fue revisado con teclado.
7. Actualiza `docs/ui-ux/2026-11-07/` si cambia una decisión de diseño.
8. Pasa lint, typecheck y build del workspace web.

---

## 11. Lo que no se debe hacer

- No añadir gamificación (rachas, XP, rankings) para “compensar” la falta de datos.
- No usar rojo para “olvido” ni etiquetas como “en riesgo” en la UI del estudiante.
- No mostrar gráficos nuevos sin tabla o resumen textual.
- No mantener la búsqueda/campana como decoración.
- No crear un “modo demo” que se active silenciosamente en producción.
- No prometer recuperación de contraseña sin backend.
- No hardcodear “Ciencias”, “Fotosíntesis” ni “Genética” en textos, diagramas o fallbacks.
- No cerrar un ítem P0 con una captura de pantalla: se requiere prueba de comportamiento.
