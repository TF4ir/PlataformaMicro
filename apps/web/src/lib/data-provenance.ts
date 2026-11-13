/**
 * Data provenance, evidence and formatting helpers (Sprint UI-UX P0 / BL-01 & BL-04).
 *
 * This module is intentionally free of React/Next imports so it can be unit-tested
 * directly with Node's type stripping (`node --test src/tests/*.test.mjs`).
 *
 * Rules encoded here:
 * - A successful query that returns zero rows is an observed zero (valid value).
 * - A metric with no denominator is "insufficient evidence", never a numeric guess.
 * - A failed/unavailable query is "unavailable", never zero.
 * - Only measured latency is displayed; unrun/failed requests show "No medida".
 * - Security controls are "unverified" unless the product actually checked them.
 */

export type DataProvenance =
  | "observed"
  | "estimated"
  | "synthetic"
  | "demo"
  | "unavailable";

export type MetricStatus = "observed" | "insufficient_evidence" | "unavailable";

export type MasteryStatus =
  | "consolidated"
  | "in_progress"
  | "requiring_reinforcement"
  | "insufficient_evidence";

export interface MetricMeta {
  status: MetricStatus;
  provenance: DataProvenance;
  sample_size: number | null;
}

export interface MetricDisplay extends MetricMeta {
  value: number | null;
  display: string;
}

export interface AttemptSummary {
  total_questions: number;
  correct_answers: number;
  score: number | null;
  has_evidence: boolean;
}

export interface MasteryDistribution {
  requiring_reinforcement: number;
  in_progress: number;
  consolidated: number;
  insufficient_evidence: number;
}

export interface MasteryThresholds {
  consolidated: number;
  inProgress: number;
  minSample: number;
}

export const PROVENANCE_LABELS: Record<DataProvenance, string> = {
  observed: "Observado",
  estimated: "Estimado",
  synthetic: "Sintético",
  demo: "Demostración",
  unavailable: "No disponible",
};

export const STATUS_LABELS: Record<MetricStatus, string> = {
  observed: "Observado",
  insufficient_evidence: "Sin evidencia suficiente",
  unavailable: "No disponible",
};

export const UNAVAILABLE_TEXT = "No disponible";
export const INSUFFICIENT_TEXT = "Sin evidencia suficiente";
export const NOT_MEASURED_TEXT = "No medida";
export const UNVERIFIED_TEXT = "No verificado";

function readThreshold(raw: string | undefined, fallback: number): number {
  if (raw === undefined || raw === null || raw === "") return fallback;
  const parsed = Number(raw);
  if (!Number.isFinite(parsed) || parsed < 0 || parsed > 100) return fallback;
  return parsed;
}

/**
 * Cut-off thresholds are configuration-driven (never invented inside a view).
 * Override with NEXT_PUBLIC_MASTERY_* environment variables.
 */
export const MASTERY_THRESHOLDS: MasteryThresholds = {
  consolidated: readThreshold(
    process.env.NEXT_PUBLIC_MASTERY_CONSOLIDATED_THRESHOLD,
    80
  ),
  inProgress: readThreshold(
    process.env.NEXT_PUBLIC_MASTERY_IN_PROGRESS_THRESHOLD,
    55
  ),
  minSample: Math.max(
    1,
    Math.trunc(
      readThreshold(process.env.NEXT_PUBLIC_MASTERY_MIN_SAMPLE, 1)
    )
  ),
};

export function observedMeta(sampleSize: number | null): MetricMeta {
  return {
    status: "observed",
    provenance: "observed",
    sample_size: sampleSize,
  };
}

export function insufficientMeta(sampleSize: number | null): MetricMeta {
  return {
    status: "insufficient_evidence",
    provenance: "observed",
    sample_size: sampleSize,
  };
}

export function unavailableMeta(): MetricMeta {
  return {
    status: "unavailable",
    provenance: "unavailable",
    sample_size: null,
  };
}

