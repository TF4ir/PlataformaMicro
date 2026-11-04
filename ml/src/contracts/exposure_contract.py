"""Data contracts for student knowledge exposure, study events, and retention tracking.

Addresses Section 5 of TASK M5.1:
Verifies and specifies the event contracts for content exposure, initial study,
and subsequent retrieval activities, strictly differentiating study exposures
from retrieval assessment observations (answer_events).
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class ExposureType(str, Enum):
    """Categorization of learning exposure opportunities."""

    INITIAL_STUDY = "initial_study"          # First time the student reads/views the KC material
    REVIEW_STUDY = "review_study"            # Subsequent scheduled or voluntary reading of microcontent
    REMEDIAL_READING = "remedial_reading"    # Review triggered immediately following retrieval failure
    DIAGNOSTIC_EXPOSURE = "diagnostic_exposure"


class ExposureCompletionStatus(str, Enum):
    """Completion status of a study or microcontent exposure."""

    COMPLETED = "completed"
    PARTIAL = "partial"
    ABANDONED = "abandoned"


class ContentExposureEvent(BaseModel):
    """Contract for student interaction with educational learning material (Microcontent).

    Note: This is an EXPOSURE event (encoding/input), distinct from an answer_event (retrieval/output).
    Currently identified as a missing telemetry contract in the existing database schema.
    """

    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    tenant_id: uuid.UUID
    student_id_pseudo: uuid.UUID = Field(
        ...,
        description="Pseudonymized student identifier (no PII, Ley N° 29733 compliant)",
    )
    microcontent_id: uuid.UUID = Field(
        ...,
        description="Reference to canonical microcontents table",
    )
    knowledge_component_id: uuid.UUID = Field(
        ...,
        description="KC associated with the microcontent studied",
    )
    exposure_type: ExposureType = Field(
        default=ExposureType.INITIAL_STUDY,
        description="Indicates whether this was initial study, review, or remedial reading",
    )
    started_at: datetime = Field(
        ...,
        description="Timestamp when the student opened/started viewing the microcontent",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Timestamp when the student finished or closed the material",
    )
    duration_seconds: float = Field(
        ...,
        ge=0.0,
        description="Active engagement time spent reading/studying the microcontent",
    )
    completion_status: ExposureCompletionStatus = Field(
        default=ExposureCompletionStatus.COMPLETED,
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional telemetry (scroll depth, audio completed, card flipped)",
    )


class StudentInteractionEvent(BaseModel):
    """Canonical memory interaction event used by knowledge tracing models.

    Represents an observable retrieval practice event (derived from answer_events).
    """

    event_id: uuid.UUID
    student_id_pseudo: str
    kc_id: str
    question_id: str
    event_timestamp: datetime
    is_correct: int = Field(..., ge=0, le=1)  # 1 = correct recall, 0 = retrieval failure
    response_time_seconds: float = Field(..., gt=0.0)
    activity_type: str = Field(
        default="practice",
        description="Type of activity: practice, diagnostic, formative, delayed_assessment",
    )
    attempt_number: int = Field(default=1, ge=1)
    question_difficulty: float = Field(default=0.50, ge=0.0, le=1.0)


class RetentionProjectionPoint(BaseModel):
    """Projected retention probability at a specific elapsed future horizon delta."""

    delta_seconds: float = Field(..., ge=0.0, description="Elapsed time into the future in seconds")
    delta_hours: float = Field(..., ge=0.0)
    delta_days: float = Field(..., ge=0.0)
    recall_probability: float = Field(..., ge=0.0, le=1.0)
    forgetting_risk: float = Field(..., ge=0.0, le=1.0)


class RetentionPredictionOutput(BaseModel):
    """Complete predictive output for a (student, KC) pair at reference time t."""

    student_id_pseudo: str
    kc_id: str
    reference_time: datetime
    tau_threshold: float = Field(
        default=0.65,
        ge=0.01,
        le=0.99,
        description="Retention threshold below which review is recommended",
    )
    current_recall_probability: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Estimated recall probability at delta = 0 (the current moment)",
    )
    current_forgetting_risk: float = Field(..., ge=0.0, le=1.0)
    predicted_forgetting_time_seconds: float | None = Field(
        default=None,
        description="Earliest future delta (in seconds) where P_recall drops below tau",
    )
    predicted_forgetting_time_days: float | None = Field(default=None)
    recommended_review_window_start_days: float | None = Field(
        default=None,
        description="Preventive review recommendation window start (e.g. 85% of critical delta)",
    )
    projections: list[RetentionProjectionPoint] = Field(
        default_factory=list,
        description="Retention curve sampled at standard evaluation horizons",
    )
    model_name: str
    model_version: str
    supports_time_decay: bool
    is_cold_start: bool = False
    audit_notes: str = ""
