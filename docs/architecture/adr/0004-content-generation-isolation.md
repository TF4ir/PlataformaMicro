# ADR-0004: Aislamiento del Módulo de Generación Asistida de Contenido, Adaptador LLM Configurable y Notificaciones In-App

- **Status:** ACCEPTED
- **Date:** 2026-11-02
- **Deciders:** Lead Architect, Antigravity AI Orchestrator
- **Technical Domain:** Educational Content Ingestion, LLM Provider Abstraction, Human-in-the-Loop Question Curation, In-App Notification Delivery, Storage Isolation
- **Consulted:** Backend Specialist, Frontend Lead, Security Auditor, Research Integrity Committee

---

## 1. Context and Problem Statement

El desarrollo de la plataforma de microaprendizaje adaptativo requiere incorporar capacidades para que los docentes carguen materiales curriculares (presentaciones PPTX y documentos PDF), extraigan conceptos clave y generen borradores de preguntas de evaluación formativa asistidos por Inteligencia Artificial. Asimismo, los estudiantes requieren consumir microcontenidos multimedia estructurados y recibir avisos oportunos de repasos espaciados recomendados.

Esta expansión funcional introduce cinco desafíos arquitectónicos y metodológicos críticos:

### 1.1 Riesgo de Contaminación del Banco Canónico y Alucinación del LLM
Los modelos de lenguaje (LLM) presentan riesgos inherentes de alucinación factual, generación de opciones de respuesta ambiguas o incorrectas, y asignaciones espurias a Componentes de Conocimiento (KC). Si un LLM pudiera insertar preguntas directamente en el banco publicado (`questions` y `question_options`), la validez de las evaluaciones y la integridad de la telemetría formativa (`answer_events`) quedarían severamente comprometidas.

### 1.2 Riesgo de Acoplamiento y Obsolescencia de Proveedores LLM
Fijar en el código un modelo propietario o versión específica (como "Gemini 1.5 Flash") crea una dependencia frágil sujeta a políticas de retiro de versiones, límites de cuota, variaciones de latencia y costos variables. Se requiere un desacoplamiento que permita alternar entre proveedores de nube y modelos locales sin alterar la lógica de negocio ni los contratos de API.

### 1.3 Sobrecarga de Infraestructura y Riesgo de Complejidad Prematura
Introducir de forma prematura colas distribuidas basadas en Redis, trabajadores asíncronos en Celery o un microservicio independiente para la ingesta documental saturaría los recursos del entorno de despliegue en blitz.cloud (máquinas limitadas con arranque en frío), incrementando la superficie de fallas y la carga cognitiva de mantenimiento.

### 1.4 Riesgo de Saturación de Notificaciones y Fragilidad de Web Push
Implementar Web Push (Service Workers, claves VAPID y notificaciones a nivel de sistema operativo) en la fase inicial expone el sistema a permisos denegados por el navegador, incompatibilidades móviles y fatiga de alertas en estudiantes menores de edad.

### 1.5 Privacidad de Menores y Seguridad de Almacenamiento
Bajo la Ley N° 29733 (Perú), queda prohibido transmitir datos identificables de estudiantes a APIs de terceros. Asimismo, los materiales docentes subidos a Supabase Storage deben aislarse estrictamente por institución educativa (`tenant_id`), impidiendo accesos cruzados no autorizados.

---

## 2. Decision Outcome

Se decide estructurar el módulo de generación y gestión de recursos bajo cinco pilares arquitectónicos:

### Pilar 1: Aislamiento Modular Estricto dentro de `services/ml-api`
- La funcionalidad de ingesta y generación de reactivos residirá en el paquete dedicado:
  `services/ml-api/app/content_generation/` (extractores, adaptadores LLM, servicios y repositorios).
- Este módulo queda **estrictamente aislado** de los paquetes `prediction/` (modelos temporales DAS3H/PFA) y `adaptation/` (política pedagógica).
- La ejecución de generación documental no bloqueará ni competirá con el hilo de inferencia en tiempo real.
- Si en fases posteriores la demanda computacional de procesamiento de archivos requiere escalar horizontalmente, el módulo podrá extraerse a un microservicio independiente (`services/content-ai`) mediante un nuevo ADR sin modificar los contratos REST existentes.

### Pilar 2: Adaptador LLM Configurable y Agnóstico (`QuestionGenerationProvider`)
- Se define un protocolo formal en Python (`QuestionGenerationProvider`) con métodos tipados:
  ```python
  class QuestionGenerationProvider(Protocol):
      async def generate_drafts(
          self, 
          extracted_text: str, 
          schema: dict, 
          context: GenerationContext
      ) -> LLMGenerationOutput:
          ...
  ```
- El proveedor y modelo concreto se configuran mediante variables de entorno en el microservicio:
  `LLM_PROVIDER` (ej. `google_vertex`, `openai`, `local_vllm`) y `LLM_MODEL_ID` (ej. identificador de modelo dinámico).
- Queda expresamente prohibido hardcodear cadenas como `"gemini-1.5-flash"` en el código.
- Los materiales se procesan bajo el principio de **dato no confiable**, aplicando prompts delimitados que rechazan inyecciones de instrucciones contenidas en los documentos fuente.
- Queda prohibido enviar nombres, notas, correos o identificadores de estudiantes a cualquier proveedor externo.

