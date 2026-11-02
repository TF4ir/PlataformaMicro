---
trigger: always_on
description: Reglas de límites arquitectónicos, modularidad y flujo de datos.
---
# Reglas de Arquitectura

1. **Separación de Responsabilidades:**
   - Presentación y experiencia de usuario: `apps/web/`.
   - Persistencia, autenticación y autorización declarativa: `supabase/`.
   - Modelado temporal, inferencia y lógica de adaptación: `services/ml-api/`.
   - Experimentación y evaluación científica: `ml/`.
2. **Cero Duplicación de Lógica:** Las reglas de negocio adaptativas no se replican en el cliente web; se exponen mediante endpoints versionados `/api/v1/recommendations/*`.
3. **Contratos Tipados:** La comunicación cliente-servidor se basa en contratos OpenAPI. Ningún payload JSON libre sin esquema Pydantic / Zod está permitido.
4. **Resiliencia de Despliegue:** FastAPI debe operar bajo la restricción de arranque en frío (cold start de 15 min en blitz.cloud free). El frontend debe implementar estados de carga no bloqueantes y fallback de políticas basadas en reglas locales o backend en caso de fallo o timeout.
