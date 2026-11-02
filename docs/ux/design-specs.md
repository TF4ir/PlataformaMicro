# Especificaciones de Diseño UI/UX — Plataforma Nexo

## 1. Identidad Visual y Estilo
- **Nombre:** Nexo (*Aprende a tu ritmo*)
- **Paleta de Color:**
  - Sidebar: `#092624` (Dark Teal profundo)
  - Interacciones / Botones: `#0f766e` / `#0d9488` (Teal esmeralda)
  - Notificaciones y refuerzo positivo: `#f5f3ff` (Lavanda suave con borde `#ede9fe` y texto `#6d28d9`)
  - Fondos generales: `#f8fafc` (Slate 50)
- **Tipografía:** Inter (sans-serif), alta legibilidad para estudiantes de secundaria (16-17 años).

## 2. Mapa de Rutas e Interfaces Implementadas

| Pantalla | Ruta | Captura Referencial | Componentes Principales |
|---|---|---|---|
| **Dashboard Estudiante (Hero)** | `/dashboard` | `01-estudiante-inicio-hero.png` | Saludo personalizado, Tarjeta Hero Adaptativa, CTA con icono |
| **Dashboard Estudiante (Métricas)** | `/dashboard` | `02-estudiante-inicio-panorama.png` | Tu panorama (3 KPIs), Widget de curso Ciencias, Próximos repasos con prioridad |
| **Mis Cursos** | `/courses` | `03-estudiante-mis-cursos.png` | Pestañas (Todos, En curso, Completados), Tarjeta de Ciencias Naturales, Tarjeta adaptativa |
| **Pre-inicio de Actividad** | `/recommendations/[id]` | `04-estudiante-recomendacion-preactividad.png` | Ilustración botánica SVG, Caja empática, Desglose de 2 fases, Botón de inicio |
| **Microlección (Proceso)** | `/learn/[id]` | `05-estudiante-microleccion-proceso.png` | Stepper lateral de 4 pasos, Barra de progreso superior, Diagrama botánico interactivo |
| **Microlección (Resumen)** | `/learn/[id]` | `06-estudiante-microleccion-resumen.png` | Ecuación química balanceada, Analogía de panel solar, 3 tarjetas "Qué debes recordar" |
| **Cuestionario Adaptativo** | `/quiz/[id]` | `07-estudiante-cuestionario-pregunta.png` | Modo inmersivo, Pregunta única, Opciones A/B/C/D interactivas, Comprobar respuesta |
| **Feedback Inmediato** | `/quiz/[id]/results` | `08-estudiante-cuestionario-feedback.png` | Checkmark de éxito, Justificación pedagógica, Resumen 3/3, Estado "En consolidación" |
| **Mi Progreso y Analítica** | `/progress` | `09-estudiante-mi-progreso.png` | 4 KPIs, Gráfico de área temporal (Recharts), Gráfico de anillo, Historial de repasos |
| **Gestión de Cursos Docente** | `/teacher/courses` | `10-docente-gestion-cursos.png` | Botón "+ Nuevo curso", Buscador y filtro, Tabla de cursos, secciones y estados |
| **Panel Resumen Docente** | `/teacher/dashboard` | N/A | Métricas de sección (5.° A, B, C), Precisión agregada, Gestión de componentes |
| **Telemetría y Estados** | `/system-status` | N/A | Monitor de cold-start (blitz.cloud), Latencia de inferencia, RLS y Ley N° 29733 |