/**
 * Normalises a count without turning zero into a fallback. Returns null only when
 * the value is genuinely absent/invalid.
 */
export function observedCount(value: number | null | undefined): number | null {
  if (typeof value !== "number" || !Number.isFinite(value) || value < 0) {
    return null;
  }
  return Math.trunc(value);
}

/**
 * Count metrics: zero is a valid observed value. `unavailable` must be passed
 * explicitly when the underlying query failed.
 */
export function formatCountMetric(
  value: number | null | undefined,
  options: { unavailable?: boolean; unit?: string } = {}
): MetricDisplay {
  if (options.unavailable) {
    return {
      ...unavailableMeta(),
      value: null,
      display: UNAVAILABLE_TEXT,
    };
  }

  const count = observedCount(value);
  if (count === null) {
    return {
      ...insufficientMeta(null),
      value: null,
      display: INSUFFICIENT_TEXT,
    };
  }

  return {
    ...observedMeta(count),
    value: count,
    display: `${count}${options.unit ? ` ${options.unit}` : ""}`,
  };
}

/**
 * Accuracy metrics require a positive denominator. A 0% observed accuracy is valid
 * (0 correct out of N), while 0/0 is insufficient evidence.
 */
export function observedPercentage(
  correct: number | null | undefined,
  total: number | null | undefined,
  options: {
    unavailable?: boolean;
    minSample?: number;
    decimals?: number;
  } = {}
): MetricDisplay {
  const decimals = options.decimals ?? 1;

  if (options.unavailable) {
    return {
      ...unavailableMeta(),
      value: null,
      display: UNAVAILABLE_TEXT,
    };
  }

  const correctCount = observedCount(correct);
  const totalCount = observedCount(total);
  const minSample = options.minSample ?? MASTERY_THRESHOLDS.minSample;

  if (
    correctCount === null ||
    totalCount === null ||
    totalCount === 0 ||
    totalCount < minSample
  ) {
    return {
      ...insufficientMeta(totalCount),
      value: null,
      display: INSUFFICIENT_TEXT,
    };
  }

  const boundedCorrect = Math.min(correctCount, totalCount);
  const value = Number(
    ((boundedCorrect / totalCount) * 100).toFixed(decimals)
  );

  return {
    ...observedMeta(totalCount),
    value,
    display: `${value.toFixed(decimals)}%`,
  };
}

/**
 * Formats an already-computed percentage while still validating the denominator.
 * Useful for backend responses that default to `0.0` when no evidence exists.
 */
export function observedPercentageValue(
  percentage: number | null | undefined,
  total: number | null | undefined,
  options: {
    unavailable?: boolean;
    minSample?: number;
    decimals?: number;
  } = {}
): MetricDisplay {
  const decimals = options.decimals ?? 1;

  if (options.unavailable) {
    return {
      ...unavailableMeta(),
      value: null,
      display: UNAVAILABLE_TEXT,
    };
  }

  const totalCount = observedCount(total);
  const minSample = options.minSample ?? MASTERY_THRESHOLDS.minSample;

  if (
    typeof percentage !== "number" ||
    !Number.isFinite(percentage) ||
    totalCount === null ||
    totalCount === 0 ||
    totalCount < minSample
  ) {
    return {
      ...insufficientMeta(totalCount),
      value: null,
      display: INSUFFICIENT_TEXT,
    };
  }

  const value = Number(
    Math.min(100, Math.max(0, percentage)).toFixed(decimals)
  );

  return {
    ...observedMeta(totalCount),
    value,
    display: `${value.toFixed(decimals)}%`,
  };
}

/**
 * Generic value formatter. `value === null` means "not measured" and is shown as
 * an em dash or an explicit status, never as a numeric fallback.
 */
