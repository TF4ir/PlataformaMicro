---
trigger: always_on
description: Reglas para la experimentación, modelado y artefactos predictivos.
---
# Reglas de Machine Learning

1. **Modelo DAS3H y Baselines:** Ningún modelo neuronal complejo se adoptará sin haber batido a una regresión logística temporal (PFA extendido) y un BKT modificado en métricas AUC-ROC y Brier Score.
2. **Calibración Probabilística:** No basta optimizar la capacidad de discriminación (AUC-ROC); la probabilidad de retención $P(R=1)$ debe estar rigurosamente calibrada (analizada vía Expected Calibration Error - ECE y curvas de calibración).
3. **Versionamiento de Artefactos:** Todo artefacto empaquetado debe incluir un `metadata.json` con:
   - Versión del modelo (SemVer).
   - Timestamp de entrenamiento.
   - Hiperparámetros.
   - Commit de Git de origen.
   - Versión exacta de `scikit-learn`, `numpy` y `pandas`.
4. **Aislamiento:** Los scripts de entrenamiento masivo jamás se ejecutan dentro del proceso web de FastAPI en producción.
