/**
 * Learning Flow & Questionnaire Management API Client (Milestone M4)
 * Connects Next.js web application to FastAPI /api/v1 activities & student learning endpoints.
 */

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

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

function shouldFetchBackend(): boolean {
  if (typeof window !== "undefined") {
    if (
      window.location.protocol === "https:" &&
      (!API_BASE_URL ||
        API_BASE_URL.startsWith("http://localhost") ||
        API_BASE_URL.startsWith("http://127.0.0.1"))
    ) {
      return false;
    }
  }
  return Boolean(API_BASE_URL);
}

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

async function getAuthHeaders(): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = await getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // No identity fallback: requests without a verified session are sent
  // unauthenticated and the FastAPI backend rejects them with 401.
  return headers;
}

async function getTeacherHeaders(): Promise<Record<string, string>> {
  return getAuthHeaders();
}

async function getStudentHeaders(): Promise<Record<string, string>> {
  return getAuthHeaders();
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
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/students/me/courses`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for courses:", err);
      }
    }
    return await listStudentCoursesFromSupabase();
  },

  async listStudentActivities(): Promise<StudentActivityListItem[]> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/students/me/activities`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for activities:", err);
      }
    }
    return await listStudentActivitiesFromSupabase();
  },

  async getStudentActivity(activityId: string): Promise<StudentActivityDetail> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/students/me/activities/${activityId}`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for activity detail:", err);
      }
    }
    return await getStudentActivityFromSupabase(activityId);
  },

  async startAttempt(activityId: string, idempotencyKey?: string): Promise<StartAttemptResponse> {
    if (shouldFetchBackend()) {
      try {
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
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for starting attempt:", err);
      }
    }
    return await startAttemptFromSupabase(activityId, idempotencyKey);
  },

  async submitAnswer(
    attemptId: string,
    payload: SubmitAnswerPayload,
    idempotencyKey?: string
  ): Promise<SubmitAnswerResponse> {
    if (shouldFetchBackend()) {
      try {
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
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for submitAnswer:", err);
      }
    }
    return await submitAnswerFromSupabase(attemptId, payload);
  },

  async submitAttempt(attemptId: string): Promise<SubmitAttemptResponse> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/students/me/attempts/${attemptId}/submit`, {
          method: "POST",
          headers: await getStudentHeaders(),
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for submitAttempt:", err);
      }
    }
    return await submitAttemptFromSupabase(attemptId);
  },

  async getAttemptResults(attemptId: string): Promise<AttemptResultsResponse> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/students/me/attempts/${attemptId}/results`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, fallback to Supabase for getAttemptResults:", err);
      }
    }
    return await getAttemptResultsFromSupabase(attemptId);
  },

  async getDashboard(): Promise<StudentDashboardResponse> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/learning/student/dashboard`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, using resilient Supabase direct fallback:", err);
      }
    }
    return await getStudentDashboardFromSupabase();
  },

  async getProgress(): Promise<StudentProgressDetailResponse> {
    if (shouldFetchBackend()) {
      try {
        const res = await fetch(`${API_BASE_URL}/api/v1/learning/student/progress`, {
          headers: await getStudentHeaders(),
          cache: "no-store",
        });
        if (res.ok) {
          return await res.json();
        }
      } catch (err) {
        console.warn("FastAPI unreachable, using resilient Supabase direct fallback:", err);
      }
    }
    return await getStudentProgressFromSupabase();
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
  const { createClient } = await import("@/lib/supabase/client");
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
        can_attempt:
          activityAttempts.length < Number(activity.max_attempts || 0) &&
          activity.status === "published",
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

  const { data: kcRows, error: kcError } = await supabase
    .from("knowledge_components")
    .select("id, name, difficulty_prior, units(title, courses(id, name))")
    .eq("is_active", true);
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
    .select("section_id, sections(id, name, course_id, courses(id, name, code, description))")
    .eq("student_id", user.id);

  if (error) {
    throw new Error(`No se pudieron cargar tus cursos: ${error.message}`);
  }

  return (enrollmentRows || [])
    .map((row: any) => {
      const section = firstRelation<any>(row.sections);
      const course = firstRelation<any>(section?.courses);
      if (!section || !course) return null;
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

  return (activityRows || []).map((activity: any) => {
    const course = firstRelation<any>(activity.courses);
    const section = Array.from(sectionById.values()).find(
      (candidate: any) => candidate.course_id === activity.course_id
    );
    const activityAttempts = attemptsByActivity.get(activity.id) || [];
    const latestAttempt = activityAttempts[0] || null;
    const maxAttempts = Number(activity.max_attempts || 0);

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
      can_attempt:
        activityAttempts.length < maxAttempts && activity.status === "published",
      latest_attempt_id: latestAttempt?.id || null,
      latest_attempt_status: (latestAttempt?.status as AttemptStatus) || null,
      latest_score:
        typeof latestAttempt?.score === "number" ? latestAttempt.score : null,
    };
  });
}

async function getStudentActivityFromSupabase(
  activityId: string
): Promise<StudentActivityDetail> {
  const context = await getStudentSupabaseContext();
  const { supabase } = context;

  const { data: act, error: activityError } = await supabase
    .from("activities")
    .select(
      "id, course_id, title, description, activity_type, feedback_policy, status, max_attempts, time_limit_minutes, courses(id, name)"
    )
    .eq("id", activityId)
    .eq("status", "published")
    .maybeSingle();

  if (activityError || !act) {
    throw new Error(
      activityError
        ? `No se pudo cargar la actividad: ${activityError.message}`
        : "La actividad no está disponible o no está publicada."
    );
  }

  const { data: questionRows, error: questionError } = await supabase
    .from("activity_questions")
    .select(
      "order_index, questions(id, question_text, question_type, question_options(id, option_text, order_index))"
    )
    .eq("activity_id", activityId)
    .order("order_index", { ascending: true });
  if (questionError) {
    throw new Error(
      `No se pudieron cargar las preguntas de la actividad: ${questionError.message}`
    );
  }

  const questions: StudentQuestionItem[] = (questionRows || []).map((row: any) => {
    const question = firstRelation<any>(row.questions);
    return {
      id: question?.id || "",
      question_text: question?.question_text || "",
      question_type: question?.question_type || "single_choice",
      order_index: row.order_index,
      options: (question?.question_options || [])
        .slice()
        .sort((x: any, y: any) => x.order_index - y.order_index)
        .map((opt: any) => ({
          id: opt.id,
          option_text: opt.option_text,
          order_index: opt.order_index,
        })),
    };
  });

  const course = firstRelation<any>(act.courses);

  return {
    activity_id: act.id,
    title: resolveContentTitle(act),
    description: act.description || null,
    course_id: act.course_id,
    course_name: resolveCourseName(course),
    activity_type: (act.activity_type as ActivityType) || "practice",
    feedback_policy:
      (act.feedback_policy as FeedbackPolicy) ||
      "immediate_with_explanation",
    max_attempts: Number(act.max_attempts || 0),
    time_limit_minutes:
      typeof act.time_limit_minutes === "number" ? act.time_limit_minutes : null,
    questions,
    active_attempt_id: null,
  };
}

async function startAttemptFromSupabase(
  activityId: string,
  idempotencyKey?: string
): Promise<StartAttemptResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user, profile } = context;

  if (!profile?.tenant_id) {
    throw new Error(
      "No se pudo resolver tu institución. Contacta a tu docente para completar tu perfil."
    );
  }

  const activity = await getStudentActivityFromSupabase(activityId);
  if (activity.questions.length === 0) {
    throw new Error("Esta actividad aún no tiene preguntas publicadas.");
  }

  const { data: existingAttempt, error: existingError } = await supabase
    .from("quiz_attempts")
    .select("id, attempt_number, started_at, status")
    .eq("student_id", user.id)
    .eq("activity_id", activityId)
    .eq("status", "in_progress")
    .maybeSingle();

  if (existingError) {
    throw new Error(
      `No se pudo verificar el intento activo: ${existingError.message}`
    );
  }

  if (existingAttempt) {
    return {
      attempt_id: existingAttempt.id,
      activity_id: activityId,
      attempt_number: Number(existingAttempt.attempt_number || 1),
      status: "in_progress",
      started_at: existingAttempt.started_at,
      questions: activity.questions,
    };
  }

  const { data: activitySectionRows, error: activitySectionError } = await supabase
    .from("activity_sections")
    .select("section_id")
    .eq("activity_id", activityId);
  if (activitySectionError) {
    throw new Error(
      `No se pudieron resolver las secciones de la actividad: ${activitySectionError.message}`
    );
  }

  const sectionIds = (activitySectionRows || []).map(
    (row: any) => row.section_id
  );

  const { data: enrollmentRows, error: enrollmentError } = sectionIds.length
    ? await supabase
        .from("enrollments")
        .select("id")
        .eq("student_id", user.id)
        .in("section_id", sectionIds)
        .limit(1)
    : { data: [], error: null };
  if (enrollmentError) {
    throw new Error(
      `No se pudo resolver tu matrícula: ${enrollmentError.message}`
    );
  }

  const enrollment = (enrollmentRows || [])[0];
  if (!enrollment) {
    throw new Error(
      "No estás matriculado en una sección asignada a esta actividad."
    );
  }

  const { count, error: countError } = await supabase
    .from("quiz_attempts")
    .select("id", { count: "exact", head: true })
    .eq("student_id", user.id)
    .eq("activity_id", activityId);
  if (countError) {
    throw new Error(
      `No se pudo calcular el número de intento: ${countError.message}`
    );
  }

  const { data: createdAttempt, error: insertError } = await supabase
    .from("quiz_attempts")
    .insert({
      tenant_id: profile.tenant_id,
      enrollment_id: enrollment.id,
      activity_id: activityId,
      student_id: user.id,
      attempt_number: (count || 0) + 1,
      status: "in_progress",
      started_at: new Date().toISOString(),
      idempotency_key: idempotencyKey || crypto.randomUUID(),
    })
    .select("id, attempt_number, started_at")
    .single();

  if (insertError || !createdAttempt) {
    throw new Error(
      insertError
        ? `No se pudo iniciar el intento: ${insertError.message}`
        : "No se pudo iniciar el intento."
    );
  }

  return {
    attempt_id: createdAttempt.id,
    activity_id: activityId,
    attempt_number: Number(createdAttempt.attempt_number || 1),
    status: "in_progress",
    started_at: createdAttempt.started_at,
    questions: activity.questions,
  };
}

