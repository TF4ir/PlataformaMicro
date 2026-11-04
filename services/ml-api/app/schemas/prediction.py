"""Schemas for retention forecasting and model state inference."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class ModelAvailabilityStatus(str, Enum):
    """Lifecycle status of the retention prediction model."""

    EMPIRICAL_MODEL_READY = "empirical_model_ready"
    COLD_START = "cold_start"
    INSUFFICIENT_EMPIRICAL_DATA = "insufficient_empirical_data"
    SYNTHETIC_TEST_MODE = "synthetic_test_mode"
    MODEL_UNAVAILABLE = "model_unavailable"


class RiskLevelEnum(str, Enum):
    """Categorical forgetting risk level."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class HorizonPrediction(BaseModel):
    """Retention probability at a specific projection horizon."""

    horizon_hours: int = Field(..., gt=0, description="Elapsed hours into the future")
    predicted_recall_probability: float = Field(..., ge=0.0, le=1.0)
    estimated_risk: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevelEnum


class KCRetentionPrediction(BaseModel):
    """Full retention profile for a Knowledge Component."""

    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    current_recall_probability: float = Field(..., ge=0.0, le=1.0)
    current_forgetting_risk: float = Field(..., ge=0.0, le=1.0)
    predicted_forgetting_time_seconds: float | None = None
    predicted_forgetting_time_days: float | None = None
    recommended_review_time: datetime | None = None
    tau_threshold: float = Field(default=0.650, ge=0.0, le=1.0)
    model_name: str
    model_version: str
    availability_status: ModelAvailabilityStatus
    horizons: list[HorizonPrediction] = Field(default_factory=list)
    input_event_cutoff: datetime
    total_exposures: int = 0
    total_retrieval_attempts: int = 0
    last_interaction_at: datetime | None = None


class StudentRetentionSummaryResponse(BaseModel):
    """Aggregated retention state of all accessible KCs for the authenticated student."""

    student_id: uuid.UUID
    as_of: datetime
    status: ModelAvailabilityStatus
    kcs: list[KCRetentionPrediction] = Field(default_factory=list)
    audit_note: str = ""
