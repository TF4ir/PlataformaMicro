/**
 * Learning Flow & Questionnaire Management API Client (Milestone M4)
 * Connects Next.js web application to FastAPI /api/v1 activities & student learning endpoints.
 */

export type ActivityStatus = "draft" | "published" | "closed";

export type ActivityType =
  | "diagnostic"
  | "practice"
  | "immediate_assessment"
  | "delayed_assessment"
  | "formative"
  | "summative"
  | "remediation"
  | "retention_check";

export type FeedbackPolicy =
  | "immediate_with_explanation"
  | "upon_completion"
  | "after_deadline";

export type AttemptStatus = "in_progress" | "completed" | "abandoned";

export interface QuestionOptionPublic {
  id: string;
  option_text: string;
  order_index: number;
}

export interface StudentQuestionItem {
  id: string;
  question_text: string;
  question_type: string;
  order_index: number;
  options: QuestionOptionPublic[];
}

export interface StudentActivityListItem {
  activity_id: string;
  title: string;
  description: string | null;
  course_id: string;
  course_name: string;
  section_id: string;
  section_name: string;
  activity_type: ActivityType;
  feedback_policy: FeedbackPolicy;
  max_attempts: number;
  time_limit_minutes: number | null;
  available_from: string | null;
  available_until: string | null;
  published_at: string | null;
  attempts_count: number;
  can_attempt: boolean;
  latest_attempt_id: string | null;
  latest_attempt_status: AttemptStatus | null;
  latest_score: number | null;
}

export interface StudentActivityDetail {
  activity_id: string;
  title: string;
  description: string | null;
  course_id: string;
  course_name: string;
  activity_type: ActivityType;
  feedback_policy: FeedbackPolicy;
  time_limit_minutes: number | null;
  max_attempts: number;
  questions: StudentQuestionItem[];
  active_attempt_id: string | null;
}

export interface StartAttemptResponse {
  attempt_id: string;
  activity_id: string;
  attempt_number: number;
  status: AttemptStatus;
  started_at: string;
  questions: StudentQuestionItem[];
}

export interface SubmitAnswerPayload {
  question_id: string;
  selected_option_id: string;
  response_time_seconds: number;
  idempotency_key?: string;
}

export interface AnswerFeedback {
  title: string;
  explanation: string | null;
}

export interface SubmitAnswerResponse {
  event_id: string;
  attempt_id: string;
  question_id: string;
  is_correct: boolean | null;
  feedback: AnswerFeedback | null;
  attempt_completed: boolean;
  next_question_index: number | null;
  current_score: number | null;
}

export interface SubmitAttemptResponse {
  attempt_id: string;
  activity_id: string;
  status: AttemptStatus;
  score: number;
  total_questions: number;
  correct_answers: number;
  completed_at: string;
}

export interface AttemptQuestionReview {
  question_id: string;
  question_text: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  selected_option_id: string | null;
  selected_option_text: string;
  is_correct: boolean;
  correct_option_id: string | null;
  correct_option_text: string | null;
  explanation: string | null;
}

export interface CourseSectionItem {
  id: string;
  course_id: string;
  name: string;
  teacher_id: string;
  created_at: string;
}

export interface StudentCourseItem {
  course_id: string;
  course_code: string;
  course_name: string;
  description: string | null;
  section_id: string;
  section_name: string;
}


export interface KCResultSummary {
  knowledge_component_id: string;
  knowledge_component_name: string;
  total_questions: number;
  correct_answers: number;
  mastery_rate: number;
}

export interface AttemptResultsResponse {
  attempt_id: string;
  activity_id: string;
  activity_title: string;
  course_name: string;
  student_id: string;
  student_name: string;
  started_at: string;
  completed_at: string | null;
  score: number;
  total_questions: number;
  correct_answers: number;
  questions: AttemptQuestionReview[];
  kc_summaries: KCResultSummary[];
}

export interface StudentCourseCard {
  course_id: string;
  course_code: string;
  course_name: string;
  description: string | null;
  section_id: string;
  section_name: string;
  units_count: number;
  kcs_count: number;
  active_activities_count: number;
  completed_activities_count: number;
  progress_percentage: number;
}

export interface UpcomingReviewItem {
  recommendation_id: string | null;
  knowledge_component_id: string;
  knowledge_component_name: string;
  course_name: string;
  scheduled_for: string | null;
  estimated_minutes: number;
  is_urgent: boolean;
  priority_label: string;
}

export interface StudentAnalyticsSummary {
  weekly_learning_minutes: number;
  completed_activities_count: number;
  total_answers: number;
  observed_accuracy_percentage: number;
  reviewed_concepts_count: number;
  consolidated_concepts_count: number;
  total_concepts_count: number;
}

export interface StudentDashboardResponse {
  student_name: string;
  student_code: string | null;
  enrolled_courses: StudentCourseCard[];
  analytics: StudentAnalyticsSummary;
  upcoming_reviews: UpcomingReviewItem[];
  recent_activities: StudentActivityListItem[];
}

