/**
 * Teacher Telemetry, Dashboard, Roster & Spaced Retention Reports API Client
 * Connects Next.js web application to FastAPI /api/v1/teacher endpoints.
 */

import { apiFetch } from "./client";

export interface ProficiencyDistributionItem {
  requiring_reinforcement: number;
  in_progress: number;
  consolidated: number;
}

export interface TeacherStudentQuickItem {
  id: string;
  name: string;
  code: string | null;
  section_name: string;
  accuracy: number;
  weak_kc_name: string | null;
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
  average_accuracy: number;
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

export interface TeacherStudentRecord {
  student_id: string;
  student_code: string | null;
  full_name: string;
  section_id: string;
  section_name: string;
  completed_activities: number;
  total_answers: number;
  observed_accuracy: number;
  status: "Consolidado" | "En proceso" | "Refuerzo sugerido";
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
  average_score: number;
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
  average_accuracy: number;
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
  ai_insight: TeacherAiInsight;
  sections_summary: SectionReportsMetric[];
  mastery_heatmap: HeatmapData;
  kc_performance_overview: KCPerformanceItem[];
  retention_growth_trajectory: GrowthTrajectoryItem[];
}

export async function getTeacherDashboard(
  sectionId?: string
): Promise<TeacherDashboardResponse> {
  const query = new URLSearchParams();
  if (sectionId) query.set("section_id", sectionId);
  const qs = query.toString();
  return apiFetch<TeacherDashboardResponse>(
    `/api/v1/teacher/dashboard${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    "teacher"
  );
}

export async function getTeacherCourses(): Promise<TeacherCourseDetail[]> {
  return apiFetch<TeacherCourseDetail[]>(
    "/api/v1/teacher/courses",
    { method: "GET" },
    "teacher"
  );
}

export async function getTeacherStudents(
  sectionId?: string,
  search?: string
): Promise<TeacherStudentRecord[]> {
  const query = new URLSearchParams();
  if (sectionId) query.set("section_id", sectionId);
  if (search) query.set("search", search);
  const qs = query.toString();
  return apiFetch<TeacherStudentRecord[]>(
    `/api/v1/teacher/students${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    "teacher"
  );
}

export async function getTeacherReports(
  sectionId?: string,
  courseId?: string
): Promise<TeacherReportsResponse> {
  const query = new URLSearchParams();
  if (sectionId) query.set("section_id", sectionId);
  if (courseId) query.set("course_id", courseId);
  const qs = query.toString();
  return apiFetch<TeacherReportsResponse>(
    `/api/v1/teacher/reports${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    "teacher"
  );
}
