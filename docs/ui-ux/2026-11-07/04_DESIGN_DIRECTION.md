# 04 — Dirección de diseño

**Proyecto:** Plataforma de Microaprendizaje Adaptativo
**Fecha:** 2026-11-07
**Estado:** propuesta para revisión; no implementada.
**Documento base:** `02_UI_UX_AUDIT.md` y `03_REDESIGN_BACKLOG.md`.

---

## 1. Tesis de diseño

> **Una plataforma que se siente como un mentor sereno: rigurosa con la evidencia, clara con el estudiante y honesta cuando no sabe.**

La interfaz actual ya tiene una identidad valiosa: el verde azulado profundo transmite calma y seriedad, y el acento menta aporta energía sin infantilizar. No se propone abandonar esa identidad. Se propone **ordenarla, hacerla legible y subordinarla a la verdad de los datos**.

El rediseño debe lograr tres cosas:

1. **Que el estudiante entienda qué sabe y qué le conviene hacer hoy**, sin métricas decorativas ni falsas certezas.
2. **Que el docente pueda tomar decisiones con evidencia**, viendo el tamaño de muestra, la fecha y la diferencia entre observado y estimado.
3. **Que la plataforma sea confiable incluso cuando falla**: un error se ve como error, un vacío se ve como vacío y un dato demo se ve como demo.

### Lo que no es este rediseño

- No es una capa de gamificación.
- No es un cambio de marca radical.
- No es un dashboard más denso.
- No es una promesa de que el modelo predice el olvido con certeza.

---

## 2. Personalidad

| Atributo | Sí | No |
|---|---|---|
| **Sereno** | Espacio en blanco, ritmo pausado, transiciones breves | Animaciones infinitas, colores saturados, ruido visual |
| **Riguroso** | Cifras con `n`, fecha y fuente; estados “sin datos” | Fórmulas mágicas, porcentajes sin contexto, insights inventados |
| **Humano** | “Por consolidar”, “refuerzo sugerido”, “a tu ritmo” | “Riesgo alto”, “olvido”, “reprobado”, alarmismo |
| **Adulto** | Tipografía sobria, iconografía lineal, densidad controlada | Estética infantil, mascotas, confeti, emojis decorativos |
| **Transparente** | “Datos de demostración”, “No verificado”, “No medido” | Simulaciones silenciosas, éxito falso, botones señuelo |
| **Ágil** | Una acción primaria por pantalla, atajos, búsqueda real | Formularios interminables, navegación profunda |

**Arquetipo:** el mentor de laboratorio. Alguien que sabe mucho, no presume, explica con calma y dice “todavía no tenemos evidencia” cuando corresponde.

---

## 3. Principios de diseño

### 3.1 La evidencia manda

Ninguna cifra aparece sin tres datos: **qué mide**, **sobre cuántos eventos** y **a qué fecha**. Si falta uno, se muestra un estado “sin datos suficientes”.

### 3.2 Observado ≠ estimado

La precisión observada es un hecho medido. La retención estimada es una probabilidad de modelo. Nunca se mezclan en el mismo estilo visual ni en la misma frase sin etiqueta.

- **Observado:** color sólido, etiqueta “Observado”, `n` visible.
- **Estimado:** línea discontinua o relleno tenue, etiqueta “Estimado”, incertidumbre si existe.
- **Sin evidencia:** gris neutro, texto “Sin datos suficientes”.

### 3.3 Una acción primaria por pantalla

El estudiante debe saber en 5 segundos qué hacer hoy. El docente debe saber en 10 segundos qué sección necesita atención. Todo lo demás es secundario.

### 3.4 Los estados vacíos son parte del producto

Un vacío no es un error de diseño: es una oportunidad de explicar el siguiente paso. Todo vacío tiene título, causa, acción y, si aplica, nota de origen de datos.

### 3.5 La accesibilidad no es una capa final

Los componentes se diseñan con foco, etiqueta, contraste y teclado desde el inicio. No se “arregla” después con un barrido.

### 3.6 El color no es la única señal

Los estados usan color + texto + icono. Los gráficos tienen tabla o resumen. Las leyendas tienen valores, no solo muestras de color.

### 3.7 La densidad es una decisión de rol

El estudiante necesita aire y foco. El docente necesita comparar y filtrar. Comparten tokens, no la misma densidad.

---

## 4. Concepto visual: “cuaderno de laboratorio sereno”

