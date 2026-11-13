/**
 * Teacher Telemetry, Dashboard, Roster & Spaced Retention Reports API Client
 * Connects Next.js web application to FastAPI /api/v1/teacher endpoints.
 */

import { apiFetch, isBackendConfigured } from "./client";
import {
  buildProficiencyDistribution,
  classifyMastery,
  observedPercentage,
  resolveCourseName,
  resolveKnowledgeComponentName,
} from "@/lib/data-provenance";

export interface ProficiencyDistributionItem {
  requiring_reinforcement: number;
  in_progress: number;
  consolidated: number;
  /** Students without enough answer events to be classified. */
  insufficient_evidence?: number;
}

export interface TeacherStudentQuickItem {
  id: string;
  name: string;
  code: string | null;
  section_name: string;
  /** Null when the student has no observed answers. */
  accuracy: number | null;
  weak_kc_name: string | null;
  sample_size: number;
}

export interface TeacherSectionSummary {
  id: string;
  name: string;
  course_id: string;
  course_name: string;
  students_count: number;
}

export interface TeacherDashboardResponse {
  teacher_name: string;
  total_students: number;
  total_courses: number;
  total_sections: number;
  published_activities: number;
  total_attempts: number;
  /** Null when no answer events exist for the selected roster. */
  average_accuracy: number | null;
  /** Denominator backing `average_accuracy` when available. */
  total_answers?: number;
  active_recommendations_count: number;
  completed_reviews_count: number;
  proficiency_distribution: ProficiencyDistributionItem;
  students_requiring_reinforcement: TeacherStudentQuickItem[];
  students_on_track: TeacherStudentQuickItem[];
  sections: TeacherSectionSummary[];
}

export interface TeacherKCDetailItem {
  id: string;
  name: string;
  difficulty_prior: number;
  microcontents_count: number;
  questions_count: number;
}

export interface TeacherUnitItem {
  id: string;
  title: string;
  order_index: number;
  kcs: TeacherKCDetailItem[];
}

export interface TeacherCourseDetail {
  course_id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
  sections: TeacherSectionSummary[];
  units: TeacherUnitItem[];
  published_activities_count: number;
  microcontents_count: number;
}

export type TeacherStudentStatus =
  | "Consolidado"
  | "En proceso"
  | "Refuerzo sugerido"
  | "Sin evidencia suficiente";

export interface TeacherStudentRecord {
  student_id: string;
  student_code: string | null;
  full_name: string;
  section_id: string;
  section_name: string;
  completed_activities: number;
  total_answers: number;
  /** Null when the student has no observed answers. */
  observed_accuracy: number | null;
  status: TeacherStudentStatus;
  active_recommendations_count: number;
  last_active_at: string | null;
}

export interface TeacherAiInsight {
  title: string;
  message: string;
  recommended_focus_kc: string | null;
}

export interface SectionReportsMetric {
  section_id: string;
  section_name: string;
  students_count: number;
  completed_attempts: number;
  /** Null when no completed attempts with a score exist for the section. */
  average_score: number | null;
  reviews_completed: number;
}

export interface HeatmapKCItem {
  id: string;
  name: string;
}

export interface HeatmapStudentRow {
  student_id: string;
  student_name: string;
  student_code: string | null;
  section_name: string;
  kcs: Record<string, { accuracy: number; status: string }>;
}

export interface HeatmapData {
  kcs: HeatmapKCItem[];
  rows: HeatmapStudentRow[];
}

export interface KCPerformanceItem {
  kc_id: string;
  kc_name: string;
  /** Null when no student answered this KC. */
  average_accuracy: number | null;
  students_evaluated: number;
}

export interface GrowthTrajectoryItem {
  period: string;
  /** Observed weekly accuracy (0-100). Null when the week has no answers. */
  historical_observed: number | null;
  /** Number of answer_events backing the observation. */
  sample_size: number;
}

export interface TeacherReportsResponse {
  /** Null when no validated model produced an insight. */
  ai_insight: TeacherAiInsight | null;
  sections_summary: SectionReportsMetric[];
  mastery_heatmap: HeatmapData;
  kc_performance_overview: KCPerformanceItem[];
  retention_growth_trajectory: GrowthTrajectoryItem[];
}

export async function getTeacherDashboard(
  sectionId?: string
): Promise<TeacherDashboardResponse> {
  if (isBackendConfigured()) {
    try {
      const query = new URLSearchParams();
      if (sectionId) query.set("section_id", sectionId);
      const qs = query.toString();
      return await apiFetch<TeacherDashboardResponse>(
        `/api/v1/teacher/dashboard${qs ? `?${qs}` : ""}`,
        { method: "GET" },
        "teacher"
      );
    } catch (e) {
      console.warn("FastAPI unreachable, fallback to Supabase for teacher dashboard:", e);
    }
  }
  return await getTeacherDashboardFromSupabase(sectionId);
}

