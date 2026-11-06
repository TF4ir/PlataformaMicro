"""Pydantic v2 schemas for teacher telemetry, dashboard, roster, and reports."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ProficiencyDistributionItem(BaseModel):
    requiring_reinforcement: int = 0
    in_progress: int = 0
    consolidated: int = 0


class TeacherStudentQuickItem(BaseModel):
    id: uuid.UUID
    name: str
    code: str | None = None
    section_name: str
    accuracy: float
    weak_kc_name: str | None = None


class TeacherSectionSummary(BaseModel):
    id: uuid.UUID
    name: str
    course_id: uuid.UUID
    course_name: str
    students_count: int = 0


class TeacherDashboardResponse(BaseModel):
    """Aggregate KPIs and section distribution for teacher dashboard."""
    model_config = ConfigDict(from_attributes=True)

    teacher_name: str
    total_students: int
    total_courses: int
    total_sections: int
    published_activities: int
    total_attempts: int
    average_accuracy: float
    active_recommendations_count: int
    completed_reviews_count: int
    proficiency_distribution: ProficiencyDistributionItem
    students_requiring_reinforcement: list[TeacherStudentQuickItem]
    students_on_track: list[TeacherStudentQuickItem]
    sections: list[TeacherSectionSummary]


class TeacherKCDetailItem(BaseModel):
    id: uuid.UUID
    name: str
    difficulty_prior: float
    microcontents_count: int = 0
    questions_count: int = 0


class TeacherUnitItem(BaseModel):
    id: uuid.UUID
    title: str
    order_index: int
    kcs: list[TeacherKCDetailItem] = Field(default_factory=list)


class TeacherCourseDetail(BaseModel):
    """Course details with assigned sections, units, and KCs."""
    model_config = ConfigDict(from_attributes=True)

    course_id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool
    sections: list[TeacherSectionSummary] = Field(default_factory=list)
    units: list[TeacherUnitItem] = Field(default_factory=list)
    published_activities_count: int = 0
    microcontents_count: int = 0


class TeacherStudentRecord(BaseModel):
    """Student roster row with performance indicators for teacher view."""
    model_config = ConfigDict(from_attributes=True)

    student_id: uuid.UUID
    student_code: str | None = None
    full_name: str
    section_id: uuid.UUID
    section_name: str
    completed_activities: int
    total_answers: int
    observed_accuracy: float
    status: str  # "Consolidado", "En proceso", "Refuerzo sugerido"
    active_recommendations_count: int
    last_active_at: datetime | None = None


class TeacherAiInsight(BaseModel):
    title: str
    message: str
    recommended_focus_kc: str | None = None


class SectionReportsMetric(BaseModel):
    section_id: uuid.UUID
    section_name: str
    students_count: int
    completed_attempts: int
    average_score: float
    reviews_completed: int


class HeatmapKCItem(BaseModel):
    id: uuid.UUID
    name: str


class HeatmapStudentRow(BaseModel):
    student_id: uuid.UUID
    student_name: str
    student_code: str | None = None
    section_name: str
    kcs: dict[str, dict[str, Any]]  # kc_id -> {"accuracy": 85.0, "status": "consolidated" | "support" | "proficient"}


class HeatmapData(BaseModel):
    kcs: list[HeatmapKCItem]
    rows: list[HeatmapStudentRow]


class KCPerformanceItem(BaseModel):
    kc_id: uuid.UUID
    kc_name: str
    average_accuracy: float
    students_evaluated: int


class GrowthTrajectoryItem(BaseModel):
    """Weekly observed accuracy from immutable answer_events.

    Projected curves are intentionally absent until a validated predictive
    model exists. This prevents fabricated retention numbers in teacher reports.
    """

    period: str
    historical_observed: float | None = None
    sample_size: int = 0


class TeacherReportsResponse(BaseModel):
    """Comprehensive analytics and telemetry report for teachers."""
    model_config = ConfigDict(from_attributes=True)

    ai_insight: TeacherAiInsight
    sections_summary: list[SectionReportsMetric]
    mastery_heatmap: HeatmapData
    kc_performance_overview: list[KCPerformanceItem]
    retention_growth_trajectory: list[GrowthTrajectoryItem]
