/**
 * Microcontents and Content Exposure Telemetry API Client
 * Connects Next.js web application to FastAPI /api/v1/microcontents endpoints.
 */

import { apiFetch } from "./client";

export interface MicrocontentSectionItem {
  id: number;
  navTitle: string;
  heading: string;
  tag: string;
  lead: string;
  durationMinutes: number;
  body?: string;
  formula?: string;
  analogy?: { title: string; text: string };
  keyTakeaways?: Array<{ label: string; text: string }>;
}

export interface MicrocontentBody {
  summary?: string;
  sections?: MicrocontentSectionItem[];
  /**
   * Explicit metadata key used to select a specialised diagram renderer.
   * The UI never infers a subject from the title (BL-03).
   */
  diagram_key?: string;
  [key: string]: unknown;
}

export interface MicrocontentDetailResponse {
  id: string;
  tenant_id: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  unit_id: string | null;
  unit_title: string | null;
  course_id: string | null;
  course_name: string | null;
  title: string;
  content_type: string;
  content_body: MicrocontentBody;
  estimated_duration_seconds: number;
  is_published: boolean;
  created_at: string;
}

export interface MicrocontentListItem {
  id: string;
  tenant_id: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  unit_title: string | null;
  course_name: string | null;
  title: string;
  content_type: string;
  estimated_duration_seconds: number;
  is_published: boolean;
  created_by: string;
  created_at: string;
}

export interface RecordExposureRequest {
  started_at: string;
  completed_at?: string | null;
  duration_seconds: number;
  active_reading_seconds?: number | null;
  completion_status?: "completed" | "abandoned";
  exposure_type?: "initial_study" | "review_study";
  session_id: string;
  idempotency_key: string;
  recommendation_id?: string | null;
  metadata?: Record<string, unknown>;
}

export interface RecordExposureResponse {
  event_id: string;
  microcontent_id: string;
  knowledge_component_id: string;
  exposure_type: string;
  recorded_at: string;
  recommendation_completed: boolean;
}

export interface MicrocontentCreatePayload {
  knowledge_component_id: string;
  title: string;
  content_type?: "text_summary" | "infographic_card" | "concept_map";
  content_body: Record<string, unknown>;
  estimated_duration_seconds?: number;
  is_published?: boolean;
}

export interface MicrocontentUpdatePayload {
  title?: string;
  content_body?: Record<string, unknown>;
  estimated_duration_seconds?: number;
  is_published?: boolean;
}

export async function getMicrocontent(id: string): Promise<MicrocontentDetailResponse> {
  return apiFetch<MicrocontentDetailResponse>(
    `/api/v1/microcontents/${id}`,
    { method: "GET" },
    "student"
  );
}

export async function recordExposure(
  microcontentId: string,
  payload: RecordExposureRequest
): Promise<RecordExposureResponse> {
  return apiFetch<RecordExposureResponse>(
    `/api/v1/microcontents/${microcontentId}/exposures`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    "student"
  );
}

export async function listMicrocontents(options?: {
  courseId?: string;
  unitId?: string;
  kcId?: string;
  status?: string;
}): Promise<MicrocontentListItem[]> {
  const query = new URLSearchParams();
  if (options?.courseId) query.set("course_id", options.courseId);
  if (options?.unitId) query.set("unit_id", options.unitId);
  if (options?.kcId) query.set("knowledge_component_id", options.kcId);
  if (options?.status) query.set("status", options.status);

  const qs = query.toString();
  return apiFetch<MicrocontentListItem[]>(
    `/api/v1/microcontents${qs ? `?${qs}` : ""}`,
    { method: "GET" },
    "teacher"
  );
}

export async function createMicrocontent(
  payload: MicrocontentCreatePayload
): Promise<MicrocontentDetailResponse> {
  return apiFetch<MicrocontentDetailResponse>(
    `/api/v1/microcontents`,
    {
      method: "POST",
      body: JSON.stringify(payload),
    },
    "teacher"
  );
}

export async function updateMicrocontent(
  id: string,
  payload: MicrocontentUpdatePayload
): Promise<MicrocontentDetailResponse> {
  return apiFetch<MicrocontentDetailResponse>(
    `/api/v1/microcontents/${id}`,
    {
      method: "PUT",
      body: JSON.stringify(payload),
    },
    "teacher"
  );
}

export async function publishMicrocontent(id: string): Promise<MicrocontentDetailResponse> {
  return apiFetch<MicrocontentDetailResponse>(
    `/api/v1/microcontents/${id}/publish`,
    { method: "POST" },
    "teacher"
  );
}