export async function getTeacherCourses(): Promise<TeacherCourseDetail[]> {
  if (isBackendConfigured()) {
    try {
      return await apiFetch<TeacherCourseDetail[]>(
        "/api/v1/teacher/courses",
        { method: "GET" },
        "teacher"
      );
    } catch (e) {
      console.warn("FastAPI unreachable, fallback to Supabase for teacher courses:", e);
    }
  }
  return await getTeacherCoursesFromSupabase();
}

export async function getTeacherStudents(
  sectionId?: string,
  search?: string
): Promise<TeacherStudentRecord[]> {
  if (isBackendConfigured()) {
    try {
      const query = new URLSearchParams();
      if (sectionId) query.set("section_id", sectionId);
      if (search) query.set("search", search);
      const qs = query.toString();
      return await apiFetch<TeacherStudentRecord[]>(
        `/api/v1/teacher/students${qs ? `?${qs}` : ""}`,
        { method: "GET" },
        "teacher"
      );
    } catch (e) {
      console.warn("FastAPI unreachable, fallback to Supabase for teacher students:", e);
    }
  }
  return await getTeacherStudentsFromSupabase(sectionId, search);
}

export async function getTeacherReports(
  sectionId?: string,
  courseId?: string
): Promise<TeacherReportsResponse> {
  if (isBackendConfigured()) {
    try {
      const query = new URLSearchParams();
      if (sectionId) query.set("section_id", sectionId);
      if (courseId) query.set("course_id", courseId);
      const qs = query.toString();
      return await apiFetch<TeacherReportsResponse>(
        `/api/v1/teacher/reports${qs ? `?${qs}` : ""}`,
        { method: "GET" },
        "teacher"
      );
    } catch (e) {
      console.warn("FastAPI unreachable, fallback to Supabase for teacher reports:", e);
    }
  }
  return await getTeacherReportsFromSupabase(sectionId, courseId);
}

interface TeacherSupabaseContext {
  supabase: any;
  user: { id: string; user_metadata?: Record<string, unknown> };
  profile: { id: string; tenant_id: string; full_name: string | null } | null;
}

function firstRelation<T>(value: T | T[] | null | undefined): T | null {
  if (Array.isArray(value)) return value.length > 0 ? value[0] : null;
  return value ?? null;
}

async function getTeacherSupabaseContext(): Promise<TeacherSupabaseContext> {
  const { createClient } = await import("@/lib/supabase/client");
  const supabase = createClient();
  const {
    data: { user },
    error,
  } = await supabase.auth.getUser();

  if (error || !user) {
    throw new Error(
      "No hay una sesión autenticada. Inicia sesión para consultar la telemetría docente."
    );
  }

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("id, tenant_id, full_name")
    .eq("id", user.id)
    .maybeSingle();

  if (profileError) {
    throw new Error(
      `No se pudo cargar el perfil docente: ${profileError.message}`
    );
  }

  return { supabase, user, profile };
}

function teacherDisplayName(context: TeacherSupabaseContext): string {
  const metadataName = context.user.user_metadata?.full_name;
  if (context.profile?.full_name) return context.profile.full_name;
  if (typeof metadataName === "string" && metadataName.trim()) {
    return metadataName.trim();
  }
  return "Docente";
}

function statusLabel(status: ReturnType<typeof classifyMastery>): TeacherStudentStatus {
  switch (status) {
    case "consolidated":
      return "Consolidado";
    case "in_progress":
      return "En proceso";
    case "requiring_reinforcement":
      return "Refuerzo sugerido";
    default:
      return "Sin evidencia suficiente";
  }
}

interface StudentAnswerStats {
  total: number;
  correct: number;
  accuracy: number | null;
  byKc: Map<
    string,
    { kcName: string; total: number; correct: number }
  >;
}

function buildStudentAnswerStats(
  studentIds: string[],
  answers: any[],
  kcNameById: Map<string, string>
): Map<string, StudentAnswerStats> {
  const statsById = new Map<string, StudentAnswerStats>();

  for (const studentId of studentIds) {
    statsById.set(studentId, {
      total: 0,
      correct: 0,
      accuracy: null,
      byKc: new Map(),
    });
  }

  for (const answer of answers) {
    const stats = statsById.get(answer.student_id);
    if (!stats) continue;
    stats.total += 1;
    if (answer.is_correct === true) stats.correct += 1;

    const kcId = answer.knowledge_component_id;
    if (kcId) {
      const kcStats = stats.byKc.get(kcId) || {
        kcName: kcNameById.get(kcId) || "Componente sin nombre",
        total: 0,
        correct: 0,
      };
      kcStats.total += 1;
      if (answer.is_correct === true) kcStats.correct += 1;
      stats.byKc.set(kcId, kcStats);
    }
  }

  for (const stats of Array.from(statsById.values())) {
    stats.accuracy =
      stats.total > 0
        ? Number(((stats.correct / stats.total) * 100).toFixed(1))
        : null;
  }

  return statsById;
}