### Pilar 3: Cuarentena de Borradores y Flujo Human-in-the-Loop Obligatorio
- La generación de preguntas es exclusivamente asistiva. El sistema persiste los resultados en la tabla temporal `question_drafts` con estado inicial `'draft'`.
- Ningún registro de `question_drafts` participa en actividades, quizzes ni recomendaciones de estudiantes.
- Cada borrador incluye `source_references` con el número de página o diapositiva y el fragmento textual de respaldo para auditoría docente.
- Un docente titular debe revisar, editar si es necesario, asociar el KC canónico definitivo y aprobar explícitamente (`POST /api/v1/content-generation/jobs/{id}/approve`).
- La aprobación ejecuta una transacción PostgreSQL que valida la existencia de exactamente una alternativa correcta e inserta los registros en `questions` y `question_options`.

### Pilar 4: Orquestación Ligera sin Redis/Celery para el MVP
- El seguimiento del ciclo de vida del procesamiento documental se modela de forma determinista en PostgreSQL mediante la tabla `content_generation_jobs` con estados:
  `'queued'`, `'processing'`, `'review_required'`, `'approved'`, `'rejected'`, `'failed'`.
- Las solicitudes del docente envían la ruta interna del objeto en Supabase Storage (`storage_path`), nunca URLs externas arbitrarias.
- El microservicio descarga el archivo validando tenant, tamaño (máx 30 MB) y tipo MIME (`application/pdf`, PPTX).
- Se evita la introducción de Redis, Celery o RabbitMQ en esta fase, manteniendo la arquitectura ligera y económica para blitz.cloud.

### Pilar 5: Canal de Avisos In-App Exclusivo y Deduplicado
- Los avisos para los estudiantes se presentan dentro de la aplicación mediante la tabla `notifications`.
- Cada notificación cuenta con una clave determinista `deduplication_key` (ej. `student_id:kc_id:horizon:date`) para evitar saturar al estudiante si refresca la interfaz.
- La consulta de notificaciones y recomendaciones del estudiante resuelve su identidad a partir de `auth.uid()` (`GET /api/v1/students/me/recommendations` y `GET /api/v1/students/me/notifications`), cerrando la vulnerabilidad de confiar en un `student_id` suministrado por el cliente.
- La tecnología Web Push queda diferida como mejora opcional a ser evaluada tras validar la adherencia in-app.

---

## 3. Diagrama de Secuencia del Flujo Asistido

```text
[Docente Web]            [Supabase Storage]       [FastAPI ml-api]       [Proveedor LLM]       [PostgreSQL DB]
      │                          │                       │                      │                     │
      │ (1) Sube PDF/PPTX        │                       │                      │                     │
      ├─────────────────────────>│ (Bucket Privado)      │                      │                     │
      │                          │                       │                      │                     │
      │ (2) POST /jobs {path}    │                       │                      │                     │
      ├─────────────────────────────────────────────────>│                      │                     │
      │                          │ (3) Descarga segura   │                      │                     │
      │                          │<──────────────────────┤                      │                     │
      │                          │                       │ (4) Prompt estruct.  │                     │
      │                          │                       ├─────────────────────>│                     │
      │                          │                       │<─────────────────────┤                     │
      │                          │                       │ (5) Valida Pydantic  │                     │
      │                          │                       │                      │                     │
      │                          │                       │ (6) Inserta drafts   │                     │
      │                          │                       ├───────────────────────────────────────────>│
      │                          │                       │                      │ (question_drafts)   │
      │ (7) GET /drafts          │                       │                      │                     │
      │<─────────────────────────────────────────────────┤                      │                     │
      │                          │                       │                      │                     │
      │ (8) POST /jobs/id/approve (Human-in-the-Loop)    │                      │                     │
      ├─────────────────────────────────────────────────>│                      │                     │
      │                          │                       │ (9) Transacción DDL: │                     │
      │                          │                       │     questions + question_options           │
      │                          │                       ├───────────────────────────────────────────>│
      │ (10) 200 OK Publicado    │                       │                      │                     │
      │<─────────────────────────────────────────────────┤                      │                     │
```

---

## 4. Consecuencias y Compensaciones

### Consecuencias Positivas:
1. **Cero Polución del Banco de Preguntas:** La cuarentena de borradores garantiza que los estudiantes nunca reciban preguntas no validadas ni alucinaciones de IA.
2. **Independencia de Proveedor:** Capacidad de alternar entre OpenAI, Google Vertex AI, Anthropic o modelos locales (Ollama/vLLM) mediante un simple cambio en variables de entorno.
3. **Seguridad y Confidencialidad:** Bucket privado de Storage con RLS por docente/tenant; cero datos de menores transmitidos al LLM.
4. **Resiliencia Operativa:** No añade dependencias pesadas de infraestructura como Redis o workers Celery en blitz.cloud.
5. **Experiencia Empática y sin Fatiga:** Notificaciones in-app con deduplicación estricta y sin alertas invasivas en pantalla bloqueada.

### Consecuencias Negativas y Mitigaciones:
1. *Procesamiento Síncrono o Semi-asíncrono de Archivos Grandes:* Documentos de más de 20 páginas pueden demorar de 15 a 30 segundos.
   - *Mitigación:* Límite estricto de tamaño a 30 MB, extracción optimizada de texto y estados de trabajo (`queued`, `processing`) consultables mediante polling ligero desde el frontend.
2. *Carga de Revisión Docente:* El docente debe revisar las preguntas antes de que estén disponibles.
   - *Mitigación:* Se diseñará un editor ergonómico de revisión rápida con comparación lado a lado del texto fuente y la pregunta generada.
