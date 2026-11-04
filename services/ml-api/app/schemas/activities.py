"""Pydantic v2 schemas for Activities and Teacher Questionnaire Management (Milestone M4)."""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class ActivityStatus(str, Enum):
    """Lifecycle status of an evaluation activity."""

    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class ActivityType(str, Enum):
    """Pedagogical classification of an activity."""

    DIAGNOSTIC = "diagnostic"
    PRACTICE = "practice"
    IMMEDIATE_ASSESSMENT = "immediate_assessment"
    DELAYED_ASSESSMENT = "delayed_assessment"
    FORMATIVE = "formative"
    SUMMATIVE = "summative"
    REMEDIATION = "remediation"
    RETENTION_CHECK = "retention_check"


class FeedbackPolicy(str, Enum):
    """Timing policy for revealing answer feedback and explanations."""

    IMMEDIATE_WITH_EXPLANATION = "immediate_with_explanation"
    UPON_COMPLETION = "upon_completion"
    AFTER_DEADLINE = "after_deadline"


class AttemptStatus(str, Enum):
    """Status of a student attempt on an activity."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class QuestionOptionDetail(BaseModel):
    """Option for questions in teacher review context."""

    id: UUID
    option_text: str
    is_correct: bool
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class QuestionOptionPublic(BaseModel):
    """Sanitized option for student evaluation without revealing is_correct."""

    id: UUID
    option_text: str
    order_index: int

    model_config = ConfigDict(from_attributes=True)


class ActivitySectionDetail(BaseModel):
    """Section assigned to an activity."""

    section_id: UUID
    section_name: str

    model_config = ConfigDict(from_attributes=True)


class ActivityQuestionDetail(BaseModel):
    """Question associated with an activity for teacher inspection."""

    question_id: UUID
    question_text: str
    question_type: str
    knowledge_component_id: UUID
    knowledge_component_name: str
    difficulty: float
    order_index: int
    options: list[QuestionOptionDetail] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ActivityCreateRequest(BaseModel):
    """Payload to create a new activity in draft status."""

    title: str = Field(..., min_length=3, max_length=200, description="Título de la actividad")
    description: str | None = Field(default=None, max_length=2000, description="Instrucciones o descripción")
    course_id: UUID = Field(..., description="UUID del curso al que pertenece")
    section_ids: list[UUID] = Field(..., min_length=1, description="Secciones destinatarias autorizadas")
    question_ids: list[UUID] = Field(..., min_length=1, description="Preguntas del banco institucional ordenadas")
    activity_type: ActivityType = Field(default=ActivityType.FORMATIVE, description="Tipo pedagógico")
    feedback_policy: FeedbackPolicy = Field(
        default=FeedbackPolicy.IMMEDIATE_WITH_EXPLANATION,
        description="Política de retroalimentación",
    )
    max_attempts: int = Field(default=1, ge=1, le=10, description="Número máximo de intentos permitidos")
    time_limit_minutes: int | None = Field(default=None, ge=1, le=180, description="Límite de tiempo en minutos")
    available_from: datetime | None = Field(default=None, description="Inicio del periodo de disponibilidad")
    available_until: datetime | None = Field(default=None, description="Fin del periodo de disponibilidad")


class ActivityUpdateRequest(BaseModel):
    """Payload to modify a draft activity."""

    title: str | None = Field(default=None, min_length=3, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    section_ids: list[UUID] | None = Field(default=None, min_length=1)
    question_ids: list[UUID] | None = Field(default=None, min_length=1)
    activity_type: ActivityType | None = None
    feedback_policy: FeedbackPolicy | None = None
    max_attempts: int | None = Field(default=None, ge=1, le=10)
    time_limit_minutes: int | None = Field(default=None, ge=1, le=180)
    available_from: datetime | None = None
    available_until: datetime | None = None


class ActivityListItem(BaseModel):
    """Summary item for teacher activity lists."""

    id: UUID
    tenant_id: UUID
    course_id: UUID
    course_name: str
    title: str
    description: str | None
    activity_type: ActivityType
    status: ActivityStatus
    feedback_policy: FeedbackPolicy
    max_attempts: int
    time_limit_minutes: int | None
    available_from: datetime | None
    available_until: datetime | None
    published_at: datetime | None
    created_by: UUID | None
    created_at: datetime
    updated_at: datetime
    questions_count: int
    sections_count: int
    attempts_count: int = 0
    sections: list[ActivitySectionDetail] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ActivityDetailResponse(ActivityListItem):
    """Full detail of an activity including its questions."""

    questions: list[ActivityQuestionDetail] = Field(default_factory=list)


class SectionResultMetric(BaseModel):
    """Performance metric per section in an activity."""

    section_id: UUID
    section_name: str
    enrolled_count: int
    participating_students: int
    completed_attempts: int
    average_score: float


class QuestionResultMetric(BaseModel):
    """Aggregated correctness metric per question."""

    question_id: UUID
    question_text: str
    knowledge_component_id: UUID
    knowledge_component_name: str
    total_answers: int
    correct_answers: int
    accuracy_rate: float
    order_index: int


class KCResultMetric(BaseModel):
    """Aggregated mastery rate per Knowledge Component."""

    knowledge_component_id: UUID
    knowledge_component_name: str
    total_answers: int
    correct_answers: int
    mastery_rate: float


class StudentAttemptSummary(BaseModel):
    """Summary of a specific student attempt for teacher reports."""

    attempt_id: UUID
    student_id: UUID
    student_name: str
    student_code: str | None
    section_name: str
    attempt_number: int
    status: AttemptStatus
    score: float | None
    started_at: datetime
    completed_at: datetime | None
    total_questions: int
    correct_answers: int


class ActivityResultsResponse(BaseModel):
    """Comprehensive analytical report for an activity (Teacher view)."""

    activity_id: UUID
    activity_title: str
    course_id: UUID
    course_name: str
    total_enrolled: int
    total_attempts: int
    completed_attempts: int
    participation_rate: float
    average_score: float
    sections_breakdown: list[SectionResultMetric]
    questions_breakdown: list[QuestionResultMetric]
    kc_breakdown: list[KCResultMetric]
    student_attempts: list[StudentAttemptSummary]


class CourseSectionItem(BaseModel):
    """Section of a course available for assigning activities."""

    id: UUID
    course_id: UUID
    name: str
    teacher_id: UUID
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

