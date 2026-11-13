export type UserRole = "student" | "teacher";

export interface StudentProfile {
  id: string;
  name: string;
  initials: string;
  grade: string;
  school: string;
}

export interface TeacherProfile {
  id: string;
  name: string;
  initials: string;
  roleTitle: string;
}

export interface Course {
  id: string;
  code: string;
  title: string;
  area: string;
  description: string;
  grade: string;
  status: "active" | "draft" | "archived";
  unitsCount: number;
  conceptsCount: number;
  sectionsCount: number;
  progressPercentage: number;
  lastUpdated: string;
}

export interface RecommendedActivity {
  id: string;
  courseId: string;
  courseTitle: string;
  unitTitle: string;
  conceptTitle: string;
  title: string;
  subtitle: string;
  whyRecommended: string;
  estimatedMinutes: number;
  steps: {
    number: number;
    title: string;
    description: string;
    duration: string;
    type: "lesson" | "quiz";
    route: string;
  }[];
}

export interface MicrocontentSection {
  id: number;
  navTitle: string;
  heading: string;
  tag: string;
  lead: string;
  durationMinutes: number;
  formula?: string;
  analogy?: {
    title: string;
    body: string;
  };
  keyTakeaways?: {
    number: string;
    text: string;
  }[];
}

export interface QuizQuestion {
  id: string;
  questionNumber: number;
  totalQuestions: number;
  conceptTitle: string;
  prompt: string;
  scorePoints: number;
  options: {
    id: string;
    label: string; // "A", "B", "C", "D"
    text: string;
  }[];
  correctOptionId: string;
  explanation: string;
  reminderNote: string;
}

export interface StudentAnalytics {
  completedActivities: number;
  completedThisMonth: number;
  observedAccuracy: number; // e.g. 82
  totalResponses: number;
  consolidatedConcepts: number;
  totalConcepts: number;
  currentStreakDays: number;
  bestStreakDays: number;
  weeklyLearningMinutes: number;
  weeklyDeltaPercentage: number;
  reviewedConceptsCount: number;
  weeklyTargetCount: number;
  overallProgress: number; // e.g. 78
  evolutionData: {
    date: string;
    accuracy: number;
  }[];
  conceptStatusBreakdown: {
    status: string;
    count: number;
    color: string;
  }[];
  history: {
    id: string;
    concept: string;
    date: string;
    observedResult: string;
    status: "Consolidado" | "En proceso" | "Por repasar";
  }[];
}

export type ApiStatus = "healthy" | "cold_start" | "degraded" | "unavailable";

export type SecurityVerificationStatus = "verified" | "unverified" | "failed";

export interface SystemStatusData {
  apiStatus: ApiStatus;
  /**
   * Only populated when the API actually reported a cold-start estimate.
   * `null` means "not reported", never zero.
   */
  coldStartEstimatedSeconds: number | null;
  /**
   * Only populated when the API explicitly reports the active model.
   * `null` means "not reported", never a guessed fallback model.
   */
  activeModel: string | null;
  /**
   * Only set when a request was actually timed. `null` means "not measured",
   * which the UI must render as "No medida".
   */
  inferenceLatencyMs: number | null;
  /** Security controls are unverified unless the product checked them. */
  supabaseRlsStatus: SecurityVerificationStatus;
  pseudonymizationStatus: SecurityVerificationStatus;
  /** ISO timestamp of the last successful check, or null when never checked. */
  lastHeartbeat: string | null;
}