async function submitAnswerFromSupabase(
  attemptId: string,
  payload: SubmitAnswerPayload
): Promise<SubmitAnswerResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user, profile } = context;

  if (!profile?.tenant_id) {
    throw new Error("No se pudo resolver tu institución para registrar la respuesta.");
  }

  const { data: attempt, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select("id, activity_id, attempt_number, student_id, status")
    .eq("id", attemptId)
    .maybeSingle();
  if (attemptError || !attempt) {
    throw new Error(
      attemptError
        ? `No se pudo validar el intento: ${attemptError.message}`
        : "El intento no existe o no está disponible."
    );
  }

  if (attempt.student_id && attempt.student_id !== user.id) {
    throw new Error("No puedes registrar respuestas en un intento de otro estudiante.");
  }

  const { data: option, error: optionError } = await supabase
    .from("question_options")
    .select("id, is_correct, question_id, questions(id, explanation, knowledge_component_id)")
    .eq("id", payload.selected_option_id)
    .maybeSingle();
  if (optionError || !option) {
    throw new Error(
      optionError
        ? `No se pudo validar la opción seleccionada: ${optionError.message}`
        : "La opción seleccionada no existe."
    );
  }

  const question = firstRelation<any>(option.questions);
  if (!question?.knowledge_component_id) {
    throw new Error("La pregunta no tiene un componente de conocimiento asociado.");
  }

  const { count: previousAnswers, error: previousError } = await supabase
    .from("answer_events")
    .select("id", { count: "exact", head: true })
    .eq("attempt_id", attemptId);
  if (previousError) {
    throw new Error(
      `No se pudo calcular la secuencia de la respuesta: ${previousError.message}`
    );
  }

  const { data: course } = await supabase
    .from("activities")
    .select("course_id")
    .eq("id", attempt.activity_id)
    .maybeSingle();

  const eventId = crypto.randomUUID();
  const key = idempotencyKeyOrDefault(
    payload.idempotency_key,
    crypto.randomUUID()
  );

  const { error: insertError } = await supabase.from("answer_events").insert({
    id: eventId,
    tenant_id: profile.tenant_id,
    attempt_id: attemptId,
    student_id: user.id,
    question_id: payload.question_id,
    knowledge_component_id: question.knowledge_component_id,
    selected_option_id: payload.selected_option_id,
    is_correct: option.is_correct === true,
    attempt_number: Number(attempt.attempt_number || 1),
    response_time_seconds: Math.max(0.01, payload.response_time_seconds),
    idempotency_key: key,
    activity_id: attempt.activity_id,
    course_id: course?.course_id || null,
    question_sequence: (previousAnswers || 0) + 1,
  });

  if (insertError) {
    throw new Error(`No se pudo registrar tu respuesta: ${insertError.message}`);
  }

  const { data: attemptAnswers, error: scoreError } = await supabase
    .from("answer_events")
    .select("is_correct")
    .eq("attempt_id", attemptId);
  if (scoreError) {
    throw new Error(
      `No se pudo recalcular el puntaje del intento: ${scoreError.message}`
    );
  }

  const scoreDisplay = observedPercentage(
    (attemptAnswers || []).filter((answer: any) => answer.is_correct === true)
      .length,
    (attemptAnswers || []).length
  );

  return {
    event_id: eventId,
    attempt_id: attemptId,
    question_id: payload.question_id,
    is_correct: option.is_correct === true,
    feedback: {
      title:
        option.is_correct === true
          ? "¡Excelente razonamiento!"
          : "Concepto por consolidar",
      explanation:
        typeof question.explanation === "string" && question.explanation.trim()
          ? question.explanation
          : null,
    },
    attempt_completed: false,
    next_question_index: null,
    current_score: scoreDisplay.value,
  };
}