La metáfora es un cuaderno de laboratorio bien ordenado:

- **Fondo claro y cálido** para reducir la fatiga.
- **Tinta oscura** para el texto, no negro puro.
- **Verde azulado** para la marca y las acciones.
- **Menta** para el acento adaptativo, usado con moderación.
- **Líneas finas y etiquetas** como anotaciones de laboratorio.
- **Datos con fecha y fuente**, como un registro.

La ilustración orbital del login puede conservarse como **momento de marca**, pero no como centro de gravedad. En el producto, la metáfora se expresa en la claridad, no en el espacio exterior.

### Antes / después conceptual

| Antes | Después |
|---|---|
| Hero “Retención Óptima” con métricas ficticias | “Tu estado de hoy” con evidencia real o “Sin datos suficientes” |
| 52 colores hex | 12 tokens semánticos |
| 10–11 px en tablas | 12 px mínimo, 14 px cuerpo |
| Tarjetas con tres radios | Control 10 / input 12 / card 16 / hero 20 |
| Insight inventado | “Insight no disponible: faltan al menos N eventos” |
| Búsqueda decorativa | Búsqueda real o ausente |
| Modales sin foco | Diálogo con foco atrapado y Escape |
| Gráfico solo SVG | Gráfico + resumen + tabla |

---

## 5. Color

### 5.1 Paleta propuesta

| Token | Hex | Uso | Contraste |
|---|---|---|---|
| `--brand-900` | `#0B2D34` | Sidebar, fondos oscuros, texto sobre menta | 8.45:1 con `#69D7C9` |
| `--brand-700` | `#0A635F` | Acción primaria, enlaces, énfasis | 7.09:1 con blanco |
| `--brand-100` | `#DDF4F0` | Fondo de énfasis suave | — |
| `--accent-400` | `#69D7C9` | Acento, iconos sobre oscuro, no texto sobre blanco | 8.45:1 sobre `#0B2D34` |
| `--surface` | `#F7FAFA` | Fondo de app | — |
| `--card` | `#FFFFFF` | Tarjetas y superficies | — |
| `--border` | `#DCE7E6` | Bordes decorativos | — |
| `--input-border` | `#6F8A8C` | Bordes de campos | 3.69:1 con blanco |
| `--text` | `#102A2E` | Texto principal | 15.08:1 con blanco |
| `--text-secondary` | `#3E5A5F` | Texto secundario | 7.41:1 con blanco |
| `--text-muted` | `#4A6267` | Metadatos, ayudas | 6.19:1 sobre `#F7FAFA` |
| `--success` | `#0F7A5A` | Éxito, consolidado | 5.31:1 con blanco |
| `--warning` | `#9A5B00` | Por consolidar, atención | 5.43:1 con blanco |
| `--danger` | `#B42318` | Error de sistema, acción destructiva | 6.57:1 con blanco |
| `--info` | `#1D4ED8` | Información, enlaces secundarios | 6.70:1 con blanco |
| `--adaptive` | `#5B21B6` | Recomendación adaptativa | 8.19:1 sobre `#F5F3FF` |
| `--adaptive-bg` | `#F5F3FF` | Fondo de recomendación | — |

### 5.2 Reglas

- **No usar menta como texto sobre blanco.** `#69D7C9` sobre blanco no alcanza AA. La menta es fondo/acento sobre oscuro o icono grande.
- **No usar rojo para el olvido.** El rojo se reserva para errores del sistema y acciones destructivas. “Por consolidar” usa ámbar (`--warning`).
- **Máximo dos acentos por pantalla:** brand + adaptive, o brand + warning. No compiten cuatro colores.
- **Estados siempre con texto.** “Consolidado”, “En proceso”, “Por consolidar”, no solo un punto de color.
- **Superficies:** una sola elevación por tarjeta; evitar gradientes salvo el hero principal.
- **Modo oscuro:** no es prioridad; si se implementa, debe repetir la auditoría de contraste.

### 5.3 Colores a retirar

- `#0f766e` y `#0d9488` como botones alternativos: unificar en `--brand-700`.
- `#39BEAD` y `#65D7C9` como textos: reemplazar por `--brand-700` o `--accent-400` según fondo.
- `#f8fafc` hardcodeado: reemplazar por `--surface`.
- `text-slate-400` en texto normal: reemplazar por `--text-muted`.

---

## 6. Tipografía

### 6.1 Familia