export interface ScoreEvolutionItem {
  date: string;
  accuracy: number;
  activity_title: string;
}

export interface StudentKCMasteryProgress {
  kc_id: string;
  kc_name: string;
  unit_title: string;
  observed_accuracy: number;
  total_answers: number;
  status: string;
  estimated_retention: number | null;
  is_cold_start: boolean;
}

export interface StudentProgressActivityHistory {
  attempt_id: string;
  activity_id: string;
  activity_title: string;
  course_name: string;
  completed_at: string;
  score: number;
  status: string;
}

export interface StudentProgressDetailResponse {
  analytics: StudentAnalyticsSummary;
  evolution: ScoreEvolutionItem[];
  kc_breakdown: StudentKCMasteryProgress[];
  activity_history: StudentProgressActivityHistory[];
}

// Teacher Activity Management Interfaces
export interface ActivitySectionDetail {
  section_id: string;
  section_name: string;
}

export interface QuestionOptionDetail {
  id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
}

export interface ActivityQuestionDetail {
  question_id: string;
  question_text: string;
  question_type: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  difficulty: number;
  order_index: number;
  options: QuestionOptionDetail[];
}

export interface ActivityListItem {
  id: string;
  tenant_id: string;
  course_id: string;
  course_name: string;
  title: string;
  description: string | null;
  activity_type: ActivityType;
  status: ActivityStatus;
  feedback_policy: FeedbackPolicy;
  max_attempts: number;
  time_limit_minutes: number | null;
  available_from: string | null;
  available_until: string | null;
  published_at: string | null;
  created_by: string | null;
  created_at: string;
  updated_at: string;
  questions_count: number;
  sections_count: number;
  attempts_count: number;
  sections: ActivitySectionDetail[];
}

export interface ActivityDetailResponse extends ActivityListItem {
  questions: ActivityQuestionDetail[];
}

export interface ActivityCreatePayload {
  title: string;
  description?: string | null;
  course_id: string;
  section_ids: string[];
  question_ids: string[];
  activity_type?: ActivityType;
  feedback_policy?: FeedbackPolicy;
  max_attempts?: number;
  time_limit_minutes?: number | null;
  available_from?: string | null;
  available_until?: string | null;
}

export interface SectionResultMetric {
  section_id: string;
  section_name: string;
  enrolled_count: number;
  participating_students: number;
  completed_attempts: number;
  average_score: number;
}

export interface QuestionResultMetric {
  question_id: string;
  question_text: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  total_answers: number;
  correct_answers: number;
  accuracy_rate: number;
  order_index: number;
}

export interface KCResultMetric {
  knowledge_component_id: string;
  knowledge_component_name: string;
  total_answers: number;
  correct_answers: number;
  mastery_rate: number;
}

export interface StudentAttemptSummary {
  attempt_id: string;
  student_id: string;
  student_name: string;
  student_code: string | null;
  section_name: string;
  attempt_number: number;
  status: AttemptStatus;
  score: number | null;
  started_at: string;
  completed_at: string | null;
  total_questions: number;
  correct_answers: number;
}

export interface ActivityResultsResponse {
  activity_id: string;
  activity_title: string;
  course_id: string;
  course_name: string;
  total_enrolled: number;
  total_attempts: number;
  completed_attempts: number;
  participation_rate: number;
  average_score: number;
  sections_breakdown: SectionResultMetric[];
  questions_breakdown: QuestionResultMetric[];
  kc_breakdown: KCResultMetric[];
  student_attempts: StudentAttemptSummary[];
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Dynamic Auth & Headers helpers
async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session }, error } = await supabase.auth.getSession();
    if (!error && session?.access_token) {
      return session.access_token;
    }
  } catch (err) {
    // In environments without window or active Supabase context
  }
  return null;
}

async function getAuthHeaders(roleFallback: "teacher" | "student" = "student"): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = await getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  // Development/Test fallback only when explicitly enabled and NOT in production
  if (process.env.NODE_ENV !== "production" && process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH === "true") {
    if (roleFallback === "teacher") {
      headers["X-User-Id"] = "d0000000-0000-0000-0000-000000000001";
      headers["X-Tenant-Id"] = "a0000000-0000-0000-0000-000000000001";
      headers["X-User-Role"] = "teacher";
      headers["X-Course-Ids"] = "c0000000-0000-0000-0000-000000000001";
    } else {
      headers["X-User-Id"] = "e0000000-0000-0000-0000-000000000001";
      headers["X-Tenant-Id"] = "a0000000-0000-0000-0000-000000000001";
      headers["X-User-Role"] = "student";
    }
  }

  return headers;
}

async function getTeacherHeaders(): Promise<Record<string, string>> {
  return getAuthHeaders("teacher");
}

async function getStudentHeaders(): Promise<Record<string, string>> {
  return getAuthHeaders("student");
}