function idempotencyKeyOrDefault(
  provided: string | undefined,
  fallback: string
): string {
  if (typeof provided === "string" && provided.trim()) return provided.trim();
  return fallback;
}

async function submitAttemptFromSupabase(
  attemptId: string
): Promise<SubmitAttemptResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user } = context;

  const { data: attempt, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select("id, activity_id, student_id, status")
    .eq("id", attemptId)
    .maybeSingle();
  if (attemptError || !attempt) {
    throw new Error(
      attemptError
        ? `No se pudo validar el intento: ${attemptError.message}`
        : "El intento no existe o no está disponible."
    );
  }

  if (attempt.student_id && attempt.student_id !== user.id) {
    throw new Error("No puedes finalizar un intento de otro estudiante.");
  }

  const { data: eventRows, error: eventError } = await supabase
    .from("answer_events")
    .select("is_correct")
    .eq("attempt_id", attemptId);
  if (eventError) {
    throw new Error(`No se pudieron leer tus respuestas: ${eventError.message}`);
  }

  const events = eventRows || [];
  const summary = summarizeAttempt({ events });
  if (!summary.has_evidence) {
    throw new Error(
      "Este intento no tiene respuestas registradas, por lo que no genera un resultado."
    );
  }

  const completedAt = new Date().toISOString();
  const { error: updateError } = await supabase
    .from("quiz_attempts")
    .update({
      status: "completed",
      completed_at: completedAt,
      submitted_at: completedAt,
      score: summary.score,
      total_questions: summary.total_questions,
      correct_answers: summary.correct_answers,
    })
    .eq("id", attemptId);
  if (updateError) {
    throw new Error(`No se pudo finalizar el intento: ${updateError.message}`);
  }

  return {
    attempt_id: attemptId,
    activity_id: attempt.activity_id,
    status: "completed",
    score: summary.score ?? 0,
    total_questions: summary.total_questions,
    correct_answers: summary.correct_answers,
    completed_at: completedAt,
  };
}