**Inter** (según `docs/ux/design-specs.md`), cargada con `next/font` y fallback:

```css
font-family: Inter, ui-sans-serif, system-ui, -apple-system, "Segoe UI", sans-serif;
```

Si el equipo decide no cargar una fuente externa, actualizar la especificación a `system-ui` y asumir la variabilidad entre sistemas. Lo que no puede pasar es que la especificación diga Inter y la app use otra cosa sin documentarlo.

### 6.2 Escala

| Rol | Tamaño / línea | Peso | Uso |
|---|---|---|---|
| Display | 36 / 44 | 700 | Hero de login, cifras grandes |
| H1 | 30 / 38 | 700 | Título de página |
| H2 | 24 / 32 | 700 | Sección |
| H3 | 20 / 28 | 600 | Subsección, tarjeta destacada |
| Lead | 18 / 28 | 400 | Introducción de página |
| Body | 16 / 26 | 400 | Texto principal |
| Body small | 14 / 22 | 400 | Tablas, ayudas, texto secundario |
| Caption | 12 / 18 | 500 | Metadatos, timestamps, badges |
| Overline | 12 / 16 | 700 | Etiquetas de sección, mayúsculas + 0.06em |

**Mínimos:** 12 px para cualquier texto; 14 px para cuerpo de tabla; 16 px para texto principal del estudiante. No usar 10 u 11 px en texto de interfaz.

### 6.3 Reglas

- Máximo 70 caracteres por línea en texto de lectura.
- `font-variant-numeric: tabular-nums` en métricas y tablas.
- No usar mayúsculas sostenidas en párrafos; solo en overlines cortos.
- No usar `font-black` (900) para texto pequeño; engorda y reduce legibilidad.
- Jerarquía por tamaño + peso + color, no por cinco tamaños distintos en la misma tarjeta.

---

## 7. Espaciado, radios y elevación

### 7.1 Espaciado (base 4)

`4, 8, 12, 16, 20, 24, 32, 40, 48, 64`

- Dentro de un componente: 8–16.
- Entre componentes: 16–24.
- Entre secciones: 32–40.
- Padding de página: 16 móvil, 24 tablet, 32–40 escritorio.

### 7.2 Radios

| Token | Valor | Uso |
|---|---|---|
| `--radius-control` | 10 px | Botones, inputs, selects |
| `--radius-card` | 16 px | Tarjetas, paneles |
| `--radius-hero` | 20 px | Hero, banner |
| `--radius-pill` | 999 px | Badges, chips |

No usar `rounded-3xl` en tarjetas pequeñas ni mezclar 8/12/16/20 sin regla.

### 7.3 Elevación

| Nivel | Sombra | Uso |
|---|---|---|
| 0 | ninguna | Tablas, secciones planas |
| 1 | `0 1px 2px rgba(11,45,52,.05)` | Tarjetas |
| 2 | `0 8px 24px rgba(11,45,52,.08)` | Modales, dropdowns |
| 3 | `0 16px 40px rgba(11,45,52,.12)` | Solo hero o overlay |

La elevación no sustituye el borde: las tarjetas tienen borde de 1 px y sombra suave.

---

## 8. Layout y responsive

### 8.1 Estructura

- Sidebar: 256 px en escritorio; drawer en móvil.
- Header: 64 px; sticky; búsqueda funcional o colapsada.
- Contenido: `max-width: 1200px` para lectura; 1360 px para tablas docentes cuando se necesite.
- Grid: 12 columnas en escritorio; 4 en tablet; 1 en móvil.
- Gutter: 24 px escritorio, 16 px móvil.

### 8.2 Breakpoints

| Nombre | Ancho | Comportamiento |
|---|---|---|
| `sm` | 480 | KPI 2×2, formularios de una columna |
| `md` | 768 | Sidebar visible en tablet horizontal; tablas con scroll |
| `lg` | 1024 | Sidebar fijo; split panes |
| `xl` | 1280 | Contenido amplio; tablas docentes |

### 8.3 Reglas móviles

- Una acción primaria visible en el primer viewport.
- KPI en 2×2, no en una columna de cuatro.
- Tablas convertidas en tarjetas o acordeón.
- Gráficos con resumen textual antes del SVG.
- Header sin búsqueda truncada; icono que abre campo completo.
- Botón de ayuda sin superposición.

---

## 9. Componentes

### 9.1 Botones

