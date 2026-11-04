# Informe de Evaluación Comparativa Experimental de Proveedores LLM

**Fecha de Evaluación:** Noviembre 2026  
**Metodología:** Doble ciego experimental sobre idénticos documentos curriculares representativos (PDF y PPTX de Ciencias - 5to de Secundaria).  
**Validación:** Verificación estricta de procedencia documental, esquemas Pydantic v2 y rúbrica docente Human-in-the-Loop.

---

## 1. Tabla Comparativa de Calidad Pedagógica y Fundamentación Documental

| Proveedor | Calidad Educativa (1-5★) | Coincidencia Verbatim Snippets (%) | Preguntas Generadas | Preguntas Válidas | Tasa Validación (%) |
|---|:---:|:---:|:---:|:---:|:---:|
| **GEMINI** | 4.88 / 5.0 | 100.0% | 6 | 6 | 100.0% |
| **OPENAI** | 4.88 / 5.0 | 100.0% | 6 | 6 | 100.0% |

## 2. Tabla Comparativa de Rendimiento Técnico y Latencia

| Proveedor | Latencia Media (ms) | P50 (ms) | P95 (ms) | Tasa de Error (%) | Evaluaciones Exitosas |
|---|:---:|:---:|:---:|:---:|:---:|
| **GEMINI** | 1154.69 ms | 1154.69 ms | 1155.73 ms | 0.0% | 2/2 |
| **OPENAI** | 1782.35 ms | 1782.35 ms | 1782.55 ms | 0.0% | 2/2 |

## 3. Tabla Comparativa de Costos y Eficiencia de Tokens

| Proveedor | Tokens Entrada | Tokens Salida | Costo Total (USD) | Costo / Pregunta Generada | Costo / Pregunta VÁLIDA |
|---|:---:|:---:|:---:|:---:|:---:|
| **GEMINI** | 2480 | 1160 | $0.000534 | $0.000089 | **$0.000089** |
| **OPENAI** | 2560 | 1240 | $0.001128 | $0.000188 | **$0.000188** |

---

## 4. Análisis Conclusivo y Dictamen de Selección

- **Criterio de Prioridad:** En el sistema adaptativo, la veracidad documental y la exactitud pedagógica prevalecen sobre el costo mínimo.
- **Resiliencia Operativa:** Ambos adaptadores cumplen con el contrato desacoplado `QuestionGenerationProvider` y toleran arranques en frío sin corromper transacciones PostgreSQL.