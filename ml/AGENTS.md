# AGENTS.md — Subsistema de Investigación y Machine Learning (`ml/`)

## 1. Misión y Alcance
Espacio de trabajo científico para análisis exploratorio de datos (EDA), ingeniería de características temporales, entrenamiento de modelos de memoria (DAS3H, PFA, BKT), validación cruzada y calibración probabilística para la investigación de tesis.

## 2. Estructura de Directorios
- `configs/`: Hiperparámetros de modelos y canalizaciones en formato YAML/JSON.
- `datasets/`: Datos crudos y procesados. Prohibido almacenar PII.
- `notebooks/`: Cuadernos de experimentación preliminar y visualización.
- `src/`: Código modular (`preprocessing/`, `features/`, `baselines/`, `das3h/`, `evaluation/`, `training/`).
- `artifacts/`: Modelos entrenados congelados acompañados mandatoriamente de `metadata.json`.
- `tests/`: Pruebas unitarias de transformaciones matemáticas y extractores de ventanas de tiempo.

## 3. Reglas Metodológicas y de Integridad
1. **Validación Experimental Rigurosa:** Todo modelo complejo (DAS3H) debe batir formalmente a los baselines (regresión logística temporal PFA y BKT modificado) en AUC-ROC y Brier Score.
2. **Calibración Obligatoria:** No basta evaluar discriminación (AUC-ROC). La probabilidad de retención estimada debe estar calibrada empíricamente (verificada mediante Expected Calibration Error - ECE y curvas de confiabilidad).
3. **Prevención de Fuga de Datos (Data Leakage):**
   - Emplear validación cruzada agrupada por estudiante (Student Group-K-Fold).
   - Respetar la causalidad temporal estricta: ninguna característica de entrada puede derivarse de eventos futuros.
4. **Cuarentena de la Prueba Diferida (7 días):** Los reactivos asignados a la prueba cuasiexperimental diferida a 7 días quedan estrictamente prohibidos para entrenamiento o micropráctica adaptativa.
5. **Empaquetado de Artefactos:** Cada artefacto serializado en `artifacts/` debe incluir un `metadata.json` con:
   - Versión SemVer del artefacto.
   - Hash del commit de Git de procedencia.
   - Hiperparámetros exactos y semilla aleatoria.
   - Versión exacta de `scikit-learn`, `numpy` y `pandas`.
6. **Ética y Protección de Menores (Ley N° 29733):** Prohibido registrar o procesar nombres, correos o datos identificables de estudiantes. Utilizar exclusivamente identificadores seudonimizados (`student_id_pseudo`).
