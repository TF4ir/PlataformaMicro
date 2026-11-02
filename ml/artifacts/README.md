# Model Artifacts Directory

Este directorio almacena los artefactos congelados y serializados de modelos predictivos validados (`.joblib` / `.pkl`).

## Protocolo de Empaquetado de Artefactos
Ningún modelo puede ser versionado ni desplegado sin un archivo `metadata.json` adyacente que declare:
- `model_name`: Identificador del modelo (ej. `DAS3H`, `PFA-Extended`, `BKT-Mod`).
- `version`: Versión semántica (ej. `1.0.0`).
- `training_timestamp`: Fecha y hora UTC ISO-8601 de finalización del entrenamiento.
- `git_commit`: Hash SHA del commit exacto del código de entrenamiento.
- `metrics`: Métricas de discriminación y calibración validadas (`auc_roc`, `brier_score`, `ece`).
- `feature_names`: Lista ordenada de nombres de características requeridas para la inferencia.
- `dependencies`: Versiones exactas de `scikit-learn`, `numpy`, `scipy` y `pandas`.

Queda terminantemente prohibido cargar modelos sin firma de metadatos o artefactos generados sin verificación de reproducibilidad.