async function getAttemptResultsFromSupabase(
  attemptId: string
): Promise<AttemptResultsResponse> {
  const context = await getStudentSupabaseContext();
  const { supabase, user, profile } = context;

  const { data: attempt, error: attemptError } = await supabase
    .from("quiz_attempts")
    .select(
      "id, activity_id, student_id, started_at, completed_at, score, total_questions, correct_answers, status, activities(id, title, course_id, courses(id, name))"
    )
    .eq("id", attemptId)
    .maybeSingle();
  if (attemptError || !attempt) {
    throw new Error(
      attemptError
        ? `No se pudo cargar el intento: ${attemptError.message}`
        : "El intento no existe o no está disponible."
    );
  }

  if (attempt.student_id && attempt.student_id !== user.id) {
    throw new Error("No puedes consultar los resultados de otro estudiante.");
  }

  const { data: eventRows, error: eventError } = await supabase
    .from("answer_events")
    .select(
      "question_id, is_correct, selected_option_id, questions(id, question_text, explanation, knowledge_component_id, knowledge_components(id, name), question_options(id, option_text, is_correct, order_index))"
    )
    .eq("attempt_id", attemptId)
    .order("event_timestamp", { ascending: true });
  if (eventError) {
    throw new Error(`No se pudieron cargar tus respuestas: ${eventError.message}`);
  }

  const events = eventRows || [];
  const summary =
    events.length > 0
      ? summarizeAttempt({ events })
      : summarizeAttempt({
          declaredTotal: attempt.total_questions,
          declaredCorrect: attempt.correct_answers,
        });

  if (!summary.has_evidence) {
    throw new Error(
      "Este intento no tiene respuestas registradas, por lo que aún no genera resultados."
    );
  }

  const questions: AttemptQuestionReview[] = events.map((event: any) => {
    const question = firstRelation<any>(event.questions);
    const options = question?.question_options || [];
    const selectedOption = options.find(
      (option: any) => option.id === event.selected_option_id
    );
    const correctOption = options.find((option: any) => option.is_correct === true);
    const kc = firstRelation<any>(question?.knowledge_components);

    return {
      question_id: event.question_id,
      question_text: question?.question_text || "Pregunta no disponible",
      knowledge_component_id: question?.knowledge_component_id || "",
      knowledge_component_name: resolveKnowledgeComponentName(kc),
      selected_option_id: event.selected_option_id || null,
      selected_option_text: selectedOption?.option_text || "Sin respuesta registrada",
      is_correct: event.is_correct === true,
      correct_option_id: correctOption?.id || null,
      correct_option_text: correctOption?.option_text || null,
      explanation:
        typeof question?.explanation === "string" ? question.explanation : null,
    };
  });

  const kcGroups = new Map<
    string,
    { name: string; total: number; correct: number }
  >();
  for (const question of questions) {
    const current = kcGroups.get(question.knowledge_component_id) || {
      name: question.knowledge_component_name,
      total: 0,
      correct: 0,
    };
    current.total += 1;
    if (question.is_correct) current.correct += 1;
    kcGroups.set(question.knowledge_component_id, current);
  }

  const kc_summaries: KCResultSummary[] = Array.from(kcGroups.entries()).map(
    ([kcId, group]) => ({
      knowledge_component_id: kcId,
      knowledge_component_name: group.name,
      total_questions: group.total,
      correct_answers: group.correct,
      mastery_rate: Number(((group.correct / group.total) * 100).toFixed(1)),
    })
  );

  const activity = firstRelation<any>(attempt.activities);
  const course = firstRelation<any>(activity?.courses);

  return {
    attempt_id: attemptId,
    activity_id: attempt.activity_id,
    activity_title: resolveContentTitle(activity),
    course_name: resolveCourseName(course),
    student_id: user.id,
    student_name:
      profile?.full_name || studentDisplayName(context),
    started_at: attempt.started_at,
    completed_at: attempt.completed_at,
    score: summary.score ?? 0,
    total_questions: summary.total_questions,
    correct_answers: summary.correct_answers,
    questions,
    kc_summaries,
  };
}

export const studentLearningApi = learningApi;