| Variante | Uso | Estilo |
|---|---|---|
| Primario | Acción principal | `--brand-700`, texto blanco, 44 px |
| Secundario | Acción alternativa | Fondo `--brand-100`, texto `--brand-700` |
| Outline | Acción terciaria | Borde `--input-border`, texto `--text` |
| Ghost | Acción en tablas/toolbars | Sin fondo, hover suave |
| Destructivo | Eliminar/rechazar | `--danger`, confirmación |
| Link | Navegación textual | Subrayado en hover/focus |

**Estados:** hover, focus-visible, active, loading, disabled. El estado deshabilitado debe explicar la causa con texto o tooltip accesible, no solo opacidad.

### 9.2 Tarjetas

- Fondo `--card`, borde `--border`, radio 16, sombra nivel 1.
- Header con título y acción; body; footer opcional.
- No usar gradientes en tarjetas de datos.
- Una tarjeta = una idea. No meter tres tablas en una tarjeta.

### 9.3 KPI

```
┌─────────────────────────────┐
│ PRECISIÓN OBSERVADA         │  overline 12
│ 69.4 %                      │  display 32, tabular
│ n = 36 respuestas · 7 nov   │  caption 12
│ [Observado]                 │  badge
└─────────────────────────────┘
```

Reglas:
- Siempre `n` y fecha o “sin datos”.
- No mostrar variación si no hay periodo comparable.
- No usar flechas verdes/rojas sin explicar la dirección.
- Si el dato es demo, badge “Demo” y borde punteado.

### 9.4 Badges

- `Consolidado` (success), `En proceso` (warning), `Por consolidar` (warning suave), `Sin datos` (neutral), `Demo` (adaptive/neutral).
- No usar rojo para el estado pedagógico.
- Texto siempre; icono opcional.

### 9.5 Estado vacío

```
[icono]
Título claro
Explicación de por qué está vacío
[Acción primaria]  [Acción secundaria]
Nota: “Datos al 7 nov 2026” o “No pudimos cargar…”
```

### 9.6 Estado de error

- Copy humano: “No pudimos cargar tus cursos.”
- Explicación breve: “Revisa tu conexión e inténtalo de nuevo.”
- Acción: “Reintentar”.
- Soporte: código de correlación solo si el usuario lo necesita.
- Nunca `Failed to fetch`, `HTTP 500` ni un stack trace.

### 9.7 Tabla de datos

- `caption` visible o `sr-only`.
- `scope="col"` y `scope="row"`.
- Header sticky en tablas largas.
- Primera columna fija en móvil.
- Fila con hover y foco.
- Acciones con etiqueta accesible, no solo icono.
- En móvil: tarjetas con label/value o acordeón.

### 9.8 Gráfico

- `figure` + `figcaption`.
- Título, subtítulo, leyenda y `n`.
- Resumen textual: “La precisión subió de 66.7 % a 72.2 % en 6 semanas.”
- Botón “Ver datos” con tabla.
- Eje Y de 0 a 100; no truncar.
- Línea observada sólida; estimada discontinua.
- No usar dos ejes Y.
- No usar pastel/dona para proporciones pequeñas; usar barra apilada con etiquetas.

### 9.9 Modal / hoja

- `role="dialog"`, `aria-modal="true"`, `aria-labelledby`.
- Foco inicial en el título o primer campo.
- Trampa de foco; Escape; retorno al disparador.
- En móvil: bottom sheet o pantalla completa.
- Título claro y acción primaria fija al pie.
- No usar modales para flujos de más de 3 pasos; usar página.

### 9.10 Formulario

- Label visible, `htmlFor`/`id`.
- Ayuda con `aria-describedby`.
- Error con `aria-invalid` y texto.
- `autocomplete` correcto.
- Campo obligatorio marcado con texto, no solo asterisco.
- Validación al salir del campo, no en cada tecla.
- Botón de envío con estado loading y errores resumidos al inicio.

### 9.11 Navegación

- Sidebar con `aria-current="page"`.
- Skip link al contenido.
- Header con búsqueda real o colapsada.
- Campana solo si hay notificaciones reales.
- En móvil, drawer con foco atrapado y cierre con Escape.

### 9.12 Toasts

- Éxito: `role="status"`, `aria-live="polite"`, 4 s.
- Error: `role="alert"`, `aria-live="assertive"`, persistente hasta cierre.
- No depender del color; incluir icono y texto.

