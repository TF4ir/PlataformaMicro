# Arquitectura del Sistema: Visión General y Topología

## 1. Identidad y Misión del Sistema

La **Plataforma de Microaprendizaje Adaptativo** es un sistema web diseñado para estudiantes de 5to año de educación secundaria (16-17 años). Su objetivo fundamental es modelar la retención y la dinámica de olvido cognitivo por Componentes de Conocimiento (*Knowledge Components* - KC), permitiendo programar actividades de micro-repaso formativo (3-5 minutos) personalizadas para mitigar el decaimiento de la memoria a largo plazo.

### Principio de Diseño Agnóstico
El diseño pedagógico y la persistencia de datos son estrictamente independientes del dominio temático. Aunque la asignatura piloto inicial es **Ciencias**, el modelo relacional, las políticas predictivas y la API no contienen referencias rígidas ni acoplamientos semánticos al curso escolar.

---

## 2. Topología del Sistema y Separación de Responsabilidades

El sistema adopta una **arquitectura desacoplada de cuatro niveles**, dividiendo estrictamente la presentación de usuario, la persistencia declarativa con seguridad a nivel de fila (RLS), la inferencia temporal adaptativa y la experimentación científica.

```text
+-----------------------------------------------------------------------------------+
|                                 CLIENTES WEB                                      |
|  [ Estudiante (Mobile/Desktop) ]              [ Docente / Investigador ]          |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼ HTTPS / WSS
+-----------------------------------------------------------------------------------+
|                              APPS / WEB (Next.js 15)                              |
|  - Next.js App Router (Server Components & Server Actions)                        |
|  - Tailwind CSS + shadcn/ui (Diseño pedagógico empático)                         |
|  - Zod Schemas & React Hook Form                                                  |
|  - Supabase SSR Client (Auth session & Token forwarder)                           |
|  - Fallback determinista local en caso de timeout predictivo (>5s)                |
+---------------------------------------┬-------------------------------------------+
                     │                  │
         HTTPS / RLS │                  │ HTTPS / JWT + Idempotency
                     ▼                  ▼
+---------------------------------+  +----------------------------------------------+
|     SUPABASE (BaaS Platform)     |  |          SERVICES / ML-API (FastAPI)         |
|  - Supabase Auth (GoTrue)       |  |  - Security Middleware (JWKS verification)    |
|  - PostgreSQL 15+ (Single Truth)|  |  - Prediction Controller (/api/v1/ml/*)      |
|  - Row Level Security (RLS)     |  |  - Recommendation Engine (Adaptation Policy) |
|  - Storage (Microcontents CDN)  |  |  - Feature Builder (Temporal Windowing)      |
|  - Append-only Event Store      |  |  - Model Runtime (DAS3H / BKT / Baselines)   |
+---------------------------------+  +----------------------------------------------+
                     ▲                                      │
                     │                                      │
                     └──────── SQLAlchemy (Asyncpg) ────────┘
                                (Inferencia y consultas read-heavy)
                                         ▲
                                         │ Artefactos congelados (.joblib + metadata)
                                         │
                              +----------------------+
                              |      ML / PIPELINE   |
                              |  - Training & EDA    |
                              |  - Offline Validation|
                              |  - Artifact Registry |
                              +----------------------+
```

### Componentes Principales:
1. **Frontend (`apps/web/`):**
   - Construido con Next.js (App Router), React y TypeScript. Desplegado en Vercel.
   - El cliente web consume datos de Supabase vía Server Actions y efectúa peticiones de inferencia o adaptación a `services/ml-api/`.
   - **Frontera Estricta:** Jamás ejecuta algoritmos predictivos, jamás accede a archivos `.joblib` ni toma decisiones de política pedagógica por cuenta propia.
   - **Nota de Alcance (Fase 0):** En esta fase el frontend contiene únicamente la estructura de configuración del monorepo, contratos tipados y scaffolding base; no incluye wireframes ni componentes de interfaz visual (postergados para la Fase 1).

2. **Capa de Persistencia e Identidad (`supabase/`):**
   - Plataforma Supabase basada en PostgreSQL 15+, Supabase Auth y Supabase Storage.
   - Es la **única fuente de verdad** (*Single Source of Truth*).
   - RLS (*Row Level Security*) habilitado en el 100% de tablas.
   - Historial de respuestas en `answer_events` como almacén de eventos de solo inserción (*Append-Only*). Operaciones `UPDATE` y `DELETE` denegadas expresamente por permisos SQL.

