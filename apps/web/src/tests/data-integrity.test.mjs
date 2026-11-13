/**
 * P0 data-integrity regression tests (Sprint UI-UX / BL-01, BL-03, BL-04).
 *
 * These tests import the shared provenance module directly through Node's
 * TypeScript type stripping, so they exercise the exact same helpers used by
 * the React views.
 */

import { describe, it } from "node:test";
import assert from "node:assert/strict";

import {
  DEMO_BANNER_TEXT,
  INSUFFICIENT_TEXT,
  NOT_MEASURED_TEXT,
  UNAVAILABLE_TEXT,
  UNVERIFIED_TEXT,
  buildProficiencyDistribution,
  classifyMastery,
  formatCountMetric,
  formatLatency,
  formatMetricValue,
  formatMetricWithMeta,
  formatVerificationTimestamp,
  isDemoModeEnabled,
  observedPercentage,
  observedPercentageValue,
  resolveContentTitle,
  resolveCourseName,
  resolveKnowledgeComponentName,
  selectContentRenderer,
  summarizeAttempt,
} from "../lib/data-provenance.ts";

describe("BL-01 · datos veraces y procedencia", () => {
  it("1. Un conteo observado de cero se muestra como 0 (no como fallback)", () => {
    const metric = formatCountMetric(0);

    assert.equal(metric.value, 0);
    assert.equal(metric.display, "0");
    assert.equal(metric.status, "observed");
    assert.equal(metric.provenance, "observed");
  });

  it("2. Una métrica sin evidencia se muestra como 'Sin evidencia suficiente', no como 0", () => {
    const accuracy = observedPercentage(0, 0);

    assert.equal(accuracy.value, null);
    assert.equal(accuracy.display, INSUFFICIENT_TEXT);
    assert.equal(accuracy.status, "insufficient_evidence");

    assert.equal(formatCountMetric(null).display, INSUFFICIENT_TEXT);
  });

  it("3. Una consulta fallida se muestra como 'No disponible', no como 0", () => {
    const metric = formatCountMetric(undefined, { unavailable: true });

    assert.equal(metric.value, null);
    assert.equal(metric.display, UNAVAILABLE_TEXT);
    assert.equal(metric.status, "unavailable");
    assert.equal(formatMetricValue(null, { unavailable: true }), UNAVAILABLE_TEXT);
  });

  it("4. Un intento con 0 respuestas correctas de N conserva 0 (no inventa aciertos)", () => {
    const accuracy = observedPercentage(0, 5);
    assert.equal(accuracy.value, 0);
    assert.equal(accuracy.display, "0.0%");
    assert.equal(accuracy.status, "observed");
    assert.equal(accuracy.sample_size, 5);

    const summary = summarizeAttempt({
      events: [
        { is_correct: false },
        { is_correct: false },
        { is_correct: false },
      ],
    });
    assert.equal(summary.total_questions, 3);
    assert.equal(summary.correct_answers, 0);
    assert.equal(summary.score, 0);
    assert.equal(summary.has_evidence, true);
  });

  it("5. Un intento vacío no genera puntaje ni evidencia", () => {
    const summary = summarizeAttempt({ events: [] });

    assert.equal(summary.total_questions, 0);
    assert.equal(summary.score, null);
    assert.equal(summary.has_evidence, false);
  });

  it("6. La clasificación de dominio distingue evidencia insuficiente de 0%", () => {
    assert.equal(classifyMastery(null, 0), "insufficient_evidence");
    assert.equal(classifyMastery(0, 5), "requiring_reinforcement");
    assert.equal(classifyMastery(60, 5), "in_progress");
    assert.equal(classifyMastery(90, 5), "consolidated");
  });

  it("7. La distribución de proficiencia es coherente: cada fila cae en un solo grupo", () => {
    const distribution = buildProficiencyDistribution([
      { accuracy: 90, sampleSize: 5 },
      { accuracy: 60, sampleSize: 5 },
      { accuracy: 20, sampleSize: 5 },
      { accuracy: null, sampleSize: 0 },
    ]);

    const total =
      distribution.consolidated +
      distribution.in_progress +
      distribution.requiring_reinforcement +
      distribution.insufficient_evidence;

    assert.equal(total, 4);
    assert.equal(distribution.consolidated, 1);
    assert.equal(distribution.in_progress, 1);
    assert.equal(distribution.requiring_reinforcement, 1);
    assert.equal(distribution.insufficient_evidence, 1);
  });

  it("8. formatMetricWithMeta respeta el estado aunque el valor numérico sea 0", () => {
    assert.equal(
      formatMetricWithMeta({ status: "unavailable", provenance: "unavailable", sample_size: null }, 0),
      UNAVAILABLE_TEXT
    );
    assert.equal(
      formatMetricWithMeta(
        { status: "insufficient_evidence", provenance: "observed", sample_size: 0 },
        0
      ),
      INSUFFICIENT_TEXT
    );
    assert.equal(
      formatMetricWithMeta({ status: "observed", provenance: "observed", sample_size: 3 }, 0),
      "0"
    );
  });

  it("9. observedPercentageValue nunca usa un denominador vacío", () => {
    assert.equal(observedPercentageValue(69.4, 0).display, INSUFFICIENT_TEXT);
    assert.equal(observedPercentageValue(0, 10).display, "0.0%");
    assert.equal(observedPercentageValue(100, 10).value, 100);
  });
});

