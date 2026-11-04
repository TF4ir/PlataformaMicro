"""Pydantic v2 schemas for Student Learning Flow, Attempts, and Answer Events (Milestone M4)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.activities import (
    ActivityType,
    AttemptStatus,
    FeedbackPolicy,
    QuestionOptionPublic,
)


class StudentActivityListItem(BaseModel):
    """Activity entry displayed in student's assigned activities list."""

    activity_id: UUID
    title: str
    description: str | None
    course_id: UUID
    course_name: str
    section_id: UUID
    section_name: str
    activity_type: ActivityType
    feedback_policy: FeedbackPolicy
    max_attempts: int
    time_limit_minutes: int | None
    available_from: datetime | None
    available_until: datetime | None
    published_at: datetime | None
    attempts_count: int
    can_attempt: bool
    latest_attempt_id: UUID | None = None
    latest_attempt_status: AttemptStatus | None = None
    latest_score: float | None = None

    model_config = ConfigDict(from_attributes=True)


class StudentQuestionItem(BaseModel):
    """Sanitized question for student assessment without leaking answers or private explanations."""

    id: UUID
    question_text: str
    question_type: str
    order_index: int
    options: list[QuestionOptionPublic]

    model_config = ConfigDict(from_attributes=True)


class StudentActivityDetail(BaseModel):
    """Full activity representation for a student about to take or currently taking a quiz."""

    activity_id: UUID
    title: str
    description: str | None
    course_id: UUID
    course_name: str
    activity_type: ActivityType
    feedback_policy: FeedbackPolicy
    time_limit_minutes: int | None
    max_attempts: int
    questions: list[StudentQuestionItem]
    active_attempt_id: UUID | None = None


class StartAttemptRequest(BaseModel):
    """Optional payload to start an attempt with an idempotency key."""

    idempotency_key: UUID | None = Field(default=None, description="UUID de idempotencia para creación de intento")


class StartAttemptResponse(BaseModel):
    """Response returned upon starting a quiz attempt."""

    attempt_id: UUID
    activity_id: UUID
    attempt_number: int
    status: AttemptStatus
    started_at: datetime
    questions: list[StudentQuestionItem]


class SubmitAnswerRequest(BaseModel):
    """Payload to submit an individual answer during an attempt."""

    question_id: UUID = Field(..., description="UUID de la pregunta respondida")
    selected_option_id: UUID = Field(..., description="UUID de la opción seleccionada")
    response_time_seconds: float = Field(
        ...,
        gt=0.0,
        le=3600.0,
        description="Tiempo de respuesta en segundos (mayor a 0)",
    )
    idempotency_key: UUID | None = Field(
        default=None,
        description="Clave de idempotencia del evento de respuesta",
    )


class AnswerFeedback(BaseModel):
    """Feedback returned to the student if policy permits immediate explanation."""

    title: str
    explanation: str | None = None


class SubmitAnswerResponse(BaseModel):
    """Response from registering an answer in answer_events."""

    event_id: UUID
    attempt_id: UUID
    question_id: UUID
    is_correct: bool | None = None
    feedback: AnswerFeedback | None = None
    attempt_completed: bool = False
    next_question_index: int | None = None
    current_score: float | None = None


class SubmitAttemptResponse(BaseModel):
    """Confirmation when an attempt is finalized and scored."""

    attempt_id: UUID
    activity_id: UUID
    status: AttemptStatus
    score: float
    total_questions: int
    correct_answers: int
    completed_at: datetime


class AttemptQuestionReview(BaseModel):
    """Detailed question breakdown shown in results feedback."""

    question_id: UUID
    question_text: str
    knowledge_component_id: UUID
    knowledge_component_name: str
    selected_option_id: UUID | None = None
    selected_option_text: str = "No respondida"
    is_correct: bool
    correct_option_id: UUID | None = None
    correct_option_text: str | None = None
    explanation: str | None = None


class KCResultSummary(BaseModel):
    """Summary of performance per Knowledge Component for the attempt."""

    knowledge_component_id: UUID
    knowledge_component_name: str
    total_questions: int
    correct_answers: int
    mastery_rate: float


class AttemptResultsResponse(BaseModel):
    """Comprehensive results report of a completed attempt for student/teacher."""

    attempt_id: UUID
    activity_id: UUID
    activity_title: str
    course_name: str
    student_id: UUID
    student_name: str
    started_at: datetime
    completed_at: datetime | None
    score: float
    total_questions: int
    correct_answers: int
    questions: list[AttemptQuestionReview]
    kc_summaries: list[KCResultSummary]


class StudentCourseItem(BaseModel):
    """Course and section enrollment representation for the authenticated student."""

    course_id: UUID
    course_code: str
    course_name: str
    description: str | None = None
    section_id: UUID
    section_name: str

    model_config = ConfigDict(from_attributes=True)