export function formatMetricValue(
  value: number | null | undefined,
  options: {
    unit?: string;
    unavailable?: boolean;
    insufficient?: boolean;
    decimals?: number;
    fallback?: "dash" | "text";
  } = {}
): string {
  if (options.unavailable) return UNAVAILABLE_TEXT;
  if (options.insufficient) return INSUFFICIENT_TEXT;
  if (typeof value !== "number" || !Number.isFinite(value)) {
    return options.fallback === "text" ? INSUFFICIENT_TEXT : "—";
  }
  const decimals = options.decimals ?? 0;
  const formatted = decimals > 0 ? value.toFixed(decimals) : String(Math.round(value));
  return `${formatted}${options.unit ? ` ${options.unit}` : ""}`;
}

/**
 * Formats a value using an explicit provenance/status envelope. Prefer this in
 * views so "unavailable" and "insufficient evidence" are never rendered as 0.
 */
export function formatMetricWithMeta(
  meta: MetricMeta | null | undefined,
  value: number | null | undefined,
  options: {
    unit?: string;
    decimals?: number;
    fallback?: "dash" | "text";
  } = {}
): string {
  if (meta?.status === "unavailable") return UNAVAILABLE_TEXT;
  if (meta?.status === "insufficient_evidence") return INSUFFICIENT_TEXT;
  return formatMetricValue(value, {
    unit: options.unit,
    decimals:
      options.decimals ??
      (typeof value === "number" && !Number.isInteger(value) ? 1 : 0),
    fallback: options.fallback,
  });
}

/** Latency is only displayed when the request actually completed and was timed. */
export function formatLatency(
  milliseconds: number | null | undefined,
  options: { measured?: boolean } = {}
): string {
  const measured = options.measured ?? true;
  if (
    !measured ||
    typeof milliseconds !== "number" ||
    !Number.isFinite(milliseconds) ||
    milliseconds < 0
  ) {
    return NOT_MEASURED_TEXT;
  }
  return `${Math.round(milliseconds)} ms`;
}

/** Timestamp with date, time and explicit timezone (BL-04). */
export function formatVerificationTimestamp(
  input: Date | string | number | null | undefined,
  timeZone: string = "America/Lima"
): string {
  if (input === null || input === undefined) return UNAVAILABLE_TEXT;
  const date = input instanceof Date ? input : new Date(input);
  if (Number.isNaN(date.getTime())) return UNAVAILABLE_TEXT;

  try {
    const formatted = new Intl.DateTimeFormat("es-PE", {
      dateStyle: "medium",
      timeStyle: "medium",
      timeZone,
    }).format(date);
    return `${formatted} (${timeZone})`;
  } catch {
    return UNAVAILABLE_TEXT;
  }
}

/** Course names come from metadata. Never hardcode a school subject. */
export function resolveCourseName(input: unknown): string {
  if (typeof input === "string" && input.trim()) return input.trim();
  if (input && typeof input === "object") {
    const candidate = (input as Record<string, unknown>).name;
    if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  }
  return "Curso sin nombre";
}

export function resolveKnowledgeComponentName(input: unknown): string {
  if (typeof input === "string" && input.trim()) return input.trim();
  if (input && typeof input === "object") {
    const candidate = (input as Record<string, unknown>).name;
    if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  }
  return "Componente sin nombre";
}

export function resolveContentTitle(input: unknown): string {
  if (typeof input === "string" && input.trim()) return input.trim();
  if (input && typeof input === "object") {
    const candidate = (input as Record<string, unknown>).title;
    if (typeof candidate === "string" && candidate.trim()) return candidate.trim();
  }
  return "Contenido sin título";
}

/** Reads `content_body.diagram_key` without trusting the title. */
export function readDiagramKey(contentBody: unknown): string | null {
  if (!contentBody || typeof contentBody !== "object") return null;
  const key = (contentBody as Record<string, unknown>).diagram_key;
  if (typeof key !== "string" || !key.trim()) return null;
  return key.trim().toLowerCase();
}

export type ContentRenderer = "photosynthesis" | "generic";

