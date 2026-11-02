# Datasets Directory — Plataforma de Microaprendizaje Adaptativo

Este directorio alberga los datasets, esquemas y fixtures de prueba para el entrenamiento, calibración y evaluación de modelos de retención temporal (DAS3H, PFA/Logística y BKT).

## Directrices Éticas y Protección de Menores (Ley N° 29733 - Perú)
1. **Anonimización Estricta Obligatoria:** Queda terminantemente prohibido almacenar nombres reales, correos electrónicos, números de identificación escolar o datos biométricos. Todo registro de estudiante debe referenciarse exclusivamente mediante `student_id_pseudo` (UUID v4 disociado).
2. **Cuarentena de la Prueba Diferida a 7 Días:** Los reactivos y preguntas que forman parte del instrumento de evaluación diferida cuasiexperimental a 7 días están en cuarentena estricta. Jamás deben incluirse en los datasets de entrenamiento ni en los pools de recomendación adaptativa de práctica formativa.
3. **Datasets Abiertos para Pre-entrenamiento:** Dado el tamaño muestral del piloto ($N \approx 66$ alumnos), se autoriza el uso de benchmarks educativos públicos (ej. ASSISTments 2012-2013, Duolingo Half-Life Regression dataset) para inicializar parámetros aditivos antes del ajuste fino local.