function weakestKcName(stats: StudentAnswerStats | undefined): string | null {
  if (!stats) return null;
  let weakest: { name: string; accuracy: number } | null = null;

  for (const kcStats of Array.from(stats.byKc.values())) {
    if (kcStats.total === 0) continue;
    const accuracy = (kcStats.correct / kcStats.total) * 100;
    if (!weakest || accuracy < weakest.accuracy) {
      weakest = { name: kcStats.kcName, accuracy };
    }
  }

  return weakest?.name || null;
}

async function getTeacherDashboardFromSupabase(
  sectionId?: string
): Promise<TeacherDashboardResponse> {
  const context = await getTeacherSupabaseContext();
  const { supabase } = context;

  const { data: sectionRows, error: sectionError } = await supabase
    .from("sections")
    .select("id, name, course_id, courses(id, name)")
    .order("name", { ascending: true });
  if (sectionError) {
    throw new Error(`No se pudieron cargar tus secciones: ${sectionError.message}`);
  }

  const allSections = sectionRows || [];
  const selectedSections = sectionId
    ? allSections.filter((section: any) => section.id === sectionId)
    : allSections;
  const selectedSectionIds = selectedSections.map((section: any) => section.id);

  const { data: enrollmentRows, error: enrollmentError } = selectedSectionIds.length
    ? await supabase
        .from("enrollments")
        .select("student_id, section_id")
        .in("section_id", selectedSectionIds)
    : { data: [], error: null };
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar las matrículas: ${enrollmentError.message}`);
  }

  const enrollments = enrollmentRows || [];
  const rosterIds: string[] = Array.from(
    new Set(enrollments.map((enrollment: any) => enrollment.student_id))
  );
  const sectionByStudent = new Map<string, any>();
  for (const enrollment of enrollments) {
    if (!sectionByStudent.has(enrollment.student_id)) {
      sectionByStudent.set(
        enrollment.student_id,
        selectedSections.find(
          (section: any) => section.id === enrollment.section_id
        )
      );
    }
  }

  const { data: profileRows, error: profileError } = rosterIds.length
    ? await supabase
        .from("profiles")
        .select("id, full_name, student_code, role")
        .in("id", rosterIds)
        .eq("role", "student")
    : { data: [], error: null };
  if (profileError) {
    throw new Error(`No se pudo cargar la nómina: ${profileError.message}`);
  }

  const students = profileRows || [];

  const { data: kcRows, error: kcError } = await supabase
    .from("knowledge_components")
    .select("id, name");
  if (kcError) {
    throw new Error(
      `No se pudieron cargar los componentes de conocimiento: ${kcError.message}`
    );
  }

  const kcNameById = new Map<string, string>(
    (kcRows || []).map((kc: any) => [kc.id, resolveKnowledgeComponentName(kc)])
  );

  const { data: answerRows, error: answerError } = rosterIds.length
    ? await supabase
        .from("answer_events")
        .select("student_id, knowledge_component_id, is_correct")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (answerError) {
    throw new Error(`No se pudieron cargar las respuestas: ${answerError.message}`);
  }

  const answers = answerRows || [];
  const statsById = buildStudentAnswerStats(
    rosterIds,
    answers,
    kcNameById
  );

  const { data: attemptRows, error: attemptError } = rosterIds.length
    ? await supabase
        .from("quiz_attempts")
        .select("id, student_id, status")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (attemptError) {
    throw new Error(`No se pudieron cargar los intentos: ${attemptError.message}`);
  }

  const attempts = attemptRows || [];
  const completedAttempts = attempts.filter(
    (attempt: any) => attempt.status === "completed"
  );

  const { data: recommendationRows, error: recommendationError } = rosterIds.length
    ? await supabase
        .from("recommendations")
        .select("id, student_id, status")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (recommendationError) {
    throw new Error(
      `No se pudieron cargar las recomendaciones: ${recommendationError.message}`
    );
  }

  const recommendations = recommendationRows || [];

  const courseMap = new Map<string, any>();
  for (const section of allSections) {
    const course = firstRelation<any>(section.courses);
    if (course && !courseMap.has(course.id)) courseMap.set(course.id, course);
  }
  const courseIds = Array.from(courseMap.keys());

  const { data: activityRows, error: activityError } = courseIds.length
    ? await supabase
        .from("activities")
        .select("id, course_id")
        .in("course_id", courseIds)
        .eq("status", "published")
    : { data: [], error: null };
  if (activityError) {
    throw new Error(
      `No se pudieron cargar las actividades publicadas: ${activityError.message}`
    );
  }

  const publishedActivities = activityRows || [];

  const enrollmentCountBySection = new Map<string, number>();
  const { data: allEnrollmentRows } = allSections.length
    ? await supabase
        .from("enrollments")
        .select("section_id")
        .in(
          "section_id",
          allSections.map((section: any) => section.id)
        )
    : { data: [] };
  for (const enrollment of allEnrollmentRows || []) {
    enrollmentCountBySection.set(
      enrollment.section_id,
      (enrollmentCountBySection.get(enrollment.section_id) || 0) + 1
    );
  }

  const distributionRows = students.map((student: any) => {
    const stats = statsById.get(student.id);
    return {
      accuracy: stats?.accuracy ?? null,
      sampleSize: stats?.total ?? 0,
    };
  });
  const proficiency_distribution = buildProficiencyDistribution(distributionRows);

  const quickItem = (student: any): TeacherStudentQuickItem => {
    const stats = statsById.get(student.id);
    const section = sectionByStudent.get(student.id);
    return {
      id: student.id,
      name: student.full_name || "Estudiante",
      code: student.student_code || null,
      section_name: section?.name || "Sección sin nombre",
      accuracy: stats?.accuracy ?? null,
      weak_kc_name: weakestKcName(stats),
      sample_size: stats?.total ?? 0,
    };
  };

  const studentsRequiringReinforcement = students
    .filter((student: any) => {
      const stats = statsById.get(student.id);
      return (
        classifyMastery(stats?.accuracy, stats?.total) ===
        "requiring_reinforcement"
      );
    })
    .map(quickItem);

  const studentsOnTrack = students
    .filter((student: any) => {
      const stats = statsById.get(student.id);
      return classifyMastery(stats?.accuracy, stats?.total) === "consolidated";
    })
    .map(quickItem);

  const totalAnswers = answers.length;
  const correctAnswers = answers.filter(
    (answer: any) => answer.is_correct === true
  ).length;
  const accuracyDisplay = observedPercentage(correctAnswers, totalAnswers);

  return {
    teacher_name: teacherDisplayName(context),
    total_students: students.length,
    total_courses: courseIds.length,
    total_sections: allSections.length,
    published_activities: publishedActivities.length,
    total_attempts: completedAttempts.length,
    average_accuracy: accuracyDisplay.value,
    total_answers: totalAnswers,
    active_recommendations_count: recommendations.filter(
      (recommendation: any) => recommendation.status === "pending"
    ).length,
    completed_reviews_count: recommendations.filter(
      (recommendation: any) => recommendation.status === "completed"
    ).length,
    proficiency_distribution,
    students_requiring_reinforcement: studentsRequiringReinforcement,
    students_on_track: studentsOnTrack,
    sections: allSections.map((section: any) => {
      const course = firstRelation<any>(section.courses);
      return {
        id: section.id,
        name: section.name || "Sección sin nombre",
        course_id: section.course_id,
        course_name: resolveCourseName(course),
        students_count: enrollmentCountBySection.get(section.id) || 0,
      };
    }),
  };
}

async function getTeacherCoursesFromSupabase(): Promise<TeacherCourseDetail[]> {
  const context = await getTeacherSupabaseContext();
  const { supabase } = context;

  const { data: courseRows, error: courseError } = await supabase
    .from("courses")
    .select("id, code, name, description, is_active")
    .order("name", { ascending: true });
  if (courseError) {
    throw new Error(`No se pudieron cargar los cursos: ${courseError.message}`);
  }

  const courses = courseRows || [];
  const courseIds = courses.map((course: any) => course.id);

  const { data: sectionRows, error: sectionError } = courseIds.length
    ? await supabase
        .from("sections")
        .select("id, name, course_id")
        .in("course_id", courseIds)
        .order("name", { ascending: true })
    : { data: [], error: null };
  if (sectionError) {
    throw new Error(`No se pudieron cargar las secciones: ${sectionError.message}`);
  }

  const sections = sectionRows || [];
  const sectionIds = sections.map((section: any) => section.id);

  const { data: enrollmentRows, error: enrollmentError } = sectionIds.length
    ? await supabase
        .from("enrollments")
        .select("section_id")
        .in("section_id", sectionIds)
    : { data: [], error: null };
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar las matrículas: ${enrollmentError.message}`);
  }

  const enrollmentCountBySection = new Map<string, number>();
  for (const enrollment of enrollmentRows || []) {
    enrollmentCountBySection.set(
      enrollment.section_id,
      (enrollmentCountBySection.get(enrollment.section_id) || 0) + 1
    );
  }

  const { data: unitRows, error: unitError } = courseIds.length
    ? await supabase
        .from("units")
        .select("id, course_id, title, order_index")
        .in("course_id", courseIds)
        .order("order_index", { ascending: true })
    : { data: [], error: null };
  if (unitError) {
    throw new Error(`No se pudieron cargar las unidades: ${unitError.message}`);
  }

  const units = unitRows || [];
  const unitIds = units.map((unit: any) => unit.id);

  const { data: kcRows, error: kcError } = unitIds.length
    ? await supabase
        .from("knowledge_components")
        .select("id, unit_id, name, difficulty_prior")
        .in("unit_id", unitIds)
    : { data: [], error: null };
  if (kcError) {
    throw new Error(
      `No se pudieron cargar los componentes de conocimiento: ${kcError.message}`
    );
  }

  const kcs = kcRows || [];
  const kcIds = kcs.map((kc: any) => kc.id);

  const { data: microcontentRows, error: microcontentError } = kcIds.length
    ? await supabase
        .from("microcontents")
        .select("id, knowledge_component_id")
        .in("knowledge_component_id", kcIds)
    : { data: [], error: null };
  if (microcontentError) {
    throw new Error(
      `No se pudieron cargar los microcontenidos: ${microcontentError.message}`
    );
  }

  const { data: questionRows, error: questionError } = kcIds.length
    ? await supabase
        .from("questions")
        .select("id, knowledge_component_id")
        .in("knowledge_component_id", kcIds)
    : { data: [], error: null };
  if (questionError) {
    throw new Error(`No se pudieron cargar las preguntas: ${questionError.message}`);
  }

  const { data: activityRows, error: activityError } = courseIds.length
    ? await supabase
        .from("activities")
        .select("id, course_id")
        .in("course_id", courseIds)
        .eq("status", "published")
    : { data: [], error: null };
  if (activityError) {
    throw new Error(
      `No se pudieron cargar las actividades publicadas: ${activityError.message}`
    );
  }

  const microcontentCountByKc = new Map<string, number>();
  for (const microcontent of microcontentRows || []) {
    microcontentCountByKc.set(
      microcontent.knowledge_component_id,
      (microcontentCountByKc.get(microcontent.knowledge_component_id) || 0) + 1
    );
  }

  const questionCountByKc = new Map<string, number>();
  for (const question of questionRows || []) {
    questionCountByKc.set(
      question.knowledge_component_id,
      (questionCountByKc.get(question.knowledge_component_id) || 0) + 1
    );
  }

  const activitiesByCourse = new Map<string, number>();
  for (const activity of activityRows || []) {
    activitiesByCourse.set(
      activity.course_id,
      (activitiesByCourse.get(activity.course_id) || 0) + 1
    );
  }

  return courses.map((course: any) => {
    const courseSections = sections
      .filter((section: any) => section.course_id === course.id)
      .map((section: any) => ({
        id: section.id,
        name: section.name,
        course_id: course.id,
        course_name: resolveCourseName(course),
        students_count: enrollmentCountBySection.get(section.id) || 0,
      }));

    const courseUnits = units
      .filter((unit: any) => unit.course_id === course.id)
      .map((unit: any) => ({
        id: unit.id,
        title: unit.title,
        order_index: unit.order_index,
        kcs: kcs
          .filter((kc: any) => kc.unit_id === unit.id)
          .map((kc: any) => ({
            id: kc.id,
            name: resolveKnowledgeComponentName(kc),
            difficulty_prior: Number(kc.difficulty_prior || 0),
            microcontents_count: microcontentCountByKc.get(kc.id) || 0,
            questions_count: questionCountByKc.get(kc.id) || 0,
          })),
      }));

    return {
      course_id: course.id,
      code: course.code || "",
      name: resolveCourseName(course),
      description: course.description || null,
      is_active: course.is_active === true,
      sections: courseSections,
      units: courseUnits,
      published_activities_count: activitiesByCourse.get(course.id) || 0,
      microcontents_count: courseUnits.reduce(
        (sum: number, unit: any) =>
          sum +
          unit.kcs.reduce(
            (kcSum: number, kc: any) => kcSum + kc.microcontents_count,
            0
          ),
        0
      ),
    };
  });
}

