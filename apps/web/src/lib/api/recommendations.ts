/**
 * Adaptive Spaced Repetition Recommendations & Retention Inference API Client
 * Connects Next.js web application to FastAPI /api/v1/students/me endpoints.
 */

import { apiFetch } from "./client";

export type RecommendationStatus = "pending" | "delivered" | "completed" | "dismissed" | "expired";
export type RecommendationMethod = "predictive_model" | "rule_based_fallback" | "teacher_assigned";
export type ModelAvailabilityStatus =
  | "empirical_model_ready"
  | "cold_start"
  | "insufficient_empirical_data"
  | "synthetic_test_mode"
  | "model_unavailable";
export type RiskLevel = "low" | "medium" | "high" | "critical";

export interface MicrocontentSummary {
  id: string;
  title: string;
  content_type: string;
  estimated_duration_seconds: number;
}

export interface RecommendationItemResponse {
  id: string;
  knowledge_component_id: string;
  knowledge_component_name: string;
  microcontent: MicrocontentSummary;
  selection_method: RecommendationMethod;
  decision_reason: string;
  status: RecommendationStatus;
  created_at: string;
  scheduled_for: string | null;
  cooldown_until: string | null;
  expires_at: string | null;
  completed_at: string | null;
  is_pending: boolean;
}

export interface CompleteRecommendationResponse {
  id: string;
  status: RecommendationStatus;
  completed_at: string;
  message: string;
}

export interface EvaluationResultItem {
  knowledge_component_id: string;
  knowledge_component_name: string;
  decision: string;
  recommendation_id: string | null;
  reason: string;
}

export interface AdaptationEvaluationResponse {
  student_id: string;
  evaluated_at: string;
  decisions: EvaluationResultItem[];
  recommendations_created: number;
}

export interface HorizonPrediction {
  horizon_hours: number;
  predicted_recall_probability: number;
  estimated_risk: number;
  risk_level: RiskLevel;
}

export interface KCRetentionPrediction {
  knowledge_component_id: string;
  knowledge_component_name: string;
  current_recall_probability: number;
  current_forgetting_risk: number;
  predicted_forgetting_time_seconds: number | null;
  predicted_forgetting_time_days: number | null;
  recommended_review_time: string | null;
  tau_threshold: number;
  model_name: string;
  model_version: string;
  availability_status: ModelAvailabilityStatus;
  horizons: HorizonPrediction[];
  input_event_cutoff: string;
  total_exposures: number;
  total_retrieval_attempts: number;
  last_interaction_at: string | null;
}

export interface StudentRetentionSummaryResponse {
  student_id: string;
  as_of: string;
  status: ModelAvailabilityStatus;
  kcs: KCRetentionPrediction[];
  audit_note: string;
}

export async function getStudentRetention(
  tau: number = 0.650,
  kcId?: string
): Promise<StudentRetentionSummaryResponse> {
  const query = new URLSearchParams();
  query.set("tau", tau.toString());
  if (kcId) query.set("knowledge_component_id", kcId);

  return apiFetch<StudentRetentionSummaryResponse>(
    `/api/v1/students/me/retention?${query.toString()}`,
    { method: "GET" },
    "student"
  );
}

export async function getStudentRecommendations(
  includeCompleted: boolean = false
): Promise<RecommendationItemResponse[]> {
  const query = new URLSearchParams();
  if (includeCompleted) query.set("include_completed", "true");

  return apiFetch<RecommendationItemResponse[]>(
    `/api/v1/students/me/recommendations?${query.toString()}`,
    { method: "GET" },
    "student"
  );
}

export async function evaluateRecommendations(
  tau: number = 0.650
): Promise<AdaptationEvaluationResponse> {
  return apiFetch<AdaptationEvaluationResponse>(
    `/api/v1/students/me/recommendations/evaluate?tau=${tau}`,
    { method: "POST" },
    "student"
  );
}

export async function completeRecommendation(
  recommendationId: string
): Promise<CompleteRecommendationResponse> {
  return apiFetch<CompleteRecommendationResponse>(
    `/api/v1/students/me/recommendations/${recommendationId}/complete`,
    { method: "POST" },
    "student"
  );
}
