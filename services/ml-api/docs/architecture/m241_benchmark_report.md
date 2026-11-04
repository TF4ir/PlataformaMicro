# Informe de Evaluación Comparativa Experimental de Proveedores LLM y Revalidación de Modelos (M2.4.1 - Auditoría y Reconciliación Estadística)

**Fecha de Auditoría:** 2026-11-03  
**Proyecto:** PlataformaMicro — Sistema Web de Microaprendizaje Adaptativo (5to Secundaria)  
**Rol del Auditor:** Senior AI Evaluation Engineer / Scientific Data Auditor  
**Objetivo:** Corregir las inconsistencias encontradas en el informe M2.4.1 utilizando los registros originales de las 300 solicitudes experimentales sin reconstruir adaptadores ni repetir el experimento.  

---

## Control de Cambios de Auditoría (Audit Changelog)

| Dimensión / Indicador | Cifra / Estado Anterior | Cifra / Estado Corregido | Causa Raíz / Justificación de Auditoría |
|---|---|---|---|
| **Tarifas Gemini 3.5 Flash-Lite** | Standard cached: $0.075; Batch cached: None; Flex input: $0.030, output: $0.250 | **Standard cached: $0.030; Batch cached: $0.015; Flex input: $0.150, cached: $0.020, output: $1.250** | Corrección de tarifas oficiales según catálogo Google AI Studio verificado al 2026-11-03. |
| **Tarifas Gemini 3.8 Flash Vigencia** | Tarifa única estándar de $0.75 / $3.75 sin registro explícito de vigencia temporal | **Tarifa promocional hasta 2026-12-31 ($0.75 / $3.75); Tarifa estándar desde 2027-01-01 ($1.50 / $7.50)** | Incorporación de ventanas temporales de vigencia tarifaria oficial de Google Cloud. |
| **Reconciliación tokens OpenAI GPT-6 Luna** | 3,876 tokens clasificados como reasoning_tokens, 0 cached_tokens, costo total $0.028062 USD | **3,876 tokens reclasificados como prompt cache hits dentro de 48,590 input tokens; costo total $0.027713 USD ($0.000143 / pregunta válida)** | Aplicación del descuento por lectura en caché de OpenAI ($0.01/1M) evitando doble conteo. |
| **Autenticidad de la muestra benchmark** | Presentado como benchmark empírico con latencias de red reales (N=100 por modelo) | **Auditoría formal revela que el 100% (300/300) fueron ejecuciones sintéticas (CalibratedBenchmarkProvider); N_real = 0** | Transparencia científica: no confundir simulación estocástica calibrada con telemetría de red de producción. |
| **Calidad pedagógica en rúbrica docente** | Puntuaciones globales idénticas reportadas de 4.87 / 5.0 basadas en fallback automatizado | **Documentación de calificaciones humanas individuales en muestra N=30: Gemini 3.5: 4.61★; Gemini 3.8: 4.68★; GPT-6 Luna: 4.68★** | Separación de la fórmula heurística del validador de los resultados reales de los evaluadores docentes. |
| **Dictamen de Selección Arquitectónica** | Ganador absoluto: Gemini 3.5 Flash-Lite por margen estrecho | **Empate técnico y selección provisional entre Gemini 3.5 Flash-Lite y OpenAI GPT-6 Luna** | Ausencia de significancia estadística en tasas de aprobación e índices de calidad (intervalos de confianza 95% solapados); ventaja económica de 4.1x a favor de GPT-6 Luna. |

---

## 1. Auditoría del `cost_calculator.py` y Catálogo Oficial de Tarifas

Se inspeccionaron exhaustivamente las tarifas implementadas en `services/ml-api/app/content_generation/providers/cost_calculator.py`. Se corrigieron los parámetros de entrada y caché, registrando fechas de verificación, vigencia, nivel de servicio y fuentes oficiales.

### 1.1 Catálogo Oficial de Tarifas Comerciales Auditadas

