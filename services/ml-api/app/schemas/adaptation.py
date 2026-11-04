"""Schemas for pedagogical adaptation and spaced review recommendations."""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class RecommendationStatusEnum(str, Enum):
    """Lifecycle status of a learning recommendation."""

    PENDING = "pending"
    DELIVERED = "delivered"
    COMPLETED = "completed"
    DISMISSED = "dismissed"
    EXPIRED = "expired"


class RecommendationMethodEnum(str, Enum):
    """Algorithmic rationale for recommendation generation."""

    PREDICTIVE_MODEL = "predictive_model"
    RULE_BASED_FALLBACK = "rule_based_fallback"
    TEACHER_ASSIGNED = "teacher_assigned"


class MicrocontentSummary(BaseModel):
    """Brief metadata for recommended microcontent."""

    id: uuid.UUID
    title: str
    content_type: str
    estimated_duration_seconds: int


class RecommendationItemResponse(BaseModel):
    """Spaced review recommendation presented to student or teacher."""

    id: uuid.UUID
    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    microcontent: MicrocontentSummary
    selection_method: RecommendationMethodEnum
    decision_reason: str
    status: RecommendationStatusEnum
    created_at: datetime
    scheduled_for: datetime | None = None
    cooldown_until: datetime | None = None
    expires_at: datetime | None = None
    completed_at: datetime | None = None
    is_pending: bool = True


class CompleteRecommendationResponse(BaseModel):
    """Response returned when marking a recommendation as completed."""

    id: uuid.UUID
    status: RecommendationStatusEnum
    completed_at: datetime
    message: str


class EvaluationResultItem(BaseModel):
    """Individual decision outcome for a single Knowledge Component."""

    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    decision: str = Field(
        ...,
        description="One of: 'recommended', 'cooldown_active', 'retention_sufficient', 'no_content_available', 'fallback_applied'",
    )
    recommendation_id: uuid.UUID | None = None
    reason: str


class AdaptationEvaluationResponse(BaseModel):
    """Summary of adaptation evaluation across all student KCs."""

    student_id: uuid.UUID
    evaluated_at: datetime
    decisions: list[EvaluationResultItem] = Field(default_factory=list)
    recommendations_created: int = 0
