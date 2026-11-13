/**
 * Content Generation & Teacher Question Editor API Client
 * Connects Next.js web application to FastAPI /api/v1/content-generation endpoints.
 */

export interface QuestionOptionDraft {
  text: string;
  is_correct: boolean;
  misconception_explanation?: string | null;
}

export interface QuestionSourceReference {
  type: "page" | "slide";
  index: number;
  snippet: string;
}

export interface QuestionDraftItem {
  id: string;
  draft_id?: string;
  generation_job_id: string;
  suggested_kc_name: string;
  question_text: string;
  question_type: string;
  explanation: string;
  options: QuestionOptionDraft[];
  difficulty: number;
  suggested_difficulty?: number;
  bloom_taxonomy: string;
  suggested_bloom_level?: string;
  source_references: QuestionSourceReference[];
  status: "draft" | "edited" | "approved" | "rejected";
  knowledge_component_id?: string | null;
  approved_question_id?: string | null;
  canonical_question_id?: string | null;
  reviewed_by?: string | null;
  reviewed_at?: string | null;
  rejection_reason?: string | null;
  created_at?: string;
  updated_at?: string;
}

export interface ContentGenerationJob {
  job_id: string;
  tenant_id: string;
  status: "queued" | "processing" | "review_required" | "failed" | "cancelled";
  course_id: string | null;
  unit_id: string | null;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  provider: string;
  model_id: string;
  drafts_count: number;
  created_by: string;
  created_at: string;
  updated_at: string | null;
  error_message: string | null;
}

export interface CourseItem {
  id: string;
  code: string;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface KnowledgeComponentItem {
  id: string;
  name: string;
  description: string | null;
  unit_id: string | null;
  unit_title: string | null;
  difficulty_prior: number;
}

export interface CanonicalOptionItem {
  id: string;
  option_text: string;
  is_correct: boolean;
  order_index: number;
}

export interface CanonicalQuestionItem {
  id: string;
  tenant_id: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  question_text: string;
  question_type: string;
  explanation: string;
  difficulty: number;
  is_active: boolean;
  created_by: string;
  created_at: string;
  source_draft_id: string | null;
  options: CanonicalOptionItem[];
}

export interface UpdateDraftPayload {
  question_text?: string;
  options?: QuestionOptionDraft[];
  explanation?: string;
  difficulty?: number;
  bloom_taxonomy?: string;
  knowledge_component_id?: string;
  expected_updated_at?: string;
}

export interface ApproveDraftResponse {
  draft_id: string;
  approved_question_id: string;
  canonical_question_id?: string | null;
  status: string;
  message: string;
}

export interface BatchApproveResponse {
  approved_count: number;
  published_question_ids: string[];
}

export interface UploadMaterialResponse {
  storage_path: string;
  storage_bucket: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_checksum: string;
}

export interface CreateGenerationJobPayload {
  storage_path: string;
  storage_bucket?: string;
  original_filename: string;
  mime_type: string;
  file_size_bytes: number;
  file_checksum: string;
  course_id?: string;
  unit_id?: string;
  provider?: string;
  model_id?: string;
  target_question_count?: number;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// Dynamic Auth & Headers helper for teacher operations
async function getAuthHeaders(includeContentType: boolean = true): Promise<Record<string, string>> {
  const headers: Record<string, string> = {};
  if (includeContentType) {
    headers["Content-Type"] = "application/json";
  }

  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session }, error } = await supabase.auth.getSession();
    if (!error && session?.access_token) {
      headers["Authorization"] = `Bearer ${session.access_token}`;
    }
  } catch (err) {
    // In environments without window or active Supabase context
  }

  // No identity fallback: requests without a verified session are sent
  // unauthenticated and the FastAPI backend rejects them with 401.
  return headers;
}