/**
 * Specialised renderers are selected exclusively from explicit metadata
 * (`content_type` / `diagram_key`). Titles are never inspected (BL-03).
 */
export function selectContentRenderer(input: {
  content_type?: string | null;
  content_body?: unknown;
}): ContentRenderer {
  const diagramKey = readDiagramKey(input.content_body);
  if (diagramKey === "photosynthesis" || diagramKey === "fotosintesis") {
    return "photosynthesis";
  }

  const contentType = (input.content_type || "").trim().toLowerCase();
  if (
    contentType === "photosynthesis_diagram" ||
    contentType === "photosynthesis"
  ) {
    return "photosynthesis";
  }

  return "generic";
}

/**
 * Classifies a student's mastery from observed accuracy. Returns
 * "insufficient_evidence" instead of guessing when there are no answers.
 */
export function classifyMastery(
  accuracy: number | null | undefined,
  sampleSize: number | null | undefined,
  thresholds: MasteryThresholds = MASTERY_THRESHOLDS
): MasteryStatus {
  const sample = observedCount(sampleSize);
  if (
    typeof accuracy !== "number" ||
    !Number.isFinite(accuracy) ||
    sample === null ||
    sample < thresholds.minSample
  ) {
    return "insufficient_evidence";
  }
  if (accuracy >= thresholds.consolidated) return "consolidated";
  if (accuracy >= thresholds.inProgress) return "in_progress";
  return "requiring_reinforcement";
}

/**
 * Coherent distribution: every roster row lands in exactly one bucket, so the
 * four counts always add up to the roster size.
 */
export function buildProficiencyDistribution(
  rows: Array<{
    accuracy: number | null | undefined;
    sampleSize: number | null | undefined;
  }>,
  thresholds: MasteryThresholds = MASTERY_THRESHOLDS
): MasteryDistribution {
  const distribution: MasteryDistribution = {
    requiring_reinforcement: 0,
    in_progress: 0,
    consolidated: 0,
    insufficient_evidence: 0,
  };

  for (const row of rows) {
    const status = classifyMastery(row.accuracy, row.sampleSize, thresholds);
    distribution[status] += 1;
  }

  return distribution;
}

/**
 * Summarises an attempt from declared values and/or recorded events.
 * Zero correct answers stays zero; an attempt with no questions has no evidence.
 */
export function summarizeAttempt(input: {
  declaredTotal?: number | null;
  declaredCorrect?: number | null;
  events?: Array<{ is_correct: boolean | null | undefined }>;
}): AttemptSummary {
  const events = input.events || [];
  const eventTotal = events.length;
  const eventCorrect = events.filter((event) => event.is_correct === true).length;

  const declaredTotal = observedCount(input.declaredTotal);
  const total = declaredTotal !== null && declaredTotal > 0 ? declaredTotal : eventTotal;

  const declaredCorrect = observedCount(input.declaredCorrect);
  const correct = Math.min(
    declaredCorrect !== null ? declaredCorrect : eventCorrect,
    total
  );

  if (total === 0) {
    return {
      total_questions: 0,
      correct_answers: 0,
      score: null,
      has_evidence: false,
    };
  }

  return {
    total_questions: total,
    correct_answers: correct,
    score: Number(((correct / total) * 100).toFixed(1)),
    has_evidence: true,
  };
}

/** Demo data/auth must be explicitly enabled outside production and is always labelled. */
export function isDemoModeEnabled(env: {
  NODE_ENV?: string;
  NEXT_PUBLIC_ENABLE_DEMO_AUTH?: string;
} = process.env): boolean {
  return (
    env.NODE_ENV !== "production" &&
    env.NEXT_PUBLIC_ENABLE_DEMO_AUTH === "true"
  );
}

export const DEMO_BANNER_TEXT =
  "Modo demostración activo: los datos sintéticos y los accesos de prueba no representan actividad real.";
