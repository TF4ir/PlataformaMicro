# Contratos de Modelos e Interfaces Abstractas (Python 3.11+ / Pydantic v2)

## 1. Visión General y Principios de Diseño

El subsistema de modelado predictivo y adaptación (`services/ml-api/` y `ml/`) opera bajo contratos de tipos estrictos utilizando **Python 3.11+** y **Pydantic v2**. 

### Principios Fundamentales:
1. **Tipado Estricto y Validación en Frontera:** Todas las entradas y salidas de inferencia son validadas contra esquemas Pydantic inmutables.
2. **Desacoplamiento Algorítmico:** La inferencia matemática de retención $P(R=1 \mid h)$ está estrictamente separada de la toma de decisiones pedagógicas (*Adaptation Policy*).
3. **Reproducibilidad y Versionamiento:** Los artefactos de modelo empaquetados deben incorporar un archivo `metadata.json` con hash criptográfico SHA-256, versiones fijas de dependencias y métricas de discriminación y calibración.
4. **Prevención de Fuga Temporal (*Data Leakage*):** Las características temporales se extraen asegurando un corte estricto (`input_event_cutoff`) que no incluye información futura o contemporánea a la ventana evaluada.

---

## 2. Definición Formal de Contratos en Python

A continuación se detalla el código fuente ejecutable y tipado que define las estructuras de datos, protocolos y clases base abstractas:

```python
"""
Model Contracts and Abstract Interfaces for Adaptive Microlearning System.
Platform: Python 3.11+ with Pydantic v2.
Defines schemas for interaction events, temporal features, inference outputs,
SHAP explainability, Bayesian Knowledge Tracing protocols, and model artifact metadata.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Protocol
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ============================================================================
# 1. Enums y Tipos Fundamentales
# ============================================================================

class RiskLevel(str, Enum):
    """Nivel cualitativo de riesgo pedagógico de olvido."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PredictionStatus(str, Enum):
    """Estado de la inferencia predictiva."""
    VALID = "valid"
    INSUFFICIENT_HISTORY = "insufficient_history"
    DEGRADED_FALLBACK = "degraded_fallback"


class RecommendationMethod(str, Enum):
    """Método algorítmico utilizado para seleccionar la recomendación."""
    PREDICTIVE_MODEL = "predictive_model"
    RULE_BASED_FALLBACK = "rule_based_fallback"
    TEACHER_ASSIGNED = "teacher_assigned"


class ContentType(str, Enum):
    """Tipología pedagógica del recurso de microcontenido."""
    TEXT_SUMMARY = "text_summary"
    INFOGRAPHIC_CARD = "infographic_card"
    CONCEPT_MAP = "concept_map"


# ============================================================================
# 2. Esquemas de Eventos e Interacciones de Entrada
# ============================================================================

class StudentInteractionEvent(BaseModel):
    """
    Reflejo en memoria de un evento inmutable registrado en answer_events.
    Garantiza consistencia absoluta con el DDL de PostgreSQL y los esquemas OpenAPI.
    """
    model_config = ConfigDict(frozen=True)

    event_id: UUID = Field(description="UUID inmutable del evento de respuesta")
    attempt_id: UUID = Field(description="UUID del intento en quiz_attempts")
    student_id: UUID = Field(description="UUID del perfil del estudiante")
    question_id: UUID = Field(description="UUID de la pregunta evaluada")
    knowledge_component_id: UUID = Field(description="UUID del Knowledge Component asociado")
    selected_option_id: UUID = Field(description="UUID de la opción seleccionada")
    is_correct: bool = Field(description="Resultado de la respuesta (True si fue correcta)")
    attempt_number: int = Field(default=1, ge=1, description="Número de intento ordinal")
    response_time_seconds: float = Field(
        ge=0.1,
        le=600.0,
        description="Tiempo cronometrado de respuesta en segundos (0.1 a 600.0)"
    )
    idempotency_key: UUID = Field(description="Clave de idempotencia única para la transacción")
    event_timestamp: datetime = Field(description="Marca temporal UTC del evento")


class TemporalWindowFeatures(BaseModel):
    """
    Acumuladores de aciertos (C) y fallos (W) en ventanas exponenciales
    de tiempo para modelos de retención tipo DAS3H.
    Ventanas:
      - 1h: Última hora (3600 segundos)
      - 1d: Último día (24 horas)
      - 7d: Última semana (168 horas)
      - 30d: Último mes (720 horas)
    """
    correct_1h: int = Field(default=0, ge=0)
    incorrect_1h: int = Field(default=0, ge=0)
    correct_1d: int = Field(default=0, ge=0)
    incorrect_1d: int = Field(default=0, ge=0)
    correct_7d: int = Field(default=0, ge=0)
    incorrect_7d: int = Field(default=0, ge=0)
    correct_30d: int = Field(default=0, ge=0)
    incorrect_30d: int = Field(default=0, ge=0)


class TemporalSequenceFeatures(BaseModel):
    """
    Vector procesado de características de entrada para inferencia probabilística.
    Construido sin fuga de información temporal hacia el futuro.
    """
    student_id: UUID = Field(description="UUID del estudiante")
    knowledge_component_id: UUID = Field(description="UUID del KC analizado")
    total_interactions: int = Field(ge=0, description="Total de intentos previos en el KC")
    historical_accuracy: float = Field(
        ge=0.0,
        le=1.0,
        description="Tasa histórica acumulada de acierto [0.0, 1.0]"
    )
    avg_response_time_seconds: float = Field(ge=0.0, description="Tiempo de respuesta promedio")
    last_interaction_timestamp: Optional[datetime] = Field(
        default=None,
        description="Marca de tiempo de la interacción más reciente"
    )
    recency_hours: float = Field(
        default=0.0,
        ge=0.0,
        description="Horas transcurridas desde la última interacción"
    )
    lag_times_hours: List[float] = Field(
        default_factory=list,
        description="Lista de intervalos entre repasos sucesivos"
    )
    windows: TemporalWindowFeatures = Field(
        default_factory=TemporalWindowFeatures,
        description="Conteo de aciertos/fallos en ventanas exponenciales"
    )
    difficulty_prior: float = Field(
        default=0.500,
        ge=0.0,
        le=1.0,
        description="Dificultad intrínseca a priori del KC"
    )


# ============================================================================
# 3. Esquemas de Salida de Inferencia y Explicabilidad SHAP
# ============================================================================

class PredictionOutput(BaseModel):
    """
    Predicción probabilística para un horizonte temporal específico.
    Mapea 1:1 con los campos de la tabla predictions y el esquema OpenAPI.
    """
    horizon_hours: int = Field(gt=0, description="Horizonte de evaluación en horas (ej. 24, 72, 168)")
    prediction_horizon_hours: Optional[int] = Field(
        default=None,
        description="Alias explícito de horizon_hours para consistencia SQL"
    )
    recall_probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Probabilidad estimada de recuerdo P(R=1 | h)"
    )
    predicted_recall_probability: Optional[float] = Field(
        default=None,
        description="Alias explícito de recall_probability para consistencia SQL"
    )
    estimated_risk: float = Field(
        ge=0.0,
        le=1.0,
        description="Riesgo de olvido complementario (1.0 - recall_probability)"
    )
    risk_level: RiskLevel = Field(description="Categorización cualitativa del riesgo")

    @field_validator("estimated_risk")
    @classmethod
    def validate_risk(cls, v: float) -> float:
        return round(v, 4)

    def model_post_init(self, __context: Any) -> None:
        """Sincroniza aliases automáticamente si no fueron provistos."""
        if self.prediction_horizon_hours is None:
            object.__setattr__(self, "prediction_horizon_hours", self.horizon_hours)
        if self.predicted_recall_probability is None:
            object.__setattr__(self, "predicted_recall_probability", self.recall_probability)


class ShapExplanation(BaseModel):
    """Atribución local de importancia de características calculada mediante SHAP."""
    base_value: float = Field(description="Valor base esperado del modelo (intersección)")
    feature_importances: Dict[str, float] = Field(
        description="Diccionario de pesos de contribución por cada característica"
    )
    summary_text: str = Field(description="Interpretación en lenguaje natural del factor de riesgo")


class ModelInferenceResult(BaseModel):
    """Resultado estructurado completo retornado por el motor de inferencia."""
    status: PredictionStatus = Field(description="Estado de la inferencia")
    prediction_status: Optional[PredictionStatus] = Field(
        default=None,
        description="Alias explícito de status para consistencia con OpenAPI y SQL"
    )
    student_id: Optional[UUID] = None
    knowledge_component_id: Optional[UUID] = None
    predictions: List[PredictionOutput] = Field(
        default_factory=list,
        description="Lista de predicciones por cada horizonte solicitado"
    )
    shap_explanation: Optional[ShapExplanation] = None
    feature_importance: Optional[Dict[str, float]] = None
    input_event_cutoff: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    reason: Optional[str] = None
    created_at: Optional[datetime] = None

    def model_post_init(self, __context: Any) -> None:
        if self.prediction_status is None:
            object.__setattr__(self, "prediction_status", self.status)
        if self.shap_explanation and not self.feature_importance:
            object.__setattr__(
                self,
                "feature_importance",
                self.shap_explanation.feature_importances
            )


# ============================================================================
# 4. Protocolo de Bayesian Knowledge Tracing (BKT)
# ============================================================================

class BKTParameters(BaseModel):
    """Parámetros estándar del modelo Bayesian Knowledge Tracing."""
    p_init: float = Field(default=0.20, ge=0.0, le=1.0, description="Prior inicial de dominio")
    p_transit: float = Field(default=0.15, ge=0.0, le=1.0, description="Probabilidad de transición")
    p_slip: float = Field(default=0.10, ge=0.0, le=1.0, description="Probabilidad de desliz")
    p_guess: float = Field(default=0.20, ge=0.0, le=1.0, description="Probabilidad de adivinanza")


class KnowledgeTracingModel(Protocol):
    """
    Protocolo formal para actualizadores de estado cognitivo y seguimiento de dominio.
    Garantiza desacoplamiento estructural entre BKT clásico, DKT y variantes.
    """
    def update_state(
        self,
        current_mastery: float,
        is_correct: bool,
        params: Optional[BKTParameters] = None
    ) -> float:
        """
        Calcula el nuevo p_mastery posterior a la observación observada.
        Aplica regla bayesiana con probabilidades de desliz y adivinanza.
        """
        ...

    def get_recall_probability(
        self,
        current_mastery: float,
        elapsed_hours: float
    ) -> float:
        """
        Calcula la probabilidad de recuerdo decaída en función del tiempo transcurrido
        siguiendo una curva de decaimiento exponencial o potencial.
        """
        ...


# ============================================================================
# 5. Interfaz Base Abstracta para Modelos de Retención (BaseRetentionModel)
# ============================================================================

class BaseRetentionModel(ABC):
    """
    Clase base abstracta obligatoria para todos los modelos de retención probabilística
    (DAS3H, PFA / Regresión Logística, Baselines de Tesis).
    """

    @abstractmethod
    def load_artifact(self, artifact_path: str) -> None:
        """
        Carga el artefacto serializado (.joblib / .onnx), valida el hash de
        integridad SHA-256 y verifica compatibilidad de versiones de scikit-learn y numpy.
        """
        pass

    @abstractmethod
    def extract_features(
        self,
        history_events: List[Dict[str, Any]],
        kc_difficulty_prior: float = 0.500
    ) -> TemporalSequenceFeatures:
        """
        Transforma la secuencia cronológica inmutable de eventos de respuesta
        en el vector estructurado de características con ventanas exponenciales.
        """
        pass

    @abstractmethod
    def predict_recall(
        self,
        features: TemporalSequenceFeatures,
        horizons_hours: List[int],
        include_shap: bool = False
    ) -> ModelInferenceResult:
        """
        Ejecuta la inferencia probabilística sobre el KC objetivo para los horizontes
        temporales dados y retorna el resultado estructurado.
        """
        pass


# ============================================================================
# 6. Metadatos de Versionamiento y Empaquetado de Artefactos
# ============================================================================

class ModelEvaluationMetrics(BaseModel):
    """Métricas científicas de evaluación calculadas durante validación cruzada."""
    auc_roc: float = Field(ge=0.0, le=1.0, description="Área bajo la curva ROC (discriminación)")
    brier_score: float = Field(ge=0.0, le=1.0, description="Puntaje de Brier (calibración global)")
    ece: float = Field(ge=0.0, le=1.0, description="Expected Calibration Error (10 bins)")
    f1_score: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    log_loss: Optional[float] = Field(default=None, ge=0.0)


class ModelArtifactMetadata(BaseModel):
    """
    Esquema persistido en metadata.json dentro de cada paquete congelado de modelo.
    Garantiza trazabilidad y reproducibilidad científica absoluta.
    """
    model_name: str = Field(description="Identificador del modelo (ej. 'DAS3H')")
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$", description="Versión SemVer")
    trained_at: datetime = Field(description="Marca temporal UTC de finalización del entrenamiento")
    git_commit_sha: str = Field(description="Hash SHA-1 del commit Git que originó el entrenamiento")
    framework: str = Field(default="scikit-learn", description="Librería de ML utilizada")
    framework_version: str = Field(description="Versión exacta del framework (ej. '1.5.2')")
    python_version: str = Field(description="Versión de Python utilizada (ej. '3.11.9')")
    hyperparameters: Dict[str, Any] = Field(description="Diccionario completo de hiperparámetros")
    evaluation_metrics: ModelEvaluationMetrics = Field(
        description="Métricas de discriminación y calibración validadas"
    )
    input_feature_names: List[str] = Field(description="Nombres ordenados de las variables de entrada")
    artifact_hash_sha256: str = Field(description="Hash criptográfico SHA-256 del archivo .joblib")
```