3. **Servicio Predictivo y Adaptativo (`services/ml-api/`):**
   - Microservicio en Python 3.11+ con FastAPI, Pydantic v2 y SQLAlchemy/asyncpg.
   - Alojado en contenedor Docker (linux/amd64) en **blitz.cloud**.
   - Responsable de:
     * Validación criptográfica de tokens Supabase JWT mediante JWKS.
     * Reconstrucción de secuencias temporales y cálculo de ventanas de práctica acumuladas.
     * Inferencia probabilística con modelos de retención (DAS3H, BKT, PFA).
     * Ejecución de la política de recomendación pedagógica con umbrales configurables y control anti-fatiga.

4. **Investigación y Experimentación Científica (`ml/`):**
   - Pipeline desacoplado para Análisis Exploratorio de Datos (EDA), extracción de características, validación cruzada con `Student Group-K-Fold` y serialización de modelos congelados con trazabilidad estricta (`metadata.json`).
   - Los scripts de entrenamiento masivo nunca se ejecutan dentro del proceso de producción de FastAPI.

---

## 3. Flujo de Ejecución Adaptativo (End-to-End en 8 Pasos)

El ciclo de interacción adaptativo sigue un flujo secuencial rigurosamente instrumentado:

```text
[Estudiante]          [Web: apps/web]        [FastAPI: services/ml-api]         [Supabase: DB]
     │                      │                            │                             │
 (1) │ Envia respuesta      │                            │                             │
     ├─────────────────────>│                            │                             │
     │                      │ (2) POST /diagnostic/answers                             │
     │                      │     + JWT + X-Idempotency  │                             │
     │                      ├───────────────────────────>│                             │
     │                      │                            │ (3) Persiste inmutable      │
     │                      │                            ├────────────────────────────>│
     │                      │                            │     INSERT INTO answer_events
     │                      │                            │<────────────────────────────┤
     │                      │                            │ (4) Reconstruye ventanas    │
     │                      │                            │     SELECT history events   │
     │                      │                            ├────────────────────────────>│
     │                      │                            │<────────────────────────────┤
     │                      │                            │                             │
     │                      │                            │ (5) Inferencia DAS3H        │
     │                      │                            │     P(R=1 | h in {24,72,168})
     │                      │                            │                             │
     │                      │                            │ (6) Adaptation Policy       │
     │                      │                            │     Riesgo > tau? Anti-spam?│
     │                      │                            │                             │
     │                      │                            │ (7) Si riesgo alto:         │
     │                      │                            │     Persiste recomendación  │
     │                      │                            ├────────────────────────────>│
     │                      │                            │<────────────────────────────┤
     │                      │                            │                             │
     │                      │ (8) Feedback + Adaptación  │ [En caso de timeout/insuf]  │
     │<─────────────────────┼────────────────────────────┤ (8b) Fallback determinista  │
```

### Detalle de los 8 Pasos:
1. **Envío de Respuesta por el Estudiante:**  
   El estudiante responde un reactivo en `apps/web/`. Se captura la opción elegida y el tiempo de respuesta exacto (`response_time_seconds`).
2. **Envío Seguro e Idempotente:**  
   `apps/web/` genera un UUIDv4 como `X-Idempotency-Key` y remite la petición autenticada a `services/ml-api/` con el JWT del estudiante.
3. **Validación, Persistencia Inmutable y Estado BKT:**  
   `services/ml-api/` valida el token mediante JWKS, evalúa la alternativa contra el banco de preguntas, persiste el evento en `answer_events` (garantizando unicidad mediante `idempotency_key`) y actualiza el estado cognitivo preliminar en `student_knowledge_states` mediante Bayesian Knowledge Tracing.
4. **Reconstrucción de Secuencia Temporal:**  
   El motor `FeatureBuilder` consulta el historial cronológico del estudiante en `answer_events` para el KC impactado, calculando aciertos y fallos en ventanas exponenciales: $w_1$ (1 hora), $w_2$ (1 día), $w_3$ (7 días) y $w_4$ (30 días), además del tiempo de inactividad transcurrido (*recency* y *lag time*).
5. **Inferencia Probabilística DAS3H:**  
   Si el estudiante cuenta con al menos $N_{min} = 3$ interacciones previas, el modelo DAS3H predice el vector de retención $P(R=1 \mid h)$ para los horizontes $h \in \{24, 72, 168\}$ horas y genera la explicación de características SHAP.
6. **Evaluación de la Política de Adaptación (*Adaptation Policy*):**  
   La política compara el riesgo estimado ($1.0 - P(R=1 \mid h=72)$) contra el umbral configurado ($\tau = 0.65$). Verifica la regla anti-fatiga (no sugerir el mismo KC si ya fue reforzado en las últimas 24 horas) y excluye de forma estricta los reactivos en cuarentena pertenecientes a la evaluación diferida de 7 días (`activity_type = 'delayed_assessment'`).
7. **Generación y Asignación de Refuerzo:**  
   Si el riesgo supera el umbral $\tau$, se asocia un microcontenido específico (`microcontents`) y se programa una actividad de repaso en `review_assignments`, registrando la decisión con su justificación algorítmica en `recommendations`.
8. **Feedback Inmediato y Fallback de Contingencia:**  
   El estudiante recibe retroalimentación formativa inmediata con la explicación del concepto. Si el estudiante no cuenta con suficiente historial (`insufficient_history`) o si el servicio ML experimenta un retraso superior a 5 segundos, se activa de manera transparente la regla de contingencia basada en aciertos recientes en base de datos.

---

## 4. Protocolos de Interacción y Comunicación

1. **Protocolo Web-to-API:**  
   Comunicación síncrona vía HTTP REST sobre TLS 1.3 con contratos formales en OpenAPI 3.1.
2. **Protocolo de Autenticación:**  
   Supabase Auth emite tokens JWT (RS256/ES256). FastAPI verifica la firma con la JWKS pública expuesta por Supabase (`/.well-known/jwks.json`).
3. **Protocolo de Idempotencia:**  
   Toda petición de registro de respuestas exige la cabecera `X-Idempotency-Key: <uuid-v4>`. Ante reintentos por intermitencia de red, la base de datos previene registros duplicados y la API retorna la respuesta original sin duplicar efectos secundarios.
4. **Protocolo de Errores Estandarizado:**  
   Todas las respuestas de error siguen la especificación **RFC 7807 (Problem Details for HTTP APIs)**, garantizando que el frontend reciba detalles estructurados de validación y códigos de error unívocos.

---

## 5. Mitigación de Arranque en Frío (*Cold Start*) en blitz.cloud

El contenedor de FastAPI se aloja en el plan gratuito de blitz.cloud, el cual suspende los procesos inactivos tras **15 minutos sin tráfico**, generando tiempos de reactivación de **10 a 25 segundos**.

Para garantizar una experiencia fluida y predecible en el entorno escolar, se aplican dos mecanismos arquitectónicos:

### 1. Endpoint de Calentamiento (*Warmup Ping*):
- Se expone el endpoint no autenticado `POST /api/v1/health/warmup`.
- Previo a las sesiones escolares de laboratorio o clase (10-15 minutos antes), un cronjob o el portal administrativo dispara este endpoint para inicializar el contenedor, cargar los artefactos de modelos en memoria RAM y verificar la conexión a Supabase.
- Respuesta:
  ```json
  {
    "status": "healthy",
    "warmed": true,
    "models_loaded": ["DAS3H", "BKT"],
    "timestamp": "2026-11-01T04:40:00Z"
  }
  ```

### 2. Presupuesto de Espera y Fallback Determinista (5000 ms):
- `apps/web/` implementa una ventana de timeout estricta de **5000 ms** para peticiones predictivas.
- Durante la espera, el cliente muestra estados de carga pedagógicamente empáticos (*"Preparando tu ruta de aprendizaje óptima..."*).
- Si el servicio predictivo excede los 5000 ms o responde con error 503, el sistema conmuta automáticamente al **Fallback Determinista**:
  - Consulta directamente en Supabase las métricas del estudiante en `student_metrics` y `student_knowledge_states`.
  - Si el acierto reciente es menor al 60% o el $p\_mastery < 0.50$, recomienda el microcontenido remedial correspondiente con el método `rule_based_fallback`.
  - La experiencia del estudiante nunca queda bloqueada ni colgada por indisponibilidad de la inferencia ML.
