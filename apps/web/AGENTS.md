# AGENTS.md — Subsisstema Web Frontend (`apps/web/`)

## 1. Misión y Alcance
Este subsistema aloja la aplicación cliente Next.js (App Router) orientada a estudiantes y docentes de 5to de secundaria. Proporciona interfaces accesibles, empáticas y de baja carga cognitiva.

## 2. Pila Tecnológica Específica
- Next.js 14+ (App Router, Server Components por defecto)
- React 18/19, TypeScript (modo estricto)
- Tailwind CSS y primitivas headless de shadcn/ui
- React Hook Form + validación de esquemas Zod
- Recharts para visualización de métricas de progreso formativo
- `@supabase/ssr` y `@supabase/supabase-js` para autenticación y consultas autorizadas

## 3. Límites y Restricciones Absolutas
1. **Fase 0 Scaffolding Guardrail (CRÍTICO):** Durante la Fase 0 queda TERMINANTEMENTE PROHIBIDO crear componentes visuales de interfaz en React/shadcn/ui, wireframes, vistas de usuario o flujos interactivos de estudiante/docente. Solo se autorizan estructuras de carpetas, archivos de configuración (`package.json`, `tsconfig.json`, `tailwind.config.ts`) y stubs de tipos.
2. **Cero Lógica Predictiva:** Prohibido importar librerías de inferencia matemática, cargar archivos `.pkl`, `.onnx` o emular la política adaptativa en el cliente.
3. **Seguridad en Navegador:** Solo se permite exponer `NEXT_PUBLIC_SUPABASE_URL` y `NEXT_PUBLIC_SUPABASE_ANON_KEY`. Prohibido referenciar `SUPABASE_SERVICE_ROLE_KEY`.
4. **Consumo de API Tipado:** Todo consumo de servicios de `services/ml-api` debe realizarse a través de clientes generados o validados contra los esquemas de `packages/contracts/openapi/openapi.json`.
5. **Lenguaje Pedagógico Empático:** En futuras fases de UI, nunca utilizar etiquetas alarmistas ("reprobado", "alto riesgo de olvido"). Usar siempre refuerzos positivos ("concepto por consolidar", "refuerzo sugerido").
6. **Resiliencia ante Cold-Start:** Diseñar clientes con estados de carga no bloqueantes y timeouts tolerantes frente al arranque en frío (10-25s) del backend FastAPI en blitz.cloud.
