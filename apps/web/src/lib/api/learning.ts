/**
 * Learning Flow & Questionnaire Management API Client (Milestone M4)
 * Connects Next.js web application to FastAPI /api/v1 activities & student learning endpoints.
 */

import { apiFetch, ApiClientError, isTransportError } from "@/lib/api/client";
import {
  DataProvenance,
  MetricMeta,
  classifyMastery,
  observedPercentage,
  resolveContentTitle,
  resolveCourseName,
  resolveKnowledgeComponentName,
  summarizeAttempt,
} from "@/lib/data-provenance";

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
  /** Null when the microcontent metadata does not declare a duration. */
  estimated_minutes: number | null;
  is_urgent: boolean;
  priority_label: string;
}

export interface StudentAnalyticsMeta {
  weekly_learning_minutes: MetricMeta;
  completed_activities_count: MetricMeta;
  observed_accuracy_percentage: MetricMeta;
  reviewed_concepts_count: MetricMeta;
  consolidated_concepts_count: MetricMeta;
  total_concepts_count: MetricMeta;
}

export interface StudentAnalyticsSummary {
  weekly_learning_minutes: number | null;
  completed_activities_count: number | null;
  total_answers: number;
  observed_accuracy_percentage: number | null;
  reviewed_concepts_count: number | null;
  consolidated_concepts_count: number | null;
  total_concepts_count: number | null;
  /** Optional metadata emitted by the resilient Supabase fallback. */
  provenance?: DataProvenance;
  metric_meta?: StudentAnalyticsMeta;
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
  /** Null when there are no answer events for this KC. */
  observed_accuracy: number | null;
  total_answers: number;
  status: string;
  /** Null unless a validated model produced an estimate. */
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

/**
 * Re-export transport error detector from central API client.
 */
export { isTransportError };

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
  // Teacher Activity Operations (Authoritative FastAPI Backend)
  // -------------------------------------------------------------

  async listTeacherActivities(courseId?: string, status?: ActivityStatus): Promise<ActivityListItem[]> {
    const params = new URLSearchParams();
    if (courseId) params.append("course_id", courseId);
    if (status) params.append("status", status);
    const qs = params.toString() ? `?${params.toString()}` : "";

    return apiFetch<ActivityListItem[]>(`/api/v1/activities${qs}`, {
      cache: "no-store",
    }, "teacher");
  },

  async getActivity(activityId: string): Promise<ActivityDetailResponse> {
    return apiFetch<ActivityDetailResponse>(`/api/v1/activities/${activityId}`, {
      cache: "no-store",
    }, "teacher");
  },

  async createActivity(payload: ActivityCreatePayload): Promise<ActivityDetailResponse> {
    return apiFetch<ActivityDetailResponse>("/api/v1/activities", {
      method: "POST",
      body: JSON.stringify(payload),
    }, "teacher");
  },

  async updateActivity(activityId: string, payload: Partial<ActivityCreatePayload>): Promise<ActivityDetailResponse> {
    return apiFetch<ActivityDetailResponse>(`/api/v1/activities/${activityId}`, {
      method: "PATCH",
      body: JSON.stringify(payload),
    }, "teacher");
  },

  async publishActivity(activityId: string): Promise<ActivityDetailResponse> {
    return apiFetch<ActivityDetailResponse>(`/api/v1/activities/${activityId}/publish`, {
      method: "POST",
    }, "teacher");
  },

  async getActivityResults(activityId: string): Promise<ActivityResultsResponse> {
    return apiFetch<ActivityResultsResponse>(`/api/v1/activities/${activityId}/results`, {
      cache: "no-store",
    }, "teacher");
  },

  async getCourseSections(courseId: string): Promise<CourseSectionItem[]> {
    return apiFetch<CourseSectionItem[]>(`/api/v1/courses/${courseId}/sections`, {
      cache: "no-store",
    }, "teacher");
  },

  // -------------------------------------------------------------
  // Student Learning Operations (FastAPI Backend Authoritative)
  // -------------------------------------------------------------

  async listStudentCourses(): Promise<StudentCourseItem[]> {
    try {
      return await apiFetch<StudentCourseItem[]>(
        "/api/v1/students/me/courses",
        { cache: "no-store" },
        "student"
      );
    } catch (err: unknown) {
      if (isTransportError(err)) {
        console.warn("Transport failure reaching FastAPI, fallback to Supabase for courses:", err);
        return await listStudentCoursesFromSupabase();
      }
      throw err;
    }
  },

  async listStudentActivities(): Promise<StudentActivityListItem[]> {
    try {
      return await apiFetch<StudentActivityListItem[]>(
        "/api/v1/students/me/activities",
        { cache: "no-store" },
        "student"
      );
    } catch (err: unknown) {
      if (isTransportError(err)) {
        console.warn("Transport failure reaching FastAPI, fallback to Supabase for activities:", err);
        return await listStudentActivitiesFromSupabase();
      }
      throw err;
    }
  },

  async getStudentActivity(activityId: string): Promise<StudentActivityDetail> {
    // Strictly authoritative FastAPI endpoint — no fallback to prevent bypassing section enrollment or dates
    return apiFetch<StudentActivityDetail>(
      `/api/v1/students/me/activities/${activityId}`,
      { cache: "no-store" },
      "student"
    );
  },

  async startAttempt(activityId: string, idempotencyKey?: string): Promise<StartAttemptResponse> {
    // Strictly authoritative FastAPI endpoint — NO fallback to prevent bypassing max_attempts or availability
    const headers: Record<string, string> = {};
    if (idempotencyKey) {
      headers["X-Idempotency-Key"] = idempotencyKey;
    }
    return apiFetch<StartAttemptResponse>(
      `/api/v1/students/me/activities/${activityId}/attempts`,
      {
        method: "POST",
        headers,
        body: JSON.stringify({ idempotency_key: idempotencyKey }),
      },
      "student"
    );
  },

  async submitAnswer(
    attemptId: string,
    payload: SubmitAnswerPayload,
    idempotencyKey?: string
  ): Promise<SubmitAnswerResponse> {
    // Strictly authoritative FastAPI endpoint — NO fallback to prevent bypassing completed attempts or duplicate answers
    const headers: Record<string, string> = {};
    const key = idempotencyKey || payload.idempotency_key;
    if (key) {
      headers["X-Idempotency-Key"] = key;
    }
    return apiFetch<SubmitAnswerResponse>(
      `/api/v1/students/me/attempts/${attemptId}/answers`,
      {
        method: "POST",
        headers,
        body: JSON.stringify(payload),
      },
      "student"
    );
  },

  async submitAttempt(attemptId: string): Promise<SubmitAttemptResponse> {
    // Strictly authoritative FastAPI endpoint — NO fallback to ensure atomic session sealing
    return apiFetch<SubmitAttemptResponse>(
      `/api/v1/students/me/attempts/${attemptId}/submit`,
      {
        method: "POST",
      },
      "student"
    );
  },

  async getAttemptResults(attemptId: string): Promise<AttemptResultsResponse> {
    // Strictly authoritative FastAPI endpoint — NO fallback to prevent premature answer leakage or bypassing after_deadline
    return apiFetch<AttemptResultsResponse>(
      `/api/v1/students/me/attempts/${attemptId}/results`,
      {
        cache: "no-store",
      },
      "student"
    );
  },

  async getDashboard(): Promise<StudentDashboardResponse> {
    try {
      return await apiFetch<StudentDashboardResponse>(
        "/api/v1/learning/student/dashboard",
        { cache: "no-store" },
        "student"
      );
    } catch (err: unknown) {
      if (isTransportError(err)) {
        console.warn("Transport failure reaching FastAPI, using resilient Supabase direct fallback for dashboard:", err);
        return await getStudentDashboardFromSupabase();
      }
      throw err;
    }
  },

  async getProgress(): Promise<StudentProgressDetailResponse> {
    try {
      return await apiFetch<StudentProgressDetailResponse>(
        "/api/v1/learning/student/progress",
        { cache: "no-store" },
        "student"
      );
    } catch (err: unknown) {
      if (isTransportError(err)) {
        console.warn("Transport failure reaching FastAPI, using resilient Supabase direct fallback for progress:", err);
        return await getStudentProgressFromSupabase();
      }
      throw err;
    }
  },
};

interface StudentSupabaseContext {
  supabase: any;
  user: { id: string; user_metadata?: Record<string, unknown> };
  profile: {
    id: string;
    tenant_id: string;
    full_name: string | null;
    student_code: string | null;
  } | null;
}

function firstRelation<T>(value: T | T[] | null | undefined): T | null {
  if (Array.isArray(value)) return value.length > 0 ? value[0] : null;
  return value ?? null;
}

async function getStudentSupabaseContext(): Promise<StudentSupabaseContext> {
  const { createClient } = await import("../supabase/client");
  const supabase = createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    throw new Error(
      "No hay una sesión autenticada. Inicia sesión para consultar tus datos."
    );
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("id, tenant_id, full_name, student_code")
    .eq("id", user.id)
    .maybeSingle();

  if (profileError) {
    throw new Error(
      `No se pudo cargar el perfil autenticado: ${profileError.message}`
    );
  }

  return { supabase, user, profile };
}

function studentDisplayName(context: StudentSupabaseContext): string {
  const metadataName = context.user.user_metadata?.full_name;
  if (context.profile?.full_name) return context.profile.full_name;
  if (typeof metadataName === "string" && metadataName.trim()) {
    return metadataName.trim();
  }
  return "Estudiante";
}

function formatShortDate(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return new Intl.DateTimeFormat("es-PE", {
    day: "2-digit",
    month: "short",
  }).format(date);
}

async function getStudentDashboardFromSupabase(): Promise<StudentDashboardResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user, profile } = context;
  const studentId = user.id;

  // 1. Enrollments -> sections -> courses (never every active course).
  const { data: enrollmentRows, error: enrollmentError } = await supabase
    .from("enrollments")
    .select("section_id, sections(id, name, course_id, courses(id, name, code, description))")
    .eq("student_id", studentId);

  if (enrollmentError) {
    throw new Error(`No se pudieron cargar tus matrículas: ${enrollmentError.message}`);
  }

  const enrollments = (enrollmentRows || [])
    .map((row: any) => {
      const section = firstRelation<any>(row.sections);
      if (!section) return null;
      const course = firstRelation<any>(section.courses);
      if (!course) return null;
      return { section, course };
    })
    .filter(Boolean) as Array<{ section: any; course: any }>;

  const courseById = new Map<string, any>();
  const sectionByCourse = new Map<string, any>();
  const courseIds: string[] = [];
  const sectionIds: string[] = [];

  for (const enrollment of enrollments) {
    if (!courseById.has(enrollment.course.id)) {
      courseById.set(enrollment.course.id, enrollment.course);
      courseIds.push(enrollment.course.id);
    }
    if (!sectionByCourse.has(enrollment.course.id)) {
      sectionByCourse.set(enrollment.course.id, enrollment.section);
    }
    if (!sectionIds.includes(enrollment.section.id)) {
      sectionIds.push(enrollment.section.id);
    }
  }

  // 2. Curricular structure for enrolled courses.
  const { data: unitRows, error: unitError } = courseIds.length
    ? await supabase
        .from("units")
        .select("id, course_id, title")
        .in("course_id", courseIds)
    : { data: [], error: null };
  if (unitError) {
    throw new Error(`No se pudieron cargar las unidades: ${unitError.message}`);
  }

  const units = unitRows || [];
  const unitIds = units.map((unit: any) => unit.id);
  const unitsByCourse = new Map<string, any[]>();
  for (const unit of units) {
    const list = unitsByCourse.get(unit.course_id) || [];
    list.push(unit);
    unitsByCourse.set(unit.course_id, list);
  }

  const { data: kcRows, error: kcError } = unitIds.length
    ? await supabase
        .from("knowledge_components")
        .select("id, name, unit_id, difficulty_prior")
        .in("unit_id", unitIds)
    : { data: [], error: null };
  if (kcError) {
    throw new Error(
      `No se pudieron cargar los componentes de conocimiento: ${kcError.message}`
    );
  }

  const kcs = kcRows || [];
  const kcsByUnit = new Map<string, any[]>();
  for (const kc of kcs) {
    const list = kcsByUnit.get(kc.unit_id) || [];
    list.push(kc);
    kcsByUnit.set(kc.unit_id, list);
  }

  // 3. Activities assigned to the student's sections.
  const { data: activitySectionRows, error: activitySectionError } =
    sectionIds.length
      ? await supabase
          .from("activity_sections")
          .select("activity_id, section_id")
          .in("section_id", sectionIds)
      : { data: [], error: null };
  if (activitySectionError) {
    throw new Error(
      `No se pudieron cargar las actividades asignadas: ${activitySectionError.message}`
    );
  }

  const assignedActivityIds: string[] = Array.from(
    new Set((activitySectionRows || []).map((row: any) => row.activity_id))
  );

  const { data: activityRows, error: activityError } = assignedActivityIds.length
    ? await supabase
        .from("activities")
        .select(
          "id, course_id, title, description, activity_type, feedback_policy, status, max_attempts, time_limit_minutes, available_from, available_until, published_at, created_at"
        )
        .in("id", assignedActivityIds)
        .eq("status", "published")
        .eq("is_active", true)
        .order("published_at", { ascending: false, nullsFirst: false })
    : { data: [], error: null };
  if (activityError) {
    throw new Error(`No se pudieron cargar las actividades: ${activityError.message}`);
  }

  const activities = activityRows || [];
  const activitiesByCourse = new Map<string, any[]>();
  for (const activity of activities) {
    const list = activitiesByCourse.get(activity.course_id) || [];
    list.push(activity);
    activitiesByCourse.set(activity.course_id, list);
  }

  // 4. Attempts, answers and exposures.
  const { data: attemptRows, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select(
      "id, activity_id, status, score, started_at, completed_at, total_questions, correct_answers"
    )
    .eq("student_id", studentId)
    .order("started_at", { ascending: false });
  if (attemptError) {
    throw new Error(`No se pudieron cargar tus intentos: ${attemptError.message}`);
  }

  const attempts = attemptRows || [];

  const { data: answerRows, error: answerError } = await supabase
    .from("answer_events")
    .select("knowledge_component_id, is_correct")
    .eq("student_id", studentId);
  if (answerError) {
    throw new Error(`No se pudieron cargar tus respuestas: ${answerError.message}`);
  }

  const answers = answerRows || [];
  const correctAnswers = answers.filter((answer: any) => answer.is_correct === true).length;
  const accuracyDisplay = observedPercentage(correctAnswers, answers.length);

  const { data: recommendationRows, error: recommendationError } = await supabase
    .from("recommendations")
    .select("id, status, decision_reason, scheduled_for, knowledge_component_id, microcontent_id")
    .eq("student_id", studentId)
    .order("scheduled_for", { ascending: true, nullsFirst: false });
  if (recommendationError) {
    throw new Error(
      `No se pudieron cargar tus recomendaciones: ${recommendationError.message}`
    );
  }

  const recommendations = recommendationRows || [];
  const pendingRecommendations = recommendations.filter(
    (recommendation: any) => recommendation.status === "pending"
  );
  const completedRecommendations = recommendations.filter(
    (recommendation: any) => recommendation.status === "completed"
  );

  const recommendationKcIds = Array.from(
    new Set(
      pendingRecommendations
        .map((recommendation: any) => recommendation.knowledge_component_id)
        .filter(Boolean)
    )
  );
  const recommendationMicrocontentIds = Array.from(
    new Set(
      pendingRecommendations
        .map((recommendation: any) => recommendation.microcontent_id)
        .filter(Boolean)
    )
  );

  const { data: recommendationKcRows, error: recommendationKcError } =
    recommendationKcIds.length
      ? await supabase
          .from("knowledge_components")
          .select("id, name, unit_id")
          .in("id", recommendationKcIds)
      : { data: [], error: null };
  if (recommendationKcError) {
    throw new Error(
      `No se pudieron cargar los conceptos recomendados: ${recommendationKcError.message}`
    );
  }

  const recommendationKcs = recommendationKcRows || [];
  const recommendationUnitIds = Array.from(
    new Set(recommendationKcs.map((kc: any) => kc.unit_id).filter(Boolean))
  );
  const { data: recommendationUnitRows, error: recommendationUnitError } =
    recommendationUnitIds.length
      ? await supabase
          .from("units")
          .select("id, course_id, title")
          .in("id", recommendationUnitIds)
      : { data: [], error: null };
  if (recommendationUnitError) {
    throw new Error(
      `No se pudieron cargar las unidades recomendadas: ${recommendationUnitError.message}`
    );
  }

  const { data: recommendationMicrocontentRows, error: recommendationMicrocontentError } =
    recommendationMicrocontentIds.length
      ? await supabase
          .from("microcontents")
          .select("id, title, estimated_duration_seconds")
          .in("id", recommendationMicrocontentIds)
      : { data: [], error: null };
  if (recommendationMicrocontentError) {
    throw new Error(
      `No se pudieron cargar los microcontenidos recomendados: ${recommendationMicrocontentError.message}`
    );
  }

  const recommendationUnitById = new Map<string, any>(
    (recommendationUnitRows || []).map((unit: any) => [unit.id, unit])
  );
  const recommendationKcById = new Map<string, any>(
    recommendationKcs.map((kc: any) => [kc.id, kc])
  );
  const recommendationMicrocontentById = new Map<string, any>(
    (recommendationMicrocontentRows || []).map((microcontent: any) => [
      microcontent.id,
      microcontent,
    ])
  );

  const now = Date.now();
  const upcoming_reviews: UpcomingReviewItem[] = pendingRecommendations.map(
    (recommendation: any) => {
      const kc = recommendationKcById.get(recommendation.knowledge_component_id);
      const unit = kc ? recommendationUnitById.get(kc.unit_id) : null;
      const course = unit ? courseById.get(unit.course_id) : null;
      const microcontent = recommendationMicrocontentById.get(
        recommendation.microcontent_id
      );
      const scheduledTime = recommendation.scheduled_for
        ? new Date(recommendation.scheduled_for).getTime()
        : null;
      const isUrgent = scheduledTime !== null && scheduledTime <= now;
      const durationSeconds = microcontent?.estimated_duration_seconds;

      return {
        recommendation_id: recommendation.id,
        knowledge_component_id: recommendation.knowledge_component_id,
        knowledge_component_name: resolveKnowledgeComponentName(kc),
        course_name: resolveCourseName(course),
        scheduled_for: recommendation.scheduled_for || null,
        estimated_minutes:
          typeof durationSeconds === "number" && durationSeconds > 0
            ? Math.max(1, Math.ceil(durationSeconds / 60))
            : null,
        is_urgent: isUrgent,
        priority_label:
          scheduledTime === null
            ? "Sin fecha programada"
            : isUrgent
            ? "Prioridad de hoy"
            : "Programado",
      };
    }
  );

  // 5. Weekly learning time is measured from content exposure events.
  const sevenDaysAgo = new Date(now - 7 * 24 * 60 * 60 * 1000).toISOString();
  const { data: exposureRows, error: exposureError } = await supabase
    .from("content_exposure_events")
    .select("duration_seconds, event_timestamp")
    .eq("student_id", studentId)
    .gte("event_timestamp", sevenDaysAgo);

  const exposureSeconds = exposureError
    ? null
    : (exposureRows || []).reduce(
        (sum: number, row: any) => sum + Number(row.duration_seconds || 0),
        0
      );

  const completedAttempts = attempts.filter(
    (attempt: any) => attempt.status === "completed"
  );

  const completedActivityIds = new Set(
    completedAttempts.map((attempt: any) => attempt.activity_id)
  );

  const kcAnswerMap = new Map<string, { total: number; correct: number }>();
  for (const answer of answers) {
    const current = kcAnswerMap.get(answer.knowledge_component_id) || {
      total: 0,
      correct: 0,
    };
    current.total += 1;
    if (answer.is_correct === true) current.correct += 1;
    kcAnswerMap.set(answer.knowledge_component_id, current);
  }

  let consolidatedConcepts = 0;
  for (const kc of kcs) {
    const stats = kcAnswerMap.get(kc.id);
    if (!stats || stats.total === 0) continue;
    const accuracy = Number(((stats.correct / stats.total) * 100).toFixed(1));
    if (classifyMastery(accuracy, stats.total) === "consolidated") {
      consolidatedConcepts += 1;
    }
  }

  const analytics: StudentAnalyticsSummary = {
    weekly_learning_minutes:
      exposureSeconds === null
        ? null
        : Number((exposureSeconds / 60).toFixed(1)),
    completed_activities_count: completedAttempts.length,
    total_answers: answers.length,
    observed_accuracy_percentage: accuracyDisplay.value,
    reviewed_concepts_count: completedRecommendations.length,
    consolidated_concepts_count: consolidatedConcepts,
    total_concepts_count: kcs.length,
    provenance: "observed",
    metric_meta: {
      weekly_learning_minutes: exposureError
        ? {
            status: "unavailable",
            provenance: "unavailable",
            sample_size: null,
          }
        : {
            status: "observed",
            provenance: "observed",
            sample_size: exposureRows?.length ?? 0,
          },
      completed_activities_count: {
        status: "observed",
        provenance: "observed",
        sample_size: completedAttempts.length,
      },
      observed_accuracy_percentage: {
        status: accuracyDisplay.status,
        provenance: accuracyDisplay.provenance,
        sample_size: answers.length,
      },
      reviewed_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: recommendations.length,
      },
      consolidated_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: answers.length,
      },
      total_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: kcs.length,
      },
    },
  };

  const enrolled_courses: StudentCourseCard[] = [];
  for (const courseId of courseIds) {
    const course = courseById.get(courseId);
    const section = sectionByCourse.get(courseId);
    const courseUnits = unitsByCourse.get(courseId) || [];
    const courseKcs = courseUnits.flatMap(
      (unit: any) => kcsByUnit.get(unit.id) || []
    );
    const courseActivities = activitiesByCourse.get(courseId) || [];
    const completedCourseActivities = courseActivities.filter((activity: any) =>
      completedActivityIds.has(activity.id)
    ).length;

    enrolled_courses.push({
      course_id: course.id,
      course_code: course.code || "",
      course_name: resolveCourseName(course),
      description: course.description || "",
      section_id: section?.id || "",
      section_name: section?.name || "Sección sin nombre",
      units_count: courseUnits.length,
      kcs_count: courseKcs.length,
      active_activities_count: courseActivities.length,
      completed_activities_count: completedCourseActivities,
      progress_percentage:
        courseActivities.length > 0
          ? Number(
              (
                (completedCourseActivities / courseActivities.length) *
                100
              ).toFixed(1)
            )
          : 0,
    });
  }

  const activityById = new Map<string, any>(
    activities.map((activity: any) => [activity.id, activity])
  );
  const attemptsByActivity = new Map<string, any[]>();
  for (const attempt of attempts) {
    const list = attemptsByActivity.get(attempt.activity_id) || [];
    list.push(attempt);
    attemptsByActivity.set(attempt.activity_id, list);
  }

  const recent_activities: StudentActivityListItem[] = assignedActivityIds
    .map((activityId) =>
      activityById.get(activityId)
    )
    .filter(Boolean)
    .slice(0, 6)
    .map((activity: any) => {
      const course = courseById.get(activity.course_id);
      const section = sectionByCourse.get(activity.course_id);
      const activityAttempts = attemptsByActivity.get(activity.id) || [];
      const latestAttempt = activityAttempts[0] || null;

      return {
        activity_id: activity.id,
        title: resolveContentTitle(activity),
        description: activity.description || null,
        course_id: activity.course_id,
        course_name: resolveCourseName(course),
        section_id: section?.id || "",
        section_name: section?.name || "Sección sin nombre",
        activity_type: (activity.activity_type as ActivityType) || "practice",
        feedback_policy:
          (activity.feedback_policy as FeedbackPolicy) ||
          "immediate_with_explanation",
        max_attempts: Number(activity.max_attempts || 0),
        time_limit_minutes:
          typeof activity.time_limit_minutes === "number"
            ? activity.time_limit_minutes
            : null,
        available_from: activity.available_from || null,
        available_until: activity.available_until || null,
        published_at: activity.published_at || null,
        attempts_count: activityAttempts.length,
        can_attempt: (() => {
          const maxAttempts = Number(activity.max_attempts || 0);
          const currentTime = new Date();
          let isAvailable = true;
          if (activity.available_from && currentTime < new Date(activity.available_from)) {
            isAvailable = false;
          }
          if (activity.available_until && currentTime > new Date(activity.available_until)) {
            isAvailable = false;
          }
          return (
            isAvailable &&
            activityAttempts.length < maxAttempts &&
            activity.status === "published"
          );
        })(),
        latest_attempt_id: latestAttempt?.id || null,
        latest_attempt_status:
          (latestAttempt?.status as AttemptStatus) || null,
        latest_score:
          typeof latestAttempt?.score === "number"
            ? latestAttempt.score
            : null,
      };
    });

  return {
    student_name: studentDisplayName(context),
    student_code: profile?.student_code || null,
    enrolled_courses,
    analytics,
    upcoming_reviews,
    recent_activities,
  };
}

async function getStudentProgressFromSupabase(): Promise<StudentProgressDetailResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user } = context;
  const studentId = user.id;

  // 1. Scope KCs strictly to student's enrolled courses to prevent leaking other curricula
  const { data: enrollmentRows, error: enrollmentError } = await supabase
    .from("enrollments")
    .select("section_id, sections(course_id)")
    .eq("student_id", studentId);
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar tus matrículas: ${enrollmentError.message}`);
  }

  const enrolledCourseIds = Array.from(
    new Set(
      (enrollmentRows || [])
        .map((r: any) => firstRelation<any>(r.sections)?.course_id)
        .filter(Boolean)
    )
  );

  const { data: unitRows, error: unitError } = enrolledCourseIds.length
    ? await supabase
        .from("units")
        .select("id")
        .in("course_id", enrolledCourseIds)
    : { data: [], error: null };
  if (unitError) {
    throw new Error(`No se pudieron cargar las unidades: ${unitError.message}`);
  }

  const enrolledUnitIds = (unitRows || []).map((u: any) => u.id);

  const { data: kcRows, error: kcError } = enrolledUnitIds.length
    ? await supabase
        .from("knowledge_components")
        .select("id, name, difficulty_prior, units(title, courses(id, name))")
        .in("unit_id", enrolledUnitIds)
        .eq("is_active", true)
    : { data: [], error: null };
  if (kcError) {
    throw new Error(
      `No se pudieron cargar los componentes de conocimiento: ${kcError.message}`
    );
  }

  const { data: answerRows, error: answerError } = await supabase
    .from("answer_events")
    .select("knowledge_component_id, is_correct, event_timestamp")
    .eq("student_id", studentId);
  if (answerError) {
    throw new Error(`No se pudieron cargar tus respuestas: ${answerError.message}`);
  }

  const allAnswers = answerRows || [];

  const { data: attemptRows, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select(
      "id, activity_id, score, status, completed_at, activities(id, title, course_id, courses(id, name))"
    )
    .eq("student_id", studentId)
    .eq("status", "completed")
    .order("completed_at", { ascending: true });
  if (attemptError) {
    throw new Error(`No se pudieron cargar tus intentos: ${attemptError.message}`);
  }

  const attempts = attemptRows || [];
  const completedAttempts = attempts.filter(
    (attempt: any) => typeof attempt.score === "number"
  );

  const { data: recommendationRows, error: recommendationError } = await supabase
    .from("recommendations")
    .select("status")
    .eq("student_id", studentId);
  if (recommendationError) {
    throw new Error(
      `No se pudieron cargar tus recomendaciones: ${recommendationError.message}`
    );
  }

  const recommendations = recommendationRows || [];
  const completedRecommendations = recommendations.filter(
    (recommendation: any) => recommendation.status === "completed"
  ).length;

  const sevenDaysAgo = new Date(
    Date.now() - 7 * 24 * 60 * 60 * 1000
  ).toISOString();
  const { data: exposureRows, error: exposureError } = await supabase
    .from("content_exposure_events")
    .select("duration_seconds, event_timestamp")
    .eq("student_id", studentId)
    .gte("event_timestamp", sevenDaysAgo);

  const exposureSeconds = exposureError
    ? null
    : (exposureRows || []).reduce(
        (sum: number, row: any) => sum + Number(row.duration_seconds || 0),
        0
      );

  const kcAnswerMap = new Map<string, { total: number; correct: number }>();
  for (const answer of allAnswers) {
    const current = kcAnswerMap.get(answer.knowledge_component_id) || {
      total: 0,
      correct: 0,
    };
    current.total += 1;
    if (answer.is_correct === true) current.correct += 1;
    kcAnswerMap.set(answer.knowledge_component_id, current);
  }

  const kcs = kcRows || [];
  const kcMastery: StudentKCMasteryProgress[] = kcs.map((kc: any) => {
    const stats = kcAnswerMap.get(kc.id);
    const total = stats?.total || 0;
    const correct = stats?.correct || 0;
    const accuracy = total > 0 ? Number(((correct / total) * 100).toFixed(1)) : null;
    const unit = firstRelation<any>(kc.units);

    return {
      kc_id: kc.id,
      kc_name: resolveKnowledgeComponentName(kc),
      unit_title: unit?.title || "Sin unidad asignada",
      observed_accuracy: accuracy,
      total_answers: total,
      status: classifyMastery(accuracy, total),
      estimated_retention: null,
      is_cold_start: total < 3,
    };
  });

  const totalAnswers = allAnswers.length;
  const correctAnswers = allAnswers.filter(
    (answer: any) => answer.is_correct === true
  ).length;
  const accuracyDisplay = observedPercentage(correctAnswers, totalAnswers);
  const consolidatedConcepts = kcMastery.filter(
    (kc) => kc.status === "consolidated"
  ).length;

  const analytics: StudentAnalyticsSummary = {
    weekly_learning_minutes:
      exposureSeconds === null
        ? null
        : Number((exposureSeconds / 60).toFixed(1)),
    completed_activities_count: attempts.length,
    total_answers: totalAnswers,
    observed_accuracy_percentage: accuracyDisplay.value,
    reviewed_concepts_count: completedRecommendations,
    consolidated_concepts_count: consolidatedConcepts,
    total_concepts_count: kcs.length,
    provenance: "observed",
    metric_meta: {
      weekly_learning_minutes: exposureError
        ? {
            status: "unavailable",
            provenance: "unavailable",
            sample_size: null,
          }
        : {
            status: "observed",
            provenance: "observed",
            sample_size: exposureRows?.length ?? 0,
          },
      completed_activities_count: {
        status: "observed",
        provenance: "observed",
        sample_size: attempts.length,
      },
      observed_accuracy_percentage: {
        status: accuracyDisplay.status,
        provenance: accuracyDisplay.provenance,
        sample_size: totalAnswers,
      },
      reviewed_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: recommendations.length,
      },
      consolidated_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: totalAnswers,
      },
      total_concepts_count: {
        status: "observed",
        provenance: "observed",
        sample_size: kcs.length,
      },
    },
  };

  const evolution: ScoreEvolutionItem[] = completedAttempts.slice(-12).map(
    (attempt: any) => {
      const activity = firstRelation<any>(attempt.activities);
      return {
        date: formatShortDate(attempt.completed_at),
        accuracy: Number(attempt.score),
        activity_title: resolveContentTitle(activity),
      };
    }
  );

  const activity_history: StudentProgressActivityHistory[] = completedAttempts
    .slice()
    .reverse()
    .map((attempt: any) => {
      const activity = firstRelation<any>(attempt.activities);
      const course = firstRelation<any>(activity?.courses);
      return {
        attempt_id: attempt.id,
        activity_id: attempt.activity_id,
        activity_title: resolveContentTitle(activity),
        course_name: resolveCourseName(course),
        completed_at: attempt.completed_at,
        score: Number(attempt.score),
        status: attempt.status,
      };
    });

  return {
    analytics,
    evolution,
    kc_breakdown: kcMastery,
    activity_history,
  };
}

async function listStudentCoursesFromSupabase(): Promise<StudentCourseItem[]> {
  const context = await getStudentSupabaseContext();
  const { supabase, user } = context;

  const { data: enrollmentRows, error } = await supabase
    .from("enrollments")
    .select("section_id, sections(id, name, course_id, courses(id, name, code, description, is_active))")
    .eq("student_id", user.id);

  if (error) {
    throw new Error(`No se pudieron cargar tus cursos: ${error.message}`);
  }

  return (enrollmentRows || [])
    .map((row: any) => {
      const section = firstRelation<any>(row.sections);
      const course = firstRelation<any>(section?.courses);
      if (!section || !course || course.is_active === false) return null;
      return {
        course_id: course.id,
        course_code: course.code || "",
        course_name: resolveCourseName(course),
        description: course.description || null,
        section_id: section.id,
        section_name: section.name || "Sección sin nombre",
      };
    })
    .filter(Boolean) as StudentCourseItem[];
}

async function listStudentActivitiesFromSupabase(): Promise<StudentActivityListItem[]> {
  const context = await getStudentSupabaseContext();
  const { supabase, user } = context;

  const { data: enrollmentRows, error: enrollmentError } = await supabase
    .from("enrollments")
    .select("sections(id, name, course_id, courses(id, name))")
    .eq("student_id", user.id);
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar tus secciones: ${enrollmentError.message}`);
  }

  const sectionRows = (enrollmentRows || [])
    .map((row: any) => firstRelation<any>(row.sections))
    .filter(Boolean);

  const sectionIds = Array.from(
    new Set(sectionRows.map((section: any) => section.id))
  );
  const sectionById = new Map<string, any>(
    sectionRows.map((section: any) => [section.id, section])
  );

  const { data: activitySectionRows, error: activitySectionError } =
    sectionIds.length
      ? await supabase
          .from("activity_sections")
          .select("activity_id, section_id")
          .in("section_id", sectionIds)
      : { data: [], error: null };
  if (activitySectionError) {
    throw new Error(
      `No se pudieron cargar tus actividades asignadas: ${activitySectionError.message}`
    );
  }

  const activityIds = Array.from(
    new Set((activitySectionRows || []).map((row: any) => row.activity_id))
  );

  const { data: activityRows, error: activityError } = activityIds.length
    ? await supabase
        .from("activities")
        .select(
          "id, course_id, title, description, activity_type, feedback_policy, status, max_attempts, time_limit_minutes, available_from, available_until, published_at, courses(id, name)"
        )
        .in("id", activityIds)
        .eq("status", "published")
        .eq("is_active", true)
        .order("published_at", { ascending: false, nullsFirst: false })
    : { data: [], error: null };
  if (activityError) {
    throw new Error(`No se pudieron cargar tus actividades: ${activityError.message}`);
  }

  const { data: attemptRows, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select("id, activity_id, status, score, started_at")
    .eq("student_id", user.id)
    .order("started_at", { ascending: false });
  if (attemptError) {
    throw new Error(`No se pudieron cargar tus intentos: ${attemptError.message}`);
  }

  const attemptsByActivity = new Map<string, any[]>();
  for (const attempt of attemptRows || []) {
    const list = attemptsByActivity.get(attempt.activity_id) || [];
    list.push(attempt);
    attemptsByActivity.set(attempt.activity_id, list);
  }

  const activityToSectionId = new Map<string, string>();
  for (const row of activitySectionRows || []) {
    if (row.activity_id && row.section_id) {
      activityToSectionId.set(row.activity_id, row.section_id);
    }
  }

  return (activityRows || []).map((activity: any) => {
    const course = firstRelation<any>(activity.courses);
    const assignedSectionId = activityToSectionId.get(activity.id);
    const section = assignedSectionId ? sectionById.get(assignedSectionId) : null;
    const activityAttempts = attemptsByActivity.get(activity.id) || [];
    const latestAttempt = activityAttempts[0] || null;
    const maxAttempts = Number(activity.max_attempts || 0);
    const now = new Date();
    let isAvailable = true;
    if (activity.available_from && now < new Date(activity.available_from)) {
      isAvailable = false;
    }
    if (activity.available_until && now > new Date(activity.available_until)) {
      isAvailable = false;
    }
    const canAttempt =
      isAvailable &&
      activityAttempts.length < maxAttempts &&
      activity.status === "published";

    return {
      activity_id: activity.id,
      title: resolveContentTitle(activity),
      description: activity.description || null,
      course_id: activity.course_id,
      course_name: resolveCourseName(course),
      section_id: section?.id || "",
      section_name: section?.name || "Sección sin nombre",
      activity_type: (activity.activity_type as ActivityType) || "practice",
      feedback_policy:
        (activity.feedback_policy as FeedbackPolicy) ||
        "immediate_with_explanation",
      max_attempts: maxAttempts,
      time_limit_minutes:
        typeof activity.time_limit_minutes === "number"
          ? activity.time_limit_minutes
          : null,
      available_from: activity.available_from || null,
      available_until: activity.available_until || null,
      published_at: activity.published_at || null,
      attempts_count: activityAttempts.length,
      can_attempt: canAttempt,
      latest_attempt_id: latestAttempt?.id || null,
      latest_attempt_status: (latestAttempt?.status as AttemptStatus) || null,
      latest_score:
        typeof latestAttempt?.score === "number" ? latestAttempt.score : null,
    };
  });
}

export const studentLearningApi = learningApi;