---

## 10. Lenguaje de datos

### 10.1 Dos capas visuales

| Capa | Qué es | Estilo | Etiqueta |
|---|---|---|---|
| **Observado** | Precisión, aciertos, intentos, tiempo | Sólido, `--brand-700` | “Observado” |
| **Estimado** | Probabilidad de retención, riesgo, tiempo hasta olvido | Discontinuo/tenue, `--adaptive` o `--warning` | “Estimado” |
| **Sin evidencia** | No hay eventos suficientes | Gris neutro | “Sin datos suficientes” |

### 10.2 Reglas de presentación

- No mostrar una probabilidad como certeza. “Probabilidad estimada de recordar: 72 %” no es “recordarás”.
- No usar “olvidarás” ni “en riesgo” en la UI del estudiante.
- Mostrar `n` y fecha de corte.
- Si el modelo no está validado, mostrar “Modelo en validación” y no una cifra.
- Si el dato es demo, mostrar “Demo” y no mezclarlo con datos reales.
- La evaluación inmediata y la diferida se etiquetan distinto; no se mezclan con práctica formativa.

### 10.3 Gráfico de retención

```
Precisión observada por semana
100 ┤
 75 ┤      ●──●
 50 ┤  ●──╯
 25 ┤
  0 └────────────────
     S1  S2  S3  S4
     n=12  n=18  n=15  n=20
```

- Línea observada: sólida.
- Proyección: discontinua, con banda de incertidumbre si existe.
- No conectar puntos sin datos.
- No mostrar una tendencia si `n < 3`; mostrar “Aún no hay suficientes datos”.

---

## 11. Diferenciación estudiante / docente

| Dimensión | Estudiante | Docente |
|---|---|---|
| **Objetivo** | Saber qué hacer hoy | Decidir dónde intervenir |
| **Tono** | “Tu estado de hoy”, “Un repaso corto” | “Sección 5.° A”, “Evidencia observada” |
| **Densidad** | Aire, una acción, 16 px | Comparación, filtros, 14 px mínimo |
| **Métricas** | 2–3 KPI, lenguaje narrativo | Tablas, distribución, `n`, fecha |
| **Navegación** | Inicio, cursos, repasos, progreso | Panel, cursos, actividades, banco, estudiantes, reportes |
| **Estados del sistema** | No visible o resumen simple | Vista técnica disponible |
| **Color** | Brand + menta | Brand + ámbar/verde para estados |
| **Acciones** | “Comenzar repaso”, “Ver mi progreso” | “Revisar”, “Asignar”, “Exportar” |
| **Error** | “No pudimos cargar. Reintenta.” | “No pudimos cargar la nómina. Reintenta o revisa el servicio.” |

La diferenciación no debe depender solo del color. Se refuerza con el título, el menú, el copy y la densidad.

---

## 12. Movimiento

- Transiciones de 150–200 ms, `ease-out`.
- Sin animaciones infinitas en el producto.
- La animación orbital del login es opcional y se desactiva con `prefers-reduced-motion`.
- Los cambios de estado (guardar, publicar) usan un check breve, no confeti.
- No animar tablas ni listas largas.
- Respetar `prefers-reduced-motion` en todos los componentes.

---

## 13. Accesibilidad objetivo

| Compromiso | Criterio |
|---|---|
| Contraste | AA en todo texto normal; AAA en texto principal si es viable |
| Tamaño de texto | ≥ 12 px; cuerpo ≥ 14 px; estudiante ≥ 16 px |
| Objetivos táctiles | ≥ 44 × 44 px en acciones |
| Foco | Anillo visible en todos los interactivos |
| Teclado | Todos los flujos completables sin ratón |
| Formularios | Label, ayuda y error asociados |
| Modales | Diálogo, foco atrapado, Escape, retorno |
| Tablas | `caption`, `scope`, alternativa móvil |
| Gráficos | `figure`, resumen, tabla de datos |
| Movimiento | `prefers-reduced-motion` |
| Mensajes | `aria-live` para toasts |
| Navegación | Skip link, `aria-current`, landmarks |

**Pruebas mínimas:** `axe` en las 10 pantallas principales, Tab en login/dashboard/quiz/preguntas/reportes, y una prueba con NVDA o VoiceOver.

---

## 14. Voz y contenido

### 14.1 Principios de copy

