# Guía de Contribución y Gobernanza Técnica

Agradecemos su interés en contribuir a la **Plataforma de Microaprendizaje Adaptativo**. Esta guía define las normas operativas, de calidad y éticas tanto para desarrolladores humanos como para agentes de IA autónomos (Antigravity).

---

## 1. Principios No Negociables

1. **Gobernanza Constitucional (`AGENTS.md`):** Todo agente y colaborador debe consultar y respetar las directrices de `AGENTS.md` y las reglas en `.agents/rules/`.
2. **Desarrollo Orientado a Contratos (Contract-First):** Si una funcionalidad requiere cambios en los tipos de datos o endpoints, el esquema en `packages/contracts/openapi/openapi.json` debe actualizarse **antes** de modificar el backend (`services/ml-api/`) o el frontend (`apps/web/`).
3. **Inmutabilidad de Eventos:** Los eventos de respuesta en `answer_events` son de solo inserción (Append-Only). No se permiten migraciones ni código que altere registros históricos de interacción.
4. **Protección de Menores (Ley N° 29733):** Jamás introducir nombres reales, correos o datos de contacto en datasets, fixtures o pruebas. Utilizar exclusivamente identificadores seudónimos (`student_id_pseudo`).
5. **Aislamiento de la Prueba a 7 Días:** Ninguna recomendación pedagógica adaptativa puede seleccionar preguntas reservadas para la evaluación de retención diferida a 7 días.

---

## 2. Flujo de Trabajo y Ramas

- Rama principal: `main` (código listo para despliegue).
- Rama de integración: `develop` (desarrollo activo).
- Ramas de funcionalidades: `feat/<subtema>` (ej. `feat/api-contracts`, `feat/das3h-features`).
- Ramas de corrección: `fix/<incidencia>` (ej. `fix/jwt-verification-audiences`).
- Ramas de investigación: `research/<experimento>` (ej. `research/das3h-pfa-benchmark`).

### Convención de Commits (Conventional Commits)
Los mensajes de commit deben seguir el estándar:
- `feat(modulo): descripción concisa en infinitivo`
- `fix(modulo): corrección de incidencia`
- `docs(modulo): actualización de documentación técnica o contratos`
- `refactor(modulo): mejora estructural sin cambio de comportamiento`
- `test(modulo): adición o corrección de suites de pruebas`
- `chore(modulo): mantenimiento de dependencias o gobernanza`

---

## 3. Criterios de Aceptación y Calidad (Definition of Done)

Para considerar completada cualquier tarea o Pull Request:

### Frontend (`apps/web/`)
- TypeScript en modo estricto sin errores (`pnpm --filter web tsc --noEmit`).
- Cero código predictivo o consumo no tipado de APIs.
- Formulario gestionado mediante `react-hook-form` y esquemas `zod`.
- Respeto a la restricción de Fase 0 (sin wireframes ni componentes visuales prematuros).

### Backend Predictivo (`services/ml-api/`)
- Verificación estricta de MyPy (`mypy --strict app`).
- Suites de pruebas unitarias y de integración pasando con código de salida 0 (`pytest`).
- Validación de `idempotency_key` en endpoints de recepción de respuestas.
- Manejo determinista de `prediction_status: "insufficient_history"`.

### Persistencia y Migraciones (`supabase/`)
- Migraciones SQL idempotentes y reversibles.
- Row Level Security (RLS) habilitado y probado en el 100% de las tablas nuevas.
- Claves primarias UUID (`gen_random_uuid()`) y columnas `created_at`.

### Investigación y Modelos (`ml/`)
- Validación con Student Group-K-Fold (sin fuga de datos de estudiantes).
- Artefactos congelados empaquetados obligatoriamente con `metadata.json`.
- Métrica Brier Score y Expected Calibration Error (ECE) reportadas formalmente.

---

## 4. Lista de Verificación Previa a Handoff / Pull Request

- [ ] ¿Los contratos OpenAPI, esquemas Pydantic y DDL SQL coinciden de forma idéntica en nombres y tipos?
- [ ] ¿Todas las pruebas automatizadas se ejecutan exitosamente?
- [ ] ¿Se preservó la inmutabilidad de `answer_events`?
- [ ] ¿Se evitó la exposición de claves privadas (`SUPABASE_SERVICE_ROLE_KEY`) al frontend?
- [ ] ¿Se verificó que los datos no contengan PII de menores de edad?