async function getTeacherStudentsFromSupabase(
  sectionId?: string,
  search?: string
): Promise<TeacherStudentRecord[]> {
  const context = await getTeacherSupabaseContext();
  const { supabase } = context;

  const { data: enrollmentRows, error: enrollmentError } = sectionId
    ? await supabase
        .from("enrollments")
        .select("student_id, section_id, sections(id, name)")
        .eq("section_id", sectionId)
    : await supabase
        .from("enrollments")
        .select("student_id, section_id, sections(id, name)");
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar las matrículas: ${enrollmentError.message}`);
  }

  const enrollments = enrollmentRows || [];
  const rosterIds: string[] = Array.from(
    new Set(enrollments.map((enrollment: any) => enrollment.student_id))
  );
  const sectionByStudent = new Map<string, any>();
  for (const enrollment of enrollments) {
    if (!sectionByStudent.has(enrollment.student_id)) {
      const section = firstRelation<any>(enrollment.sections);
      if (section) sectionByStudent.set(enrollment.student_id, section);
    }
  }

  const { data: profileRows, error: profileError } = rosterIds.length
    ? await supabase
        .from("profiles")
        .select("id, full_name, student_code")
        .in("id", rosterIds)
        .eq("role", "student")
        .order("student_code", { ascending: true })
    : { data: [], error: null };
  if (profileError) {
    throw new Error(`No se pudo cargar la nómina: ${profileError.message}`);
  }

  const profiles = profileRows || [];

  const { data: answerRows, error: answerError } = rosterIds.length
    ? await supabase
        .from("answer_events")
        .select("student_id, is_correct, event_timestamp")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (answerError) {
    throw new Error(`No se pudieron cargar las respuestas: ${answerError.message}`);
  }

  const answers = answerRows || [];

  const { data: attemptRows, error: attemptError } = rosterIds.length
    ? await supabase
        .from("quiz_attempts")
        .select("id, student_id, activity_id, status, completed_at")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (attemptError) {
    throw new Error(`No se pudieron cargar los intentos: ${attemptError.message}`);
  }

  const attempts = attemptRows || [];

  const { data: recommendationRows, error: recommendationError } = rosterIds.length
    ? await supabase
        .from("recommendations")
        .select("student_id, status")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (recommendationError) {
    throw new Error(
      `No se pudieron cargar las recomendaciones: ${recommendationError.message}`
    );
  }

  const recommendations = recommendationRows || [];

  const answersByStudent = new Map<string, any[]>();
  for (const answer of answers) {
    const list = answersByStudent.get(answer.student_id) || [];
    list.push(answer);
    answersByStudent.set(answer.student_id, list);
  }

  const attemptsByStudent = new Map<string, any[]>();
  for (const attempt of attempts) {
    const list = attemptsByStudent.get(attempt.student_id) || [];
    list.push(attempt);
    attemptsByStudent.set(attempt.student_id, list);
  }

  const recommendationsByStudent = new Map<string, any[]>();
  for (const recommendation of recommendations) {
    const list = recommendationsByStudent.get(recommendation.student_id) || [];
    list.push(recommendation);
    recommendationsByStudent.set(recommendation.student_id, list);
  }

  const records: TeacherStudentRecord[] = profiles.map((profile: any) => {
    const studentAnswers = answersByStudent.get(profile.id) || [];
    const studentAttempts = attemptsByStudent.get(profile.id) || [];
    const studentRecommendations = recommendationsByStudent.get(profile.id) || [];
    const total = studentAnswers.length;
    const correct = studentAnswers.filter(
      (answer: any) => answer.is_correct === true
    ).length;
    const accuracy =
      total > 0 ? Number(((correct / total) * 100).toFixed(1)) : null;
    const mastery = classifyMastery(accuracy, total);
    const section = sectionByStudent.get(profile.id);

    const completedActivityIds = new Set(
      studentAttempts
        .filter((attempt: any) => attempt.status === "completed")
        .map((attempt: any) => attempt.activity_id)
    );

    const activityDates = studentAnswers
      .map((answer: any) => answer.event_timestamp)
      .filter(Boolean)
      .sort();
    const attemptDates = studentAttempts
      .map((attempt: any) => attempt.completed_at)
      .filter(Boolean)
      .sort();
    const lastCandidate =
      activityDates[activityDates.length - 1] ||
      attemptDates[attemptDates.length - 1] ||
      null;

    return {
      student_id: profile.id,
      student_code: profile.student_code || null,
      full_name: profile.full_name || "Estudiante",
      section_id: section?.id || "",
      section_name: section?.name || "Sección sin nombre",
      completed_activities: completedActivityIds.size,
      total_answers: total,
      observed_accuracy: accuracy,
      status: statusLabel(mastery),
      active_recommendations_count: studentRecommendations.filter(
        (recommendation: any) => recommendation.status === "pending"
      ).length,
      last_active_at: lastCandidate || null,
    };
  });

  if (search) {
    const q = search.toLowerCase();
    return records.filter(
      (record) =>
        record.full_name.toLowerCase().includes(q) ||
        (record.student_code &&
          record.student_code.toLowerCase().includes(q))
    );
  }

  return records;
}

function startOfWeek(date: Date): Date {
  const result = new Date(date);
  const day = result.getDay();
  const diff = day === 0 ? -6 : 1 - day;
  result.setDate(result.getDate() + diff);
  result.setHours(0, 0, 0, 0);
  return result;
}

function weekKey(date: Date): string {
  return date.toISOString().slice(0, 10);
}

async function getTeacherReportsFromSupabase(
  sectionId?: string,
  _courseId?: string
): Promise<TeacherReportsResponse> {
  const context = await getTeacherSupabaseContext();
  const { supabase } = context;

  const { data: kcRows, error: kcError } = await supabase
    .from("knowledge_components")
    .select("id, name");
  if (kcError) {
    throw new Error(
      `No se pudieron cargar los componentes de conocimiento: ${kcError.message}`
    );
  }

  const kcList: HeatmapKCItem[] = (kcRows || []).map((kc: any) => ({
    id: kc.id,
    name: resolveKnowledgeComponentName(kc),
  }));

  const { data: sectionRows, error: sectionError } = sectionId
    ? await supabase
        .from("sections")
        .select("id, name")
        .eq("id", sectionId)
    : await supabase.from("sections").select("id, name").order("name");
  if (sectionError) {
    throw new Error(`No se pudieron cargar las secciones: ${sectionError.message}`);
  }

  const sections = sectionRows || [];
  const sectionIds = sections.map((section: any) => section.id);

  const { data: enrollmentRows, error: enrollmentError } = sectionIds.length
    ? await supabase
        .from("enrollments")
        .select("student_id, section_id")
        .in("section_id", sectionIds)
    : { data: [], error: null };
  if (enrollmentError) {
    throw new Error(`No se pudieron cargar las matrículas: ${enrollmentError.message}`);
  }

  const enrollments = enrollmentRows || [];
  const rosterIds: string[] = Array.from(
    new Set(enrollments.map((enrollment: any) => enrollment.student_id))
  );
  const sectionByStudent = new Map<string, string>();
  for (const enrollment of enrollments) {
    if (!sectionByStudent.has(enrollment.student_id)) {
      const section = sections.find(
        (candidate: any) => candidate.id === enrollment.section_id
      );
      if (section) sectionByStudent.set(enrollment.student_id, section.name);
    }
  }

  const { data: profileRows, error: profileError } = rosterIds.length
    ? await supabase
        .from("profiles")
        .select("id, full_name, student_code")
        .in("id", rosterIds)
        .eq("role", "student")
        .order("student_code", { ascending: true })
    : { data: [], error: null };
  if (profileError) {
    throw new Error(`No se pudo cargar la nómina: ${profileError.message}`);
  }

  const profiles = profileRows || [];

  const { data: answerRows, error: answerError } = rosterIds.length
    ? await supabase
        .from("answer_events")
        .select("student_id, knowledge_component_id, is_correct, event_timestamp")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (answerError) {
    throw new Error(`No se pudieron cargar las respuestas: ${answerError.message}`);
  }

  const answers = answerRows || [];

  const { data: attemptRows, error: attemptError } = rosterIds.length
    ? await supabase
        .from("quiz_attempts")
        .select("id, student_id, status, score, completed_at")
        .in("student_id", rosterIds)
        .eq("status", "completed")
    : { data: [], error: null };
  if (attemptError) {
    throw new Error(`No se pudieron cargar los intentos: ${attemptError.message}`);
  }

  const attempts = attemptRows || [];

  const { data: recommendationRows, error: recommendationError } = rosterIds.length
    ? await supabase
        .from("recommendations")
        .select("student_id, status")
        .in("student_id", rosterIds)
    : { data: [], error: null };
  if (recommendationError) {
    throw new Error(
      `No se pudieron cargar las recomendaciones: ${recommendationError.message}`
    );
  }

  const recommendations = recommendationRows || [];

  const answersByStudentKc = new Map<string, any[]>();
  for (const answer of answers) {
    const key = `${answer.student_id}:${answer.knowledge_component_id}`;
    const list = answersByStudentKc.get(key) || [];
    list.push(answer);
    answersByStudentKc.set(key, list);
  }

  const rows: HeatmapStudentRow[] = profiles.map((profile: any) => {
    const kcsMap: Record<string, { accuracy: number; status: string }> = {};

    for (const kc of kcList) {
      const matching =
        answersByStudentKc.get(`${profile.id}:${kc.id}`) || [];
      if (matching.length === 0) continue;

      const correct = matching.filter(
        (answer: any) => answer.is_correct === true
      ).length;
      const accuracy = Number(
        ((correct / matching.length) * 100).toFixed(1)
      );

      kcsMap[kc.id] = {
        accuracy,
        status: classifyMastery(accuracy, matching.length),
      };
    }

    return {
      student_id: profile.id,
      student_name: profile.full_name || "Estudiante",
      student_code: profile.student_code || null,
      section_name: sectionByStudent.get(profile.id) || "Sección sin nombre",
      kcs: kcsMap,
    };
  });

  const kcOverview: KCPerformanceItem[] = kcList.map((kc) => {
    const matching = answers.filter(
      (answer: any) => answer.knowledge_component_id === kc.id
    );
    const correct = matching.filter(
      (answer: any) => answer.is_correct === true
    ).length;
    const evaluation = observedPercentage(correct, matching.length);

    return {
      kc_id: kc.id,
      kc_name: kc.name,
      average_accuracy: evaluation.value,
      students_evaluated: new Set(
        matching.map((answer: any) => answer.student_id)
      ).size,
    };
  });

  const attemptsBySection = new Map<string, any[]>();
  const recommendationsBySection = new Map<string, any[]>();
  for (const enrollment of enrollments) {
    const sectionAttempts =
      attemptsBySection.get(enrollment.section_id) || [];
    sectionAttempts.push(
      ...attempts.filter(
        (attempt: any) => attempt.student_id === enrollment.student_id
      )
    );
    attemptsBySection.set(enrollment.section_id, sectionAttempts);

    const sectionRecommendations =
      recommendationsBySection.get(enrollment.section_id) || [];
    sectionRecommendations.push(
      ...recommendations.filter(
        (recommendation: any) =>
          recommendation.student_id === enrollment.student_id
      )
    );
    recommendationsBySection.set(
      enrollment.section_id,
      sectionRecommendations
    );
  }

  const sections_summary: SectionReportsMetric[] = sections.map(
    (section: any) => {
      const sectionEnrollments = enrollments.filter(
        (enrollment: any) => enrollment.section_id === section.id
      );
      const sectionAttempts = attemptsBySection.get(section.id) || [];
      const scoredAttempts = sectionAttempts.filter(
        (attempt: any) => typeof attempt.score === "number"
      );
      const sectionRecommendations =
        recommendationsBySection.get(section.id) || [];

      return {
        section_id: section.id,
        section_name: section.name || "Sección sin nombre",
        students_count: new Set(
          sectionEnrollments.map(
            (enrollment: any) => enrollment.student_id
          )
        ).size,
        completed_attempts: sectionAttempts.length,
        average_score:
          scoredAttempts.length > 0
            ? Number(
                (
                  scoredAttempts.reduce(
                    (sum: number, attempt: any) =>
                      sum + Number(attempt.score),
                    0
                  ) / scoredAttempts.length
                ).toFixed(1)
              )
            : null,
        reviews_completed: sectionRecommendations.filter(
          (recommendation: any) => recommendation.status === "completed"
        ).length,
      };
    }
  );

  const weekBuckets = new Map<
    string,
    { period: string; total: number; correct: number }
  >();
  const currentWeek = startOfWeek(new Date());
  for (let offset = 5; offset >= 0; offset -= 1) {
    const weekStart = new Date(currentWeek);
    weekStart.setDate(weekStart.getDate() - offset * 7);
    const key = weekKey(weekStart);
    weekBuckets.set(key, {
      period: `Semana del ${new Intl.DateTimeFormat("es-PE", {
        day: "2-digit",
        month: "short",
      }).format(weekStart)}`,
      total: 0,
      correct: 0,
    });
  }

  for (const answer of answers) {
    if (!answer.event_timestamp) continue;
    const eventDate = new Date(answer.event_timestamp);
    if (Number.isNaN(eventDate.getTime())) continue;
    const key = weekKey(startOfWeek(eventDate));
    const bucket = weekBuckets.get(key);
    if (!bucket) continue;
    bucket.total += 1;
    if (answer.is_correct === true) bucket.correct += 1;
  }

  const trajectory: GrowthTrajectoryItem[] = Array.from(
    weekBuckets.values()
  ).map((bucket) => ({
    period: bucket.period,
    historical_observed:
      bucket.total > 0
        ? Number(((bucket.correct / bucket.total) * 100).toFixed(1))
        : null,
    sample_size: bucket.total,
  }));

  return {
    ai_insight: null,
    sections_summary,
    mastery_heatmap: {
      kcs: kcList,
      rows,
    },
    kc_performance_overview: kcOverview,
    retention_growth_trajectory: trajectory,
  };
}
