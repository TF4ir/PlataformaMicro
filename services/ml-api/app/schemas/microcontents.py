"""Pydantic v2 schemas for microcontents and content exposure telemetry."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class MicrocontentSectionItem(BaseModel):
    """Structured section within a microcontent."""
    model_config = ConfigDict(extra="ignore")

    id: int
    nav_title: str = Field(alias="navTitle")
    heading: str
    tag: str
    lead: str
    duration_minutes: int = Field(default=2, alias="durationMinutes")
    body: str | None = None
    formula: str | None = None
    analogy: dict[str, str] | None = None
    key_takeaways: list[dict[str, str]] | None = Field(default=None, alias="keyTakeaways")


class MicrocontentDetailResponse(BaseModel):
    """Detailed microcontent response for student lesson reader."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    unit_id: uuid.UUID | None = None
    unit_title: str | None = None
    course_id: uuid.UUID | None = None
    course_name: str | None = None
    title: str
    content_type: str
    content_body: dict[str, Any]
    estimated_duration_seconds: int
    is_published: bool
    created_at: datetime


class MicrocontentListItem(BaseModel):
    """Brief microcontent summary for catalog listings."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    tenant_id: uuid.UUID
    knowledge_component_id: uuid.UUID
    knowledge_component_name: str
    unit_title: str | None = None
    course_name: str | None = None
    title: str
    content_type: str
    estimated_duration_seconds: int
    is_published: bool
    created_by: uuid.UUID
    created_at: datetime


class RecordExposureRequest(BaseModel):
    """Payload to record a completed reading or review session in content_exposure_events."""
    model_config = ConfigDict(extra="forbid")

    started_at: datetime
    completed_at: datetime | None = None
    duration_seconds: float = Field(ge=0.0)
    active_reading_seconds: float | None = Field(default=None, ge=0.0)
    completion_status: str = Field(default="completed", pattern="^(completed|abandoned)$")
    exposure_type: str = Field(default="initial_study", pattern="^(initial_study|review_study)$")
    session_id: uuid.UUID
    idempotency_key: uuid.UUID
    recommendation_id: uuid.UUID | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class RecordExposureResponse(BaseModel):
    """Confirmation of recorded exposure in append-only event store."""
    model_config = ConfigDict(from_attributes=True)

    event_id: uuid.UUID
    microcontent_id: uuid.UUID
    knowledge_component_id: uuid.UUID
    exposure_type: str
    recorded_at: datetime
    recommendation_completed: bool = False


class MicrocontentCreateRequest(BaseModel):
    """Teacher payload to author a new microcontent."""
    model_config = ConfigDict(extra="forbid")

    knowledge_component_id: uuid.UUID
    title: str = Field(min_length=3, max_length=255)
    content_type: str = Field(default="text_summary", pattern="^(text_summary|infographic_card|concept_map)$")
    content_body: dict[str, Any]
    estimated_duration_seconds: int = Field(default=180, ge=30, le=1800)
    is_published: bool = False


class MicrocontentUpdateRequest(BaseModel):
    """Teacher payload to edit microcontent draft."""
    model_config = ConfigDict(extra="forbid")

    title: str | None = Field(default=None, min_length=3, max_length=255)
    content_type: str | None = Field(default=None, pattern="^(text_summary|infographic_card|concept_map)$")
    content_body: dict[str, Any] | None = None
    estimated_duration_seconds: int | None = Field(default=None, ge=30, le=1800)
    is_published: bool | None = None