export function extractErrorMessage(err: unknown, fallback: string): string {
  if (!err || typeof err !== "object") return fallback;
  const e = err as Record<string, any>;
  if (typeof e.detail === "string") return e.detail;
  if (typeof e.detail?.detail === "string") return e.detail.detail;
  if (typeof e.detail?.title === "string") return e.detail.title;
  if (Array.isArray(e.detail)) {
    const msgs = e.detail.map((item: any) => item?.msg || item?.message).filter(Boolean);
    if (msgs.length > 0) return msgs.join("; ");
  }
  if (typeof e.message === "string") return e.message;
  return fallback;
}

export const learningApi = {
  // -------------------------------------------------------------
  // Teacher Activity Operations
  // -------------------------------------------------------------

  async listTeacherActivities(courseId?: string, status?: ActivityStatus): Promise<ActivityListItem[]> {
    const params = new URLSearchParams();
    if (courseId) params.append("course_id", courseId);
    if (status) params.append("status", status);
    const qs = params.toString() ? `?${params.toString()}` : "";

    const res = await fetch(`${API_BASE_URL}/api/v1/activities${qs}`, {
      headers: await getTeacherHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al listar actividades docentes"));
    }
    return res.json();
  },

  async getActivity(activityId: string): Promise<ActivityDetailResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}`, {
      headers: await getTeacherHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al obtener actividad"));
    }
    return res.json();
  },

  async createActivity(payload: ActivityCreatePayload): Promise<ActivityDetailResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities`, {
      method: "POST",
      headers: await getTeacherHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al crear actividad"));
    }
    return res.json();
  },

  async updateActivity(activityId: string, payload: Partial<ActivityCreatePayload>): Promise<ActivityDetailResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}`, {
      method: "PATCH",
      headers: await getTeacherHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al actualizar actividad"));
    }
    return res.json();
  },

  async publishActivity(activityId: string): Promise<ActivityDetailResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/publish`, {
      method: "POST",
      headers: await getTeacherHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al publicar actividad"));
    }
    return res.json();
  },

  async getActivityResults(activityId: string): Promise<ActivityResultsResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/activities/${activityId}/results`, {
      headers: await getTeacherHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al consultar analítica docente"));
    }
    return res.json();
  },

  async getCourseSections(courseId: string): Promise<CourseSectionItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/courses/${courseId}/sections`, {
      headers: await getTeacherHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al listar secciones del curso"));
    }
    return res.json();
  },

  // -------------------------------------------------------------
  // Student Learning Operations
  // -------------------------------------------------------------

  async listStudentCourses(): Promise<StudentCourseItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/courses`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al listar cursos del estudiante"));
    }
    return res.json();
  },

  async listStudentActivities(): Promise<StudentActivityListItem[]> {
    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/activities`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al listar actividades del estudiante"));
    }
    return res.json();
  },

  async getStudentActivity(activityId: string): Promise<StudentActivityDetail> {
    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/activities/${activityId}`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al cargar cuestionario del estudiante"));
    }
    return res.json();
  },

  async startAttempt(activityId: string, idempotencyKey?: string): Promise<StartAttemptResponse> {
    const baseHeaders = await getStudentHeaders();
    const headers: Record<string, string> = { ...baseHeaders };
    if (idempotencyKey) {
      headers["X-Idempotency-Key"] = idempotencyKey;
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/activities/${activityId}/attempts`, {
      method: "POST",
      headers,
      body: JSON.stringify({ idempotency_key: idempotencyKey }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al iniciar intento de evaluación"));
    }
    return res.json();
  },

  async submitAnswer(
    attemptId: string,
    payload: SubmitAnswerPayload,
    idempotencyKey?: string
  ): Promise<SubmitAnswerResponse> {
    const baseHeaders = await getStudentHeaders();
    const headers: Record<string, string> = { ...baseHeaders };
    const key = idempotencyKey || payload.idempotency_key;
    if (key) {
      headers["X-Idempotency-Key"] = key;
    }

    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/attempts/${attemptId}/answers`, {
      method: "POST",
      headers,
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al registrar respuesta"));
    }
    return res.json();
  },

  async submitAttempt(attemptId: string): Promise<SubmitAttemptResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/attempts/${attemptId}/submit`, {
      method: "POST",
      headers: await getStudentHeaders(),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al finalizar intento"));
    }
    return res.json();
  },

  async getAttemptResults(attemptId: string): Promise<AttemptResultsResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/students/me/attempts/${attemptId}/results`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al consultar resultados del intento"));
    }
    return res.json();
  },

  async getDashboard(): Promise<StudentDashboardResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/learning/student/dashboard`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al consultar panel del estudiante"));
    }
    return res.json();
  },

  async getProgress(): Promise<StudentProgressDetailResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/learning/student/progress`, {
      headers: await getStudentHeaders(),
      cache: "no-store",
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(extractErrorMessage(err, "Error al consultar progreso del estudiante"));
    }
    return res.json();
  },
};

export const studentLearningApi = learningApi;