- Segunda persona, “tú”.
- Frases cortas.
- Verbo concreto: “Revisa”, “Comienza”, “Consulta”.
- Sin alarmismo.
- Sin promesas de certeza.
- Sin jerga técnica en la UI del estudiante.

### 14.2 Ejemplos

| Situación | Antes | Después |
|---|---|---|
| Sin datos | “12 actividades completadas” (ficticio) | “Aún no hay actividad registrada. Completa una práctica para empezar.” |
| Retención | “Retención Óptima” | “Sin datos suficientes para estimar tu retención.” |
| Recomendación | “Refuerzo de Fotosíntesis” (sin datos) | “Aún no tienes un refuerzo asignado. Explora tus cursos.” |
| Error | “Failed to fetch” | “No pudimos cargar el contenido. Reintenta en unos segundos.” |
| Docente sin datos | “10 estudiantes, 69.2 %” (ficticio) | “Aún no hay estudiantes en esta sección.” |
| Insight | “La precisión disminuyó 12 %” (ficticio) | “Insight no disponible: se necesitan al menos N eventos.” |
| Demo | Datos demo sin aviso | “Datos de demostración. No corresponden a tu actividad.” |

### 14.3 Glosario

| Término | Uso |
|---|---|
| Estudiante | Persona que aprende; no “alumno” en la UI |
| Docente | Persona que enseña; no “profesor” salvo copy institucional |
| Curso | Asignatura/sección |
| Componente de conocimiento (KC) | Unidad evaluable |
| Precisión observada | Aciertos / respuestas |
| Retención estimada | Probabilidad del modelo |
| Por consolidar | Estado pedagógico, no “en riesgo” |
| Refuerzo sugerido | Acción recomendada |
| Sin datos suficientes | Estado honesto |

---

## 15. Wireframes de referencia

### 15.1 Dashboard del estudiante

```
┌────────────────────────────────────────────────────────────┐
│ SÁBADO, 7 DE NOVIEMBRE                                      │
│ Hola, Lucía                                                 │
│ Tu estado de hoy                                            │
│                                                            │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 2 conceptos por consolidar · 1 repaso sugerido         │ │
│ │ [Comenzar repaso · 8 min]                              │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                            │
│ Precisión observada    Conceptos consolidados   Tiempo     │
│ 69.4 %                 3 de 5                   45 min     │
│ n=36 · 7 nov           Observado                esta sem.  │
│                                                            │
│ Próximo repaso                          Mis cursos         │
│ [tarjeta o vacío honesto]               [tarjeta o vacío]  │
│                                                            │
│ Datos al 7 nov 2026 · Fuente: actividad formativa          │
└────────────────────────────────────────────────────────────┘
```

### 15.2 Panel del docente

```
┌────────────────────────────────────────────────────────────┐
│ PANEL DOCENTE · 5.° A                 [Todas las secciones]│
│ Bienvenida, Ana                                             │
│ Estado de la sección                                        │
│                                                            │
│ 10 estudiantes    69.2 % observado    10 repasos           │
│ n=360 · 7 nov     [Observado]         completados          │
│                                                            │
│ Distribución                                                │
│ ██████████ 3 consolidados · 5 en proceso · 2 por consolidar│
│                                                            │
│ Necesitan refuerzo                                          │
│ [Mateo · 47.2 % · Respiración celular]                     │
│ [Camila · 52.8 % · Herencia mendeliana]                    │
│                                                            │
│ Insight: sin evidencia suficiente para generar una          │
│ recomendación automática. Revisa la nómina.                 │
└────────────────────────────────────────────────────────────┘
```

### 15.3 Login móvil

```
┌──────────────────────┐
│ [Nexo]   5.° SEC.    │
│ [Iniciar sesión] [Conoce Nexo] │
│                      │
│ Ingresa a tu espacio │
│ Elige tu perfil      │
│ ┌────────┐ ┌────────┐│
│ │Estudiante│ │Docente ││
│ │Aprende  │ │Gestiona││
│ └────────┘ └────────┘│
│                      │
│ Correo institucional │
│ [__________________] │
│ Contraseña           │
│ [__________________] │
│ [Ingresar]           │
│                      │
│ ¿Cómo funciona?      │
│ Ver presentación →   │
└──────────────────────┘
```

---

## 16. Alternativas consideradas