describe("BL-03 · contenido agnóstico a la asignatura", () => {
  it("10. Los metadatos de un curso de Historia se muestran sin sustituirse por Ciencias", () => {
    const course = { id: "c-historia", name: "Historia" };
    const kc = { id: "kc-revolucion", name: "Revolución Industrial" };
    const content = { id: "m-1", title: "Causas de la Revolución Industrial" };

    assert.equal(resolveCourseName(course), "Historia");
    assert.equal(resolveKnowledgeComponentName(kc), "Revolución Industrial");
    assert.equal(resolveContentTitle(content), "Causas de la Revolución Industrial");
    assert.equal(resolveCourseName(null), "Curso sin nombre");
  });

  it("11. El renderizador especializado depende de content_type/diagram_key, nunca del título", () => {
    assert.equal(
      selectContentRenderer({
        content_type: "text_summary",
        content_body: { summary: "Título engañoso" },
      }),
      "generic"
    );

    assert.equal(
      selectContentRenderer({
        content_type: "text_summary",
        content_body: { diagram_key: "photosynthesis" },
      }),
      "photosynthesis"
    );

    assert.equal(
      selectContentRenderer({ content_type: "photosynthesis_diagram" }),
      "photosynthesis"
    );

    // Un título con la palabra "Fotosíntesis" no activa el diagrama por sí solo.
    const misleading = {
      title: "Fotosíntesis: fase luminosa",
      content_type: "text_summary",
      content_body: {},
    };
    assert.equal(selectContentRenderer(misleading), "generic");
  });
});

describe("BL-04 · estados del sistema honestos", () => {
  it("12. La latencia solo se muestra cuando fue medida", () => {
    assert.equal(formatLatency(null), NOT_MEASURED_TEXT);
    assert.equal(formatLatency(undefined), NOT_MEASURED_TEXT);
    assert.equal(formatLatency(120, { measured: false }), NOT_MEASURED_TEXT);
    assert.equal(formatLatency(0), "0 ms");
    assert.equal(formatLatency(1534.7), "1535 ms");
  });

  it("13. El timestamp de verificación incluye fecha, hora y zona horaria", () => {
    const formatted = formatVerificationTimestamp("2026-11-08T15:04:05Z");

    assert.match(formatted, /\d{1,2}/);
    assert.match(formatted, /\d{1,2}:\d{2}/);
    assert.ok(formatted.includes("America/Lima"));
    assert.ok(formatted.includes("2026"));
    assert.equal(formatVerificationTimestamp(null), UNAVAILABLE_TEXT);
  });

  it("14. RLS y seudonimización se reportan como 'No verificado' por defecto", () => {
    assert.equal(UNVERIFIED_TEXT, "No verificado");
    assert.notEqual(UNVERIFIED_TEXT, "verified");
  });

  it("15. El modo demo exige bandera explícita y NODE_ENV distinto de production, con banner persistente", () => {
    assert.equal(isDemoModeEnabled({ NODE_ENV: "production", NEXT_PUBLIC_ENABLE_DEMO_AUTH: "true" }), false);
    assert.equal(isDemoModeEnabled({ NODE_ENV: "development", NEXT_PUBLIC_ENABLE_DEMO_AUTH: "false" }), false);
    assert.equal(isDemoModeEnabled({ NODE_ENV: "development" }), false);
    assert.equal(isDemoModeEnabled({ NODE_ENV: "development", NEXT_PUBLIC_ENABLE_DEMO_AUTH: "true" }), true);
    assert.match(DEMO_BANNER_TEXT, /demostración/i);
  });
});
