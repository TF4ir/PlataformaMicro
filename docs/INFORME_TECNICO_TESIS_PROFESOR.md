# Informe Técnico y Pedagógico del MVP — Plataforma de Microaprendizaje Adaptativo (Nexo)

> **Documento de Sustentación para Revisión Docente / Asesoría de Tesis**  
> **Proyecto:** Nexo — Plataforma de Microaprendizaje Adaptativo con Modelado Temporal de Retención  
> **Población Objetivo:** Estudiantes de 5.° año de secundaria (16–17 años) — Educación Básica Regular (Perú)  
> **Materia Piloto:** Ciencias (Arquitectura agnóstica a la disciplina curricular)  
> **Marco Normativo y Ético:** Ley N.° 29733 (Protección de Datos Personales de Menores)  
> **Fecha de Actualización:** Noviembre 2026  
> **Versión del Sistema:** MVP Funcional (Fase M5.4)

---

## 1. Solución Tecnológica y su Relación con el Problema de Investigación

### 1.1 El Problema Científico y Educativo
En la educación secundaria tradicional, la retención de conceptos con alta densidad abstracta (como los fenómenos biológicos y fisicoquímicos en Ciencias) se ve fuertemente degradada por la **dinámica natural del olvido**. De acuerdo con la formalización clásica de Hermann Ebbinghaus ($R = e^{-\frac{t}{S}}$, donde $R$ es la probabilidad de recuperación, $t$ el tiempo transcurrido y $S$ la fuerza mnemónica del trazo de memoria), los estudiantes pierden más del 60 % de la información aprendida dentro de los primeros 7 días posteriores a una sesión expositiva si no median intervenciones de reactivación oportunas.

Las prácticas habituales de estudio en secundaria sufren de dos fallas estructurales:
1. **Práctica Masiva y Tardía (*Cramming*):** Los estudiantes concentran el repaso la noche previa a una evaluación sumativa, logrando una retención efímera a corto plazo con nula consolidación a largo plazo.
2. **Falta de Adaptatividad al Nivel del Componente de Conocimiento (KC):** Las tareas y repasos asignados por los docentes son uniformes para todo el salón de clases, ignorando que cada alumno posee una tasa de degradación mnemónica diferenciada por cada concepto específico (*Knowledge Component*).

### 1.2 La Solución Tecnológica Desarrollada: Plataforma Nexo
**Nexo** es un sistema web de microaprendizaje adaptativo diseñado para modelar la dinámica de adquisición y olvido de cada estudiante a nivel de microcomponentes de conocimiento, programando repasos formativos oportunos mediante microcontenidos interactivos (de 3 a 5 minutos) y reactivos formativos dosificados.

La relación directa con la investigación de tesis se fundamenta en tres pilares:
- **Modelado Cognitivo por Componente de Conocimiento (KC):** En lugar de evaluar la "asignatura general", el sistema desagrega el currículo en unidades mínimas de significado (p. ej., *Fotosíntesis*, *Respiración celular*, *Estructura celular*, *Herencia mendeliana*, *Ciclos biogeoquímicos*). Cada interacción alimenta un vector temporal de desempeño.
- **Intervenciones de Repaso Espaciado Adaptativo:** Un motor de políticas pedagógicas calcula cuándo la probabilidad estimada de recuerdo decae hacia una zona de intervención óptima ($\tau \approx 0.65$), momento en el cual el esfuerzo cognitivo de recuperación maximiza la plasticidad mnemónica sin generar frustración por olvido irreversible.
- **Arquitectura Agnóstica y Desacoplada:** El modelo de datos, la API REST y las interfaces web son 100 % independientes de la materia escolar. La lógica no contiene referencias rígidas a "Ciencias", permitiendo que la misma solución tecnológica escale a Matemáticas, Historia, Comunicación o cualquier dominio escolar.

### 1.3 Formulación de Hipótesis de Tesis
- **Hipótesis Nula ($H_0$):** No existe diferencia estadísticamente significativa en el puntaje de la prueba diferida a 7 días ($h = 168$ horas) entre los estudiantes que reciben repasos adaptativos dosificados por modelado temporal y aquellos que reciben prácticas tradicionales lineales no adaptativas ($p \ge 0.05$).
- **Hipótesis Alternativa ($H_1$):** Los estudiantes que reciben repasos adaptativos dosificados por modelado temporal alcanzan un puntaje estadísticamente significativo mayor en la prueba diferida a 7 días que el grupo control ($p < 0.05$), con un tamaño de efecto estandarizado (d de Cohen) $\ge 0.40$.

---

## 2. Funcionalidades Principales Justificadas Técnica y Pedagógicamente

| # | Funcionalidad | Justificación Técnica | Justificación Pedagógica y Científica |
|---|---|---|---|
| **F-01** | **Microaprendizaje Dosificado (3–5 min)** | Entrega de microcontenidos modulares estructurados en formato JSON tipado (`content_schema_version`), consumidos vía endpoints optimizados. | Mitigación de la Sobrecarga Cognitiva (Teoría de John Sweller). La memoria de trabajo de adolescentes retiene mejor unidades atómicas enfocadas en un solo KC antes de pasar a la práctica. |
| **F-02** | **Telemetría de Respuestas Inmutable (`answer_events`)** | Almacenamiento PostgreSQL en modo *Append-Only*. Denegación estricta de sentencias `UPDATE` y `DELETE` mediante triggers nativos a nivel de motor. | Integridad científica del dataset experimental. Garantiza que las marcas de tiempo ($t$), latencias y respuestas observadas sean auditables sin riesgo de alteración retrospectiva. |
| **F-03** | **Eventos de Exposición a Contenido (`content_exposure_events`)** | Registro inmutable de apertura, tiempo de lectura activa (`dwell_time_seconds`) y completitud de microcontenidos antes de resolver quizzes. | Aislamiento entre la fase de estudio (*study phase*) y la fase de prueba (*testing phase*), permitiendo al modelo aislar el efecto de la lectura del efecto del testeo formativo. |
| **F-04** | **Motor de Adaptación Pedagógica y Fallback Determinista** | Servicio de recomendación con arquitectura de dos etapas: (1) Inferencia predictiva temporal y (2) Fallback basado en reglas explícitas para arranque en frío (*cold-start*). | Principio de no-interrupción escolar: si el estudiante tiene menos de 3 respuestas previas en un KC o la API de inferencia tiene latencia, el sistema jamás se congela; asigna refuerzo guiado por reglas pedagógicas auditables. |
| **F-05** | **Control Anti-Fatiga y Capping de Frecuencia** | Límite algorítmico configurable en el motor adaptativo: máximo 2 micro-repasos pendientes simultáneos por estudiante y enfriamiento temporal de 24 horas. | Prevención del agotamiento académico (*burnout* escolar). El microaprendizaje no debe saturar la jornada del estudiante con una avalancha de repasos pendientes. |
| **F-06** | **Disociación Criptográfica de Identidad (`student_id_pseudo`)** | Separación entre la tabla `profiles` (que aloja datos de matrícula institucional) y `enrollments.student_id_pseudo` (UUID criptográfico derivado). | Cumplimiento mandatorio de la **Ley N.° 29733** (Perú) para protección de datos personales de menores de edad (16–17 años). Los datasets de tesis y telemetría analítica jamás contienen nombres ni correos reales. |
| **F-07** | **Cuarentena Inmutable de Evaluación a 7 Días (`delayed_assessment`)** | Filtro restrictivo a nivel de repositorio y base de datos: `WHERE activity_type != 'delayed_assessment'`. | Blindaje metodológico contra el *Testing Effect Leakage*. Los reactivos que medirán la retención en la prueba diferida de tesis tienen prohibición absoluta de ser seleccionados para repasos formativos. |
| **F-08** | **Panel de Monitoreo Docente y Heatmap de Retención** | Agregaciones SQL sobre eventos reales observados (sin interpolaciones algorítmicas inventadas), renderizadas con componentes React + Tailwind + Recharts. | Soporte a la docencia formativa (*Teacher Telemetry*). Permite al profesor identificar en tiempo real qué conceptos presentan mayor fragilidad colectiva para reorientar su clase presencial. |

---

## 3. Prototipo / MVP Demostrable

### 3.1 Arquitectura del Sistema Desplegado
El MVP sigue una arquitectura desacoplada y orientada a servicios, optimizada para responder con baja latencia y alta seguridad:

```text
┌─────────────────────────────────────────────────────────────┐
│                 Navegador Web (Estudiante / Docente)        │
│        Next.js 14.2 (App Router) + Tailwind CSS + Lucide     │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTPS / Bearer Token ES256
                               ▼
┌─────────────────────────────────────────────────────────────┐
│       Frontend Edge: Cloudflare Workers (OpenNext)          │
│         - Despliegue global en red distribuida Edge         │
│         - Renderizado reactivo y Server Components          │
│         - Validación de formularios con Zod & React Hook Form│
└──────────────┬──────────────────────────────┬───────────────┘
               │                              │
               │ REST / JSON (JWT ES256)      │ REST / Supabase SSR Client
               ▼                              ▼
┌──────────────────────────────┐ ┌────────────────────────────┐
│   Backend de Inferencia &    │ │    Persistencia & Auth     │
│   Adaptación (FastAPI/Py)    │ │   (Supabase / PostgreSQL)  │
│  - FastAPI en Python 3.11+   │ │  - 26 Tablas relacionales  │
│  - Validación Pydantic v2    │ │  - Row Level Security (RLS)│
│  - Verificación JWKS / ES256 │ │  - GoTrue Auth (ES256)     │
│  - Políticas de adaptación   │ │  - Triggers de inmutabilidad│
└──────────────┬───────────────┘ └────────────┬───────────────┘
               │                              │
               └───────────────┬──────────────┘
                               │ asyncpg (Connection Pool)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│       PostgreSQL 15+ (Nube Supabase - oqjahhbqcethwgpufgnm) │
│           Dataset sintético de demostración cargado         │
└─────────────────────────────────────────────────────────────┘
```

### 3.2 Evidencia del Entorno de Persistencia
La base de datos en producción cuenta con **26 tablas relacionales** bajo políticas RLS activas, habiendo aplicado las 8 migraciones acumulativas del repositorio:
1. `tenants`, `profiles`, `auth_recovery_pins`
2. `courses`, `sections`, `enrollments`, `units`
3. `knowledge_components`, `microcontents`, `questions`, `question_options`
4. `activities`, `activity_sections`, `activity_questions`, `quiz_attempts`, `answer_events`
5. `student_knowledge_states`, `student_metrics`, `model_versions`, `predictions`
6. `recommendations`, `review_assignments`, `content_exposure_events`
7. `content_generation_jobs`, `question_drafts`, `notifications`

### 3.3 Dataset Sintético de Demostración Operativo
Para validar todos los flujos sin depender de la recolección presencial de campo (que corresponde al experimento final), se cargó un dataset sintético, determinista y reproducible:

- **1 Institución Educativa:** Colegio Piloto San Agustín.
- **1 Docente Titular:** Lic. Ana García.
- **10 Estudiantes:** Lucía Mendoza (`EST-501`) + 9 estudiantes con códigos seudónimos (`EST-502` a `EST-510`).
- **1 Curso y Sección:** Ciencias — 5.° Secundaria, Sección "A".
- **5 Knowledge Components (KCs):**
  1. *Fotosíntesis* (Reacciones lumínicas y ciclo de Calvin).
  2. *Respiración celular* (Glucólisis, ciclo de Krebs y fosforilación oxidativa).
  3. *Estructura y función celular* (Organelos, membrana y transporte).
  4. *Herencia mendeliana* (Leyes de Mendel, cuadros de Punnett).
  5. *Ciclos biogeoquímicos* (Ciclos del carbono, nitrógeno y fósforo).
- **5 Microcontenidos publicados:** Estructurados con diagramas y conceptos clave.
- **15 Preguntas canónicas:** 3 por cada KC, con 4 alternativas y explicaciones formativas.
- **5 Actividades asignadas:** Prácticas formativas vinculadas curricularmente.
- **120 Intentos de cuestionario (`quiz_attempts`):** Distribuidos en un horizonte de 6 semanas de actividad simulada.
- **360 Respuestas inmutables (`answer_events`):** Registros con aciertos/errores reales observados.
- **60 Eventos de exposición (`content_exposure_events`):** Lectura activa previa a las evaluaciones.
- **30 Recomendaciones generadas:** 20 pendientes de repaso prioritario y 10 completadas por los estudiantes.

### 3.4 Credenciales para Demostración

| Rol | Correo Electrónico | Contraseña | Perfil y Acceso |
|---|---|---|---|
| **Docente** | `ana.garcia@nexo.edu.pe` | `Nexo2026!` | Acceso completo al panel `/teacher/*`, directorio de estudiantes, heatmap de KCs y reportes semanales observados. |
| **Estudiante** | `lucia.mendoza@nexo.edu.pe` | `Nexo2026!` | Acceso al panel `/dashboard`, microlecciones `/learn/[id]`, cuestionarios `/quiz/[id]` y progreso `/progress`. |
| **Estudiante Secundario** | `estudiante.502@nexo.edu.pe` … `.510` | `Nexo2026!` | Cuentas seudonimizadas para comprobar la variabilidad en el heatmap docente. |