| Alternativa | Por qué se consideró | Por qué no se elige |
|---|---|---|
| **Gamificación con rachas, XP y rankings** | Aumenta engagement a corto plazo | Contradice el enfoque de autorregulación; puede aumentar ansiedad; los estudiantes de 16–17 no necesitan infantilización; distrae de la evidencia. |
| **Tema espacial completo** | El login orbital ya existe y llama la atención | La metáfora no escala al producto; distrae; las animaciones infinitas afectan accesibilidad. Se conserva solo como momento de marca. |
| **Dashboard oscuro para docente** | Se ve “analítico” | Reduce legibilidad de tablas densas; no es una necesidad; se puede explorar como tema opcional futuro. |
| **Paleta gris + un solo acento** | Máxima neutralidad | Pierde la identidad y la calidez; el verde azulado actual funciona. |
| **Rediseño completo desde cero** | Elimina deuda | Costoso y arriesgado; la base es rescatable; el problema principal son los datos y los componentes, no la marca. |
| **Más gráficos y animaciones** | Percepción de modernidad | Aumenta carga cognitiva y barreras; el problema es la claridad, no la espectacularidad. |

---

## 17. Implementación

### 17.1 Archivos base

| Archivo | Cambio propuesto |
|---|---|
| `src/app/globals.css` | Tokens semánticos, tipografía, foco global, reduced motion |
| `tailwind.config.ts` | Mapear tokens a colores/radios/sombras |
| `src/app/layout.tsx` | Cargar Inter con `next/font`, metadata |
| `src/components/ui/button.tsx` | Tamaños 44 px, estados, focus |
| `src/components/ui/card.tsx` | `CardTitle` configurable, radios |
| `src/components/ui/field.tsx` | Nuevo: label + help + error |
| `src/components/ui/modal.tsx` | Nuevo: diálogo accesible |
| `src/components/ui/empty-state.tsx` | Nuevo |
| `src/components/ui/error-state.tsx` | Nuevo |
| `src/components/ui/data-table.tsx` | Nuevo |
| `src/components/ui/chart-frame.tsx` | Nuevo |
| `src/components/ui/toast.tsx` | Nuevo |
| `src/app/error.tsx` | Nuevo: boundary global |

### 17.2 Orden de migración

1. Tokens y tipografía.
2. Botón, campo, tarjeta y badge.
3. Modal, toast, estados vacío/error.
4. Tabla y gráfico.
5. Migración de pantallas: login → dashboard estudiante → cursos → quiz → progreso → docente.
6. Barrido de hex y tamaños pequeños.
7. Pruebas de accesibilidad y responsive.

### 17.3 Reglas de código

- Prohibido hex de marca en páginas; solo tokens.
- Prohibido `text-[10px]` y `text-[11px]` en texto de UI.
- Todo campo debe usar `Field`.
- Todo modal debe usar `Modal`.
- Toda tabla debe usar `DataTable`.
- Todo gráfico debe usar `ChartFrame`.
- Todo dato debe pasar por un tipo con `provenance` (`observed | estimated | demo | unavailable`) y `sample_size`.
- Todo texto de asignatura debe venir de datos, no de literales.

### 17.4 QA visual

- 390 px, 768 px, 1440 px.
- Zoom 200 %.
- Teclado solamente.
- `prefers-reduced-motion` activado.
- Contraste con herramienta (Stark, axe, Lighthouse).
- Revisión de las 18 rutas.

---

## 18. Criterios de éxito de la dirección

La dirección se considera bien implementada cuando:

1. Un estudiante puede explicar qué mide cada número de su dashboard y de dónde sale.
2. Un docente puede comparar la nómina, el dashboard y los reportes y obtiene los mismos conteos.
3. Ninguna pantalla muestra datos demo sin un aviso visible.
4. Ningún texto de UI baja de 12 px.
5. Todos los formularios se completan con teclado y lector de pantalla.
6. Todos los modales se cierran con Escape y devuelven el foco.
7. Todos los gráficos tienen una alternativa textual.
8. El login móvil no trunca roles ni superpone ayuda.
9. La plataforma puede renderizar un curso que no sea Ciencias sin textos de Ciencias.
10. El equipo puede cambiar un color o un radio en un token y ver el cambio en toda la app.

---

## 19. Resumen en una frase

**Mantener la calma visual del verde azulado, pero ponerla al servicio de una promesa simple: mostrar solo lo que se puede sostener con evidencia, explicar lo que no se sabe y permitir que cualquier estudiante o docente lo entienda y lo use sin barreras.**