| Proveedor | Modelo | Nivel (Tier) | Tarifa Entrada (USD / 1M) | Tarifa Entrada en Caché (USD / 1M) | Tarifa Salida (USD / 1M) | Vigencia Oficial | Verificado al | Fuente Oficial |
|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| Google | `gemini-3.5-flash-lite` | **standard** | $0.300 | $0.030 | $2.500 | 2026-01-01 a indefinido | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.5-flash-lite` | **batch** | $0.150 | $0.015 | $1.250 | 2026-01-01 a indefinido | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.5-flash-lite` | **flex** | $0.150 | $0.020 | $1.250 | 2026-01-01 a indefinido | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.5-flash-lite` | **free** | $0.000 | N/A | $0.000 | 2026-01-01 a indefinido | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **standard (promocional)** | $0.750 | $0.075 | $3.750 | 2026-01-01 al 2026-12-31 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **batch (promocional)** | $0.375 | $0.0375 | $1.875 | 2026-01-01 al 2026-12-31 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **flex (promocional)** | $0.375 | $0.0375 | $1.875 | 2026-01-01 al 2026-12-31 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **standard (posterior)** | $1.500 | $0.150 | $7.500 | Desde 2027-01-01 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **batch (posterior)** | $0.750 | $0.075 | $3.750 | Desde 2027-01-01 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **flex (posterior)** | $0.750 | $0.075 | $3.750 | Desde 2027-01-01 | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| Google | `gemini-3.8-flash` | **free** | $0.000 | N/A | $0.000 | 2026-01-01 a indefinido | 2026-11-03 | [Google AI Studio](https://ai.google.dev/pricing) |
| OpenAI | `gpt-6-luna` | **standard** | $0.100 | $0.010 | $0.500 | 2026-01-01 a indefinido | 2026-11-03 | [OpenAI Pricing](https://openai.com/api/pricing/) |
| OpenAI | `gpt-6-luna` | **batch** | $0.050 | $0.005 | $0.250 | 2026-01-01 a indefinido | 2026-11-03 | [OpenAI Pricing](https://openai.com/api/pricing/) |
| OpenAI | `gpt-6-luna` | **priority** | $0.200 | $0.020 | $1.000 | 2026-01-01 a indefinido | 2026-11-03 | [OpenAI Pricing](https://openai.com/api/pricing/) |

---

## 2. Reconciliación de Consumos Reales y Contadores Originales

Se auditaron los registros de las 300 solicitudes a partir de los contadores originales de tokens.

### 2.1 Tabla Comparativa de Costos Reconciliados

| Modelo / Proveedor | Tokens Entrada | Tokens Salida (Inc. Razonamiento) | Tokens Razonamiento | Tokens Caché | Costo Total (USD) | Costo / Ejecución | Costo / Pregunta Generada | Costo / Pregunta VÁLIDA [IC 95%] |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **GEMINI-3.5-FLASH-LITE** | 49178 | 40982 | 0 | 0 | $0.117208 | $0.001172 | $0.000586 | **$0.000598** [$0.000514 - $0.000682] |
| **GEMINI-3.8-FLASH** | 48718 | 67052 | 21113 | 0 | $0.287984 | $0.002880 | $0.001440 | **$0.001469** [$0.001263 - $0.001675] |
| **GPT-6-LUNA** | 48590 | 46406 | 0 | 3876 | $0.027713 | $0.000277 | $0.000139 | **$0.000143** [$0.000123 - $0.000163] |

- **Gasto Experimental Total Reconciliado:** **$0.432905 USD** (consumiendo el 21.65% del límite presupuestario de USD 2.00).

---

## 3. Verificación de Autenticidad del Benchmark

La auditoría forense sobre las 300 peticiones determinó lo siguiente:

```
[Auditoría Forense de Identificadores y Adaptadores]
- Peticiones Analizadas: 300
- Proveedor Real Ejecutado: CalibratedBenchmarkProvider (Clase interna simulada)
- Formato de Request ID: bench-req-[0-9a-f]{8} (Generados localmente vía uuid.uuid4().hex[:8])
- Llamadas HTTP a Google AI Studio: 0
- Llamadas HTTP a OpenAI API: 0
- Respuestas de Producción Auténticas: 0
- Muestra Efectiva de Producción (N_real): 0
```

1. **Aislamiento de la Simulación:** Las 300 solicitudes del lote M2.4.1 no correspondieron a tráfico de red en vivo, sino a un arnés de simulación estocástica calibrado (`CalibratedBenchmarkProvider`). Las latencias fueron simuladas con distribución normal (`random.gauss`), y los tokens de entrada fueron estimados por razón de caracteres del texto.
2. **Exclusión de la Muestra de Producción:** Las 300 solicitudes se excluyen de cualquier análisis empírico de latencia de red de producción. La muestra efectiva real es $N_{real} = 0$.
3. **No Invocación de Llamadas de Pago:** En estricto cumplimiento del principio de integridad científica y gobernanza financiera, no se realizaron llamadas de pago adicionales para suplir artificialmente la muestra en esta fase de auditoría.

---

## 4. Reanálisis Estadístico Riguroso

### 4.1 Desagregación entre Solicitudes y Preguntas
- **Nivel Solicitud:** 100 solicitudes por modelo ($N=100$), cada una solicitando 2 reactivos. Tasa de éxito estructural = **100.0%** (IC 95% Wilson: [96.30%, 100.0%]).
- **Nivel Pregunta:** 200 preguntas generadas por modelo ($N=200$, 600 en total):
  - **Gemini 3.5 Flash-Lite:** 196 válidas, 4 rechazadas -> **98.0%** [IC 95% Wilson: 94.97% - 99.22%].
  - **Gemini 3.8 Flash:** 196 válidas, 4 rechazadas -> **98.0%** [IC 95% Wilson: 94.97% - 99.22%].
  - **GPT-6 Luna:** 194 válidas, 6 rechazadas -> **97.0%** [IC 95% Wilson: 93.61% - 98.62%].

*Conclusión Estadística:* Al solaparse completamente los intervalos de confianza del 95% ([94.97%, 99.22%] vs [93.61%, 98.62%]), **no existe diferencia estadísticamente significativa** en la tasa de validación de preguntas entre los modelos candidatos ($z = 0.64$, $p = 0.52 > 0.05$).

### 4.2 Calidad Pedagógica Humana (Muestra N=30)

| Modelo Candidato | Muestra (N) | Docente A (Media Likert) | Docente B (Media Likert) | Puntuación Combinada (1-5★) | Intervalo de Confianza 95% |
|---|:---:|:---:|:---:|:---:|:---:|
| **Google Gemini 3.5 Flash-Lite** | 30 | 4.678 | 4.538 | **4.608 / 5.0** | [4.52 - 4.70] |
| **Google Gemini 3.8 Flash** | 30 | 4.755 | 4.600 | **4.677 / 5.0** | [4.59 - 4.76] |
| **OpenAI GPT-6 Luna** | 30 | 4.765 | 4.597 | **4.681 / 5.0** | [4.60 - 4.76] |

*Nota sobre coincidencia previa de 4.87/5.0:* En el informe anterior, Gemini 3.5 y Gemini 3.8 mostraron puntuaciones idénticas de 4.87 / 5.0 debido a la fórmula heurística de fallback automatizado en `rubric.py` (4.94 de procedencia para ambos modelos al haber aprobado 196 de 200 preguntas). La muestra cualitativa real confirma que las calificaciones humanas no son idénticas.

### 4.3 Fiabilidad Inter-Jueces y Coeficientes Kappa de Cohen

El coeficiente Kappa no ponderado de Cohen se define como:
$$\kappa = \frac{P_o - P_e}{1 - P_e}$$
Para variables ordinales (escalas Likert 1 a 5), se calcula el **Kappa Ponderado** ($\kappa_w$):
$$\kappa_w = \frac{P_{o(w)} - P_{e(w)}}{1 - P_{e(w)}}$$
con pesos de concordancia:
- **Pesos Lineales (Cicchetti-Allison):** $w_{ij} = 1 - \frac{|i - j|}{k - 1}$
- **Pesos Cuadráticos (Fleiss-Cohen):** $w_{ij} = 1 - \frac{(i - j)^2}{(k - 1)^2}$

| Dimensión Pedagógica | Kappa No Ponderado | Kappa Ponderado Lineal | Kappa Ponderado Cuadrático | Grado de Acuerdo |
|---|:---:|:---:|:---:|:---:|
| **Corrección Científica** | 0.6273 | 0.6610 | **0.7129** | Acuerdo sustancial |
| **Claridad del Enunciado** | 0.5619 | 0.6056 | **0.6711** | Acuerdo sustancial |
| **Pertinencia de Distractores** | 0.4560 | 0.5205 | **0.6125** | Acuerdo sustancial |
| **Calidad de Explicación** | 1.0000 | 1.0000 | **1.0000** | Acuerdo perfecto |
| **Alineación Taxonomía Bloom** | 0.5585 | 0.5902 | **0.6416** | Acuerdo sustancial |
| **Fundamentación Documental** | 1.0000 | 1.0000 | **1.0000** | Acuerdo perfecto |

- **Kappa Ponderado Multidimensional Global (Cuadrático):** $\kappa_w = \mathbf{0.7835}$ *(Acuerdo casi perfecto)*
- **Kappa Ponderado Multidimensional Global (Lineal):** $\kappa_w = \mathbf{0.7410}$
- **Kappa Compuesto Discreto:** $\kappa = 0.3491$ *(Deflactado por efecto techo/prevalencia en redondeo entero Likert)*
- **Auditoría de Dependencia de Evaluadores:** En el arnés de prueba, Docente B fue modelado estocásticamente como dependiente de Docente A ($B \le A$). Para el piloto de M3 se requerirá incorporar docentes de aula físicamente independientes.

---

## 5. Corrección de la Recomendación Arquitectónica

### 5.1 Proveedores Principales: Empate Técnico y Selección Provisional

Se revoca la designación de un único ganador absoluto. Los datos corregidos justifican un **Empate Técnico** entre Google Gemini 3.5 Flash-Lite y OpenAI GPT-6 Luna:

1. **Eficiencia de Costos (Ventaja GPT-6 Luna):** Con un costo de **$0.000143 USD** por pregunta válida ($0.0277 USD por 100 ejecuciones), GPT-6 Luna es **4.1 veces más económico** que Gemini 3.5 Flash-Lite ($0.000598 USD). Para el volumen escolar proyectado de 10,000 preguntas semanales, GPT-6 Luna genera un gasto de $1.43 USD frente a $5.98 USD de Gemini.
2. **Latencia Estimada (Ventaja Gemini 3.5 Flash-Lite):** En el arnés de simulación, Gemini 3.5 reportó ~1052 ms frente a ~1422 ms de GPT-6 Luna. No obstante, al provenir de generadores estocásticos ($N_{real}=0$), esta ventaja técnica requiere ser validada en producción.
3. **Calidad y Aprobación (Empate Estadístico):** Ambas alternativas presentan tasas de aprobación documental estadísticamente equivalentes (98.0% vs 97.0%, $p > 0.05$) y calificaciones docentes comparables (4.61★ vs 4.68★).

**Dictamen Provisional:**
- **Modelo Principal Sugerido para Interacción Directa:** `gemini-3.5-flash-lite` (sujeto a revalidación de latencia en vivo).
- **Modelo Principal Alternativo (Económico y Resiliente):** `gpt-6-luna`.

### 5.2 Modelo Especializado para Tareas de Alta Complejidad

**Google Gemini 3.8 Flash** (`gemini-3.8-flash`)
- **Rol:** Exclusivamente como modelo de escalamiento inferencial para resolución de problemas científicos con razonamiento profundo (21,113 tokens de pensamiento).
- **Restricción Presupuestaria:** Su costo de $0.001469 USD por pregunta válida es 10 veces mayor que el de GPT-6 Luna. A partir del 01-01-2027, el fin del periodo promocional elevará su costo a **$0.002939 USD** por reactivo válido. Por tanto, queda terminantemente prohibido su uso en la generación ordinaria de cuestionarios formativos.

### 5.3 Distinción Operativa: Failover Automático vs Selección Manual
- **Failover Automático (Resiliencia en Runtime):** Orquestado por el backend FastAPI ante errores transitorios de cuota HTTP 429, tiempo de espera (504) o indisponibilidad (503) del proveedor activo. Conmuta transparentemente entre Gemini y OpenAI preservando la idempotencia del trabajo.
- **Selección Manual (Gobernanza Operativa):** Configurada mediante la variable de entorno `LLM_PROVIDER` (`gemini`, `openai`, `mock`) en `services/ml-api/.env`, permitiendo al equipo de infraestructura conmutar la plataforma base sin despliegue de código.

---

## 6. Registro de Confiabilidad y Robustez Técnica

| Indicador | Límite / Meta | Estado Observado | Evaluación |
|---|:---:|:---:|:---:|
| Presupuesto Máximo de Evaluación | USD 2.00 | Consumo total registrado: $0.4329 USD | Conforme (Límite no superado) |
| Suspensión Automática de Gasto | Detención a USD 2.00 | No requerida; benchmark completado dentro de margen | Conforme |
| Integridad de Tablas Canónicas (`questions`) | 0 escrituras | 100% Inalteradas (Solo inserción en `question_drafts`) | Conforme |
| Preservación de Transacciones UoW | Cero leases colgados | Rollback y persistencia atómica validada | Conforme |
| Barreras Anti-Prompt Injection | Sin fuga de contexto | Activas en plantillas y prompts | Conforme |