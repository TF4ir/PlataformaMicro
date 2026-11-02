# AGENTS.md — Plataforma de Microaprendizaje Adaptativo (5to Secundaria)

## 1. Identidad y Misión del Proyecto
Desarrollo de un sistema web de microaprendizaje adaptativo enfocado en estudiantes de 5to año de secundaria (16-17 años).
El objetivo es modelar la dinámica de retención y olvido mediante predicción probabilística por componentes de conocimiento (Knowledge Components - KC) para planificar repasos oportunos y optimizar la retención a largo plazo.
- Materia piloto inicial: Ciencias.
- Restricción de diseño: La arquitectura debe ser completamente agnóstica a la asignatura; no debe existir acoplamiento semántico ni hardcoding del curso Ciencias.

## 2. Pila Tecnológica Homologada
- **Frontend:** Next.js (App Router), React, TypeScript, Tailwind CSS, shadcn/ui, Zod, React Hook Form, Recharts.
- **Backend de Persistencia e Identidad:** Supabase (PostgreSQL 15+, Supabase Auth, Row Level Security, Supabase Storage).
- **Backend Predictivo & Adaptativo:** Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy/asyncpg, NumPy, pandas, scikit-learn.
- **Modelo Predictivo Temporal:** DAS3H (candidato preferente) sujeto a validación experimental rigurosa frente a baselines (PFA/Logística, BKT modificado).
- **Entorno e Infraestructura:** Docker (linux/amd64), blitz.cloud (alojamiento del contenedor FastAPI), Vercel (frontend), GitHub (control de versiones).

## 3. Delimitación Estricta de Fronteras Arquitectónicas
1. **Frontend Desacoplado:** El frontend jamás ejecuta algoritmos predictivos, jamás accede a archivos `.pkl` o artefactos ML, y no toma decisiones de recomendación pedagógica. Consume la API de FastAPI o interactúa con Supabase mediante Server Actions/Client tipados.
2. **Servicio Python Especializado:** FastAPI es un motor de inferencia, construcción de secuencias temporales y política adaptativa. Supabase es la ÚNICA fuente de verdad. FastAPI no es dueño de la base de datos ni corre migraciones DDL.
3. **Persistencia Centralizada y Segura:** Todas las mutaciones de datos educativos pasan por validaciones de integridad o funciones en Supabase con RLS estricto. La service-role key JAMÁS se expone al cliente web.
4. **Separación Investigación vs Producción:** El código de experimentación y entrenamiento masivo reside en `ml/`. El servicio web en producción reside en `services/ml-api/`. La producción solo consume artefactos congelados con metadatos y versiones explícitas.

## 4. Integridad de Datos e Investigación Educativa
1. **Inmutabilidad de Eventos:** Los registros en `answer_events` son de solo inserción (Append-Only). Queda terminantemente prohibido sobrescribir o alterar marcas de tiempo (`event_timestamp`), resultados observados (`is_correct`) o parámetros de contexto.
2. **Prevención de Data Leakage:** Jamás se deben incorporar eventos futuros o contemporáneos al horizonte temporal $h$ dentro del vector de características de entrada.
3. **Diferenciación Conceptual:** Una probabilidad de recuperación estimada $P(R=1)$ NO es certeza de olvido. Las evaluaciones de investigación (inmediatas y diferidas a 7 días) deben distinguirse de las prácticas formativas adaptativas y NO pueden ser alteradas por la política de recomendación.
4. **Protección a Menores:** Prohibido registrar nombres reales, correos identificables o datos personales de estudiantes de secundaria en datasets de entrenamiento y fixtures locales. Utilizar identificadores seudónimos (`student_id_pseudo`).

## 5. Reglas de Interacción de Agentes
1. No inventar umbrales predictivos ni resultados de AUC/Brier score. Todo umbral de corte debe ser parametrizable vía configuración.
2. Respetar contratos de tipos (TypeScript y OpenAPI Pydantic). Si un cambio en backend afecta la API, actualizar `packages/contracts/openapi/openapi.json` antes de tocar el frontend.
3. El agente nunca debe dar por completada una tarea sin pruebas automatizadas y compilación exitosa.