export const contentGenerationApi = {
  /**
   * List academic courses assigned to the authenticated teacher.
   */
  async getCourses(): Promise<CourseItem[]> {
    try {
      const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/courses`, {
        headers: await getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      // No hidden subject-specific fallback: the UI must show an empty state.
      return [];
    }
  },

  /**
   * List knowledge components associated with a specific course.
   */
  async getCourseKnowledgeComponents(courseId: string): Promise<KnowledgeComponentItem[]> {
    try {
      const res = await fetch(
        `${API_BASE_URL}/api/v1/content-generation/courses/${courseId}/knowledge-components`,
        { headers: await getAuthHeaders() }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      // No hidden subject-specific fallback: the UI must show an empty state.
      return [];
    }
  },

  /**
   * List generation jobs for the authenticated teacher.
   */
  async getJobs(courseId?: string, status?: string): Promise<ContentGenerationJob[]> {
    try {
      const params = new URLSearchParams();
      if (courseId) params.append("course_id", courseId);
      if (status) params.append("status", status);

      const qs = params.toString() ? `?${params.toString()}` : "";
      const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/jobs${qs}`, {
        headers: await getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  /**
   * Get single job details.
   */
  async getJob(jobId: string): Promise<ContentGenerationJob> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/jobs/${jobId}`, {
      headers: await getAuthHeaders(),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  },

  /**
   * List question drafts for a specific job.
   */
  async getDraftsByJob(jobId: string, status?: string): Promise<QuestionDraftItem[]> {
    try {
      const qs = status ? `?status=${encodeURIComponent(status)}` : "";
      const res = await fetch(
        `${API_BASE_URL}/api/v1/content-generation/jobs/${jobId}/drafts${qs}`,
        { headers: await getAuthHeaders() }
      );
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },

  /**
   * Edit a question draft (stem, options, explanation, KC, difficulty, bloom).
   */
  async updateDraft(draftId: string, payload: UpdateDraftPayload): Promise<QuestionDraftItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/drafts/${draftId}`, {
      method: "PATCH",
      headers: await getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || err.detail?.message || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Atomically approve a single draft, publishing to canonical questions and options.
   */
  async approveDraft(
    draftId: string,
    payload: { knowledge_component_id?: string }
  ): Promise<ApproveDraftResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/drafts/${draftId}/approve`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || err.detail?.message || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Batch approve multiple drafts for a job.
   */
  async batchApproveDrafts(
    jobId: string,
    draftIds: string[],
    defaultKnowledgeComponentId?: string
  ): Promise<BatchApproveResponse> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/jobs/${jobId}/approve`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        draft_ids: draftIds,
        default_knowledge_component_id: defaultKnowledgeComponentId,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Discard/reject a question draft with reason.
   */
  async rejectDraft(draftId: string, reason?: string): Promise<QuestionDraftItem> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/drafts/${draftId}/reject`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({ rejection_reason: reason || null, reason: reason || null }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Upload curricular material (PDF / PPTX <= 30MB).
   * Direct Supabase Storage upload is preferred for large files (> 6 MB) to prevent
   * Lambda buffered payload limit breaches, sending only storage_path reference to ML-API.
   */
  async uploadMaterial(file: File, courseId?: string): Promise<UploadMaterialResponse> {
    // Attempt direct Supabase Storage upload for large files (> 6MB) or when session is active
    if (file.size > 6 * 1024 * 1024) {
      try {
        const { createClient } = await import("@/lib/supabase/client");
        const supabase = createClient();
        const { data: { session } } = await supabase.auth.getSession();
        if (session) {
          let tenantId = (session.user?.app_metadata?.tenant_id as string) || (session.user?.user_metadata?.tenant_id as string);
          if (!tenantId && session.user?.id) {
            const { data: profile } = await supabase
              .from("profiles")
              .select("tenant_id")
              .eq("id", session.user.id)
              .maybeSingle();
            if (profile?.tenant_id) {
              tenantId = profile.tenant_id;
            }
          }

          if (!tenantId) {
            throw new Error("No se pudo determinar el tenant_id del usuario autenticado.");
          }

          const cleanName = file.name.replace(/[^a-zA-Z0-9._-]/g, "_");
          const folder = courseId || "general";
          const storagePath = `${tenantId}/${folder}/${cleanName}`;

          // Calculate SHA-256 checksum in browser
          const buffer = await file.arrayBuffer();
          const digest = await crypto.subtle.digest("SHA-256", buffer);
          const checksum = Array.from(new Uint8Array(digest))
            .map((b) => b.toString(16).padStart(2, "0"))
            .join("");

          const { error: uploadError } = await supabase.storage
            .from("teacher-materials")
            .upload(storagePath, file, { upsert: true });

          if (!uploadError) {
            const formData = new FormData();
            formData.append("storage_path", storagePath);
            formData.append("storage_bucket", "teacher-materials");
            formData.append("original_filename", file.name);
            formData.append("mime_type", file.type || (file.name.endsWith(".pptx") ? "application/vnd.openxmlformats-officedocument.presentationml.presentation" : "application/pdf"));
            formData.append("file_size_bytes", String(file.size));
            formData.append("file_checksum", checksum);
            if (courseId) formData.append("course_id", courseId);

            const headers = await getAuthHeaders(false);
            const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/upload-material`, {
              method: "POST",
              headers,
              body: formData,
            });
            if (res.ok) {
              return await res.json();
            }
          }
        }
      } catch {
        // Fallback to standard multipart upload
      }
    }

    const formData = new FormData();
    formData.append("file", file);
    if (courseId) formData.append("course_id", courseId);

    const headers = await getAuthHeaders(false);

    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/upload-material`, {
      method: "POST",
      headers,
      body: formData,
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Create content generation job.
   */
  async createGenerationJob(payload: CreateGenerationJobPayload): Promise<ContentGenerationJob> {
    const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/jobs`, {
      method: "POST",
      headers: await getAuthHeaders(),
      body: JSON.stringify({
        storage_bucket: payload.storage_bucket || "teacher-materials",
        storage_path: payload.storage_path,
        original_filename: payload.original_filename,
        mime_type: payload.mime_type,
        file_size_bytes: payload.file_size_bytes,
        file_checksum: payload.file_checksum,
        course_id: payload.course_id,
        unit_id: payload.unit_id,
        provider: payload.provider || "mock",
        model_id: payload.model_id || "mock-v1",
        target_question_count: payload.target_question_count || 5,
      }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      const msg = err.detail?.detail || `HTTP ${res.status}`;
      throw new Error(msg);
    }
    return await res.json();
  },

  /**
   * Retrieve canonical published questions bank.
   */
  async getCanonicalQuestions(courseId?: string): Promise<CanonicalQuestionItem[]> {
    try {
      const qs = courseId ? `?course_id=${encodeURIComponent(courseId)}` : "";
      const res = await fetch(`${API_BASE_URL}/api/v1/content-generation/questions${qs}`, {
        headers: await getAuthHeaders(),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      return await res.json();
    } catch {
      return [];
    }
  },
};