---

## 4. Flujos de Interacción y Experiencia de Usuario (UX/UI)

### 4.1 Flujo del Estudiante (Ciclo de Microaprendizaje y Repaso)

```text
[1. Inicio de Sesión]
       │  Autenticación Supabase Auth -> Emisión de JWT ES256
       ▼
[2. Dashboard Principal (/dashboard)]
       │  Hero con Repaso Prioritario sugerido según la política adaptativa
       │  Visualización de precisión observada y unidades curriculares
       ▼
[3. Microlección (/learn/[id])]
       │  Lectura activa de 3 a 5 minutos (Diagrama conceptual interactivo)
       │  Registro inmutable en content_exposure_events (dwell time)
       ▼
[4. Cuestionario Formativo (/quiz/[id])]
       │  3 a 5 preguntas de opción múltiple del KC en estudio
       │  Registro inmediato e inmutable en answer_events
       ▼
[5. Retroalimentación Inmediata (/quiz/[id]/results)]
       │  Explicación pedagógica de aciertos y errores (sin penalización)
       │  Recálculo automático del estado de dominio en student_knowledge_states
       ▼
[6. Monitoreo de Progreso (/progress)]
       └─ Vista transparente de precisión por concepto y lista de repasos sugeridos
```

### 4.2 Flujo del Docente (Telemetría de Aula e Intervención)

```text
[1. Inicio de Sesión Docente]
       │  Validación de rol 'teacher' mediante RLS y claims de Supabase
       ▼
[2. Dashboard Docente (/teacher/dashboard)]
       │  KPIs de consolidación de sección (ej. 10 alumnos, 120 cuestionarios)
       │  Alerta de estudiantes que requieren refuerzo prioritario
       ▼
[3. Reportes Analíticos (/teacher/reports)]
       │  Heatmap de Dominio: Matriz de 10 estudiantes × 5 KCs
       │  Trayectoria Semanal Observada: Gráfico histórico basado en eventos reales
       ▼
[4. Directorio de Alumnos (/teacher/students)]
       │  Roster con nivel de actividad reciente y tasa de acierto observada
       ▼
[5. Banco Curricular (/teacher/courses, /teacher/questions)]
       └─ Inspección de microcontenidos, unidades y reactivos publicados
```

### 4.3 Principios de Diseño UX y Lenguaje Empático
1. **Ergonomía Cognitiva:** La interfaz minimiza el ruido visual, empleando tarjetas limpias, tipografía legible y jerarquía de contrastes que cumple los estándares **WCAG 2.1 nivel AA**.
2. **Lenguaje Empático y Constructivo:** En cumplimiento de las directrices del proyecto, la plataforma **prohíbe estrictamente el lenguaje punitivo o de déficit**. No se muestran advertencias como *"Estás a punto de desaprobar"* o *"Riesgo alto de olvido"*. En su lugar, el sistema emplea frases pedagógicas como:
   - *"Momento ideal para repasar este concepto."*
   - *"Concepto por consolidar."*
   - *"Refuerzo sugerido para asegurar tu aprendizaje a largo plazo."*
3. **Resiliencia ante Fallos:** La interfaz implementa componentes de carga con esqueletos (*skeleton loaders*) y gestión elegante de errores, garantizando que una desconexión o demora en el backend predictivo degrade ordenadamente a la política de reglas sin bloquear la pantalla del estudiante.

---

## 5. Validación Experimental, Criterios de Utilidad y Rigor Científico

### 5.1 Criterios de Utilidad del Software Desarrollado
Para asegurar la viabilidad técnica en un entorno escolar real en el Perú, el sistema fue evaluado contra los siguientes criterios de calidad de software:

1. **Aislamiento Multitenant con RLS:** Las pruebas automatizadas verifican que un estudiante jamás puede consultar datos de otro estudiante (`auth.uid() = student_id`), y que un docente solo visualiza las secciones formalmente asignadas.
2. **Resiliencia ante Cold-Start:** El servicio backend FastAPI implementa un endpoint de calentamiento (`/warmup`) y políticas no bloqueantes, mitigando las latencias de arranque en frío típicas de la infraestructura en la nube sin degradar la experiencia de usuario.
3. **Idempotencia en Registro de Respuestas:** El endpoint de envío de cuestionarios valida claves de idempotencia (`idempotency_key`), previniendo registros duplicados por doble clic o intermitencias en la red escolar.
4. **Verificación Automatizada de Código:** La suite de pruebas de integración y contratos alcanza **245 pruebas superadas exitosamente** (`245 passed`), con 100 % de cumplimiento de tipos en TypeScript (`tsc --noEmit`) y compilación exitosa en Next.js.

### 5.2 Metodología Cuasiexperimental de Validación Pedagógica
La comprobación empírica de la tesis se estructura mediante un diseño cuasiexperimental con grupos intactos:

- **Población:** 2 secciones de 5.° año de secundaria del colegio piloto ($N \approx 66$ estudiantes).
  - **Grupo Experimental ($n_e \approx 33$):** Utiliza la plataforma con recomendaciones adaptativas de repaso espaciado disparadas automáticamente según el modelado de retención.
  - **Grupo Control ($n_c \approx 33$):** Utiliza la plataforma con el mismo contenido curricular y preguntas, pero recibe repasos asignados de manera lineal y estática (sin adaptación temporal).
- **Cronograma Experimental:**
  1. *Día 1:* Pre-test diagnóstico para establecer la línea base de conocimiento en ambos grupos.
  2. *Días 2 al 4:* Intervención pedagógica con microcontenidos. El grupo experimental recibe micro-repasos adaptativos oportunos.
  3. *Día 5:* Post-test inmediato ($h = 0$ horas).
  4. *Días 5 al 11:* **Periodo de Cuarentena (168 horas / 7 días):** Prohibición absoluta de reactivos vinculados al instrumento de medición diferida.
  5. *Día 12:* **Post-test Diferido ($h = 168$ horas):** Medición de la retención a largo plazo. Es el instrumento principal para la contrastación de la hipótesis alternativa $H_1$ mediante pruebas $t$ de Student para muestras independientes o pruebas $U$ de Mann-Whitney.

### 5.3 Marco de Modelado Predictivo (Fase Posterior de la Tesis)
La plataforma se encuentra completamente instrumentada para conectar el modelo predictivo formal:
- **Candidato Principal:** **DAS3H** (*Difficulty, Ability, Student, Student-Skill, Recency/Frequency* a través de ventanas temporales logarítmicas), modelando la probabilidad de recuerdo $P(R=1)$ considerando la práctica distribuida en el tiempo.
- **Baselines de Comparación:** Regresión logística temporal extendida (**PFA**) y Redes Bayesianas de Rastreo de Conocimiento (**BKT modificado**).
- **Métricas de Evaluación Científica:**
  - *Capacidad Discriminativa:* AUC-ROC ($\ge 0.75$).
  - *Calibración Probabilística:* Brier Score ($\le 0.15$) y Expected Calibration Error (ECE $\le 0.08$), analizados mediante reliability diagrams para garantizar que un 70 % de probabilidad estimada equivalga exactamente a un 70 % de retención empírica.
  - *Prevención de Fuga de Datos (*Data Leakage*):* Validación cruzada agrupada por estudiante (*Student Group-K-Fold*), impidiendo que interacciones del mismo alumno se compartan entre entrenamiento y prueba.

### 5.4 Declaración de Integridad Científica y Estado Real del Proyecto
Con total apego a la ética científica y la transparencia académica:

1. **Estado Actual Implementado:** El MVP funcional presentado demuestra la operatividad de punta a punta de la arquitectura de software, el registro inmutable de telemetría, el catálogo curricular, las guardas de seguridad RLS y el motor de adaptación por reglas deterministas (`rule_based_fallback`).
2. **Delimitación Honesta:** Las curvas y datos observados en el MVP provienen de una simulación sintética estadísticamente controlada para validar la navegación y la robustez del sistema. **No se presentan como resultados empíricos definitivos de aprendizaje escolar real ni como métricas de un modelo de Machine Learning ya entrenado.**
3. **Fase Inmediata Siguiente:** La recolección de telemetría de campo durante la prueba piloto escolar alimentará el dataset real para el entrenamiento masivo, congelamiento con `metadata.json` y calibración estadística rigurosa de los modelos predictivos definitivos.
