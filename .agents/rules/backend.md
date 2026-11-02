---
trigger: always_on
description: Reglas de desarrollo para el backend FastAPI y servicios Python.
---
# Reglas de Backend (FastAPI)

1. **Estructura Hexagonal / Modular:**
   - `core/`: Configuraciones, seguridad, middleware.
   - `api/v1/`: Rutas y serialización de controladores HTTP.
   - `schemas/`: Modelos Pydantic v2 de entrada y salida con validación estricta.
   - `services/`: Orquestación de casos de uso (Learning, Prediction, Adaptation).
   - `prediction/`: Cargadores de artefactos de inferencia y cálculo de características.
   - `adaptation/`: Motores de políticas de decisión pedagógica.
2. **Manejo de Errores y Estados de Fallback:** Todo endpoint predictivo debe contemplar la respuesta `insufficient_history` y delegar a la política de reglas de respaldo (`rule_based_fallback`).
3. **Idempotencia:** Toda operación de registro de respuestas (`/learning/attempts/{id}/answers`) debe requerir y validar un encabezado o clave de idempotencia (`idempotency_key`).
4. **Tipado Estricto:** Código 100% tipado con comprobaciones MyPy y validación Pydantic.
