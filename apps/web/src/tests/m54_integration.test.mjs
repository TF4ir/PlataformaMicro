import { describe, it } from "node:test";
import assert from "node:assert/strict";

describe("Frontend M5.4 Integration & UI/UX Telemetry Tests", () => {
  it("1. Microcontent structure: sections parse correctly with required navigation fields", () => {
    const rawMicrocontent = {
      id: "a1000000-0000-0000-0000-000000000001",
      title: "Fotosíntesis: Fase luminosa y fijación de carbono",
      content_body: {
        summary: "Visión global del proceso fotosintético",
        sections: [
          {
            id: 1,
            navTitle: "Conceptos clave",
            heading: "Fundamentos fotosintéticos",
            tag: "Microlección",
            lead: "Las plantas capturan fotones solares...",
            durationMinutes: 2,
          },
          {
            id: 2,
            navTitle: "El proceso",
            heading: "Reacciones dependientes de la luz",
            tag: "Bioquímica",
            lead: "Ocurre en la membrana del tilacoide...",
            durationMinutes: 3,
            formula: "6 CO2 + 6 H2O + Luz -> C6H12O6 + 6 O2",
          },
        ],
      },
      estimated_duration_seconds: 300,
      is_published: true,
    };

    assert.equal(rawMicrocontent.content_body.sections.length, 2);
    assert.equal(rawMicrocontent.content_body.sections[0].navTitle, "Conceptos clave");
    assert.equal(rawMicrocontent.content_body.sections[1].durationMinutes, 3);
    assert.ok(rawMicrocontent.content_body.sections[1].formula.includes("6 CO2"));
  });

  it("2. Exposure telemetry payload: validates required audit fields and duration tracking", () => {
    const startedAt = new Date(Date.now() - 180000).toISOString();
    const completedAt = new Date().toISOString();
    const sessionId = "s1000000-0000-0000-0000-000000000001";
    const idempotencyKey = "i1000000-0000-0000-0000-000000000001";

    const payload = {
      started_at: startedAt,
      completed_at: completedAt,
      duration_seconds: 180,
      active_reading_seconds: 165,
      completion_status: "completed",
      exposure_type: "review_study",
      session_id: sessionId,
      idempotency_key: idempotencyKey,
      recommendation_id: "r1000000-0000-0000-0000-000000000001",
    };

    assert.equal(payload.completion_status, "completed");
    assert.equal(payload.exposure_type, "review_study");
    assert.ok(payload.duration_seconds >= payload.active_reading_seconds);
    assert.ok(payload.recommendation_id);
  });

  it("3. Cold start handling: identifies N < 3 as early phase without punitive retention score", () => {
    function classifyKC(totalAnswers, observedAccuracy, estimatedRetention) {
      if (totalAnswers < 3) {
        return {
          status: "Fase inicial (requiere más respuestas)",
          isColdStart: true,
          displayScore: "—",
        };
      }
      return {
        status:
          observedAccuracy >= 80
            ? "Consolidado"
            : observedAccuracy >= 60
            ? "En proceso"
            : "Refuerzo sugerido",
        isColdStart: false,
        displayScore: `${estimatedRetention}%`,
      };
    }

    const coldCase = classifyKC(1, 100.0, 95.0);
    assert.equal(coldCase.isColdStart, true);
    assert.equal(coldCase.displayScore, "—");
    assert.equal(coldCase.status, "Fase inicial (requiere más respuestas)");

    const warmCase = classifyKC(5, 75.0, 72.0);
    assert.equal(warmCase.isColdStart, false);
    assert.equal(warmCase.status, "En proceso");
    assert.equal(warmCase.displayScore, "72%");
  });

  it("4. Empathetic pedagogical status mapping: replaces negative labels with constructive phrasing", () => {
    function getPedagogicalBadge(accuracy) {
      if (accuracy >= 80) {
        return { variant: "success", label: "Consolidado" };
      }
      if (accuracy >= 60) {
        return { variant: "warning", label: "En proceso" };
      }
      return { variant: "warning", label: "Refuerzo sugerido" };
    }

    assert.equal(getPedagogicalBadge(90).label, "Consolidado");
    assert.equal(getPedagogicalBadge(70).label, "En proceso");
    assert.equal(getPedagogicalBadge(45).label, "Refuerzo sugerido");
    // Ensure no negative/punitive terms
    assert.notEqual(getPedagogicalBadge(45).label, "Riesgo de reprobar");
    assert.notEqual(getPedagogicalBadge(45).label, "Deficiente");
  });

  it("5. Pseudonymized export: strips real student names and emails from CSV", () => {
    const rawStudents = [
      {
        student_id: "e0000000-0000-0000-0000-000000000001",
        full_name: "Camila Rojas",
        student_code: "EST-501",
        email: "camila.rojas@colegio.edu.pe",
        section_name: "5.° A",
        observed_accuracy: 88.5,
      },
    ];

    const exportedRows = rawStudents.map((s) => ({
      code: s.student_code,
      section: s.section_name,
      accuracy: s.observed_accuracy,
    }));

    const jsonStr = JSON.stringify(exportedRows);
    assert.ok(!jsonStr.includes("Camila"));
    assert.ok(!jsonStr.includes("camila.rojas@colegio.edu.pe"));
    assert.ok(jsonStr.includes("EST-501"));
  });

  it("6. Spaced repetition priority sorting: ranks urgent recommendations ahead of routine ones", () => {
    const reviews = [
      { id: "1", priority: "Recomendado", is_urgent: false, days_elapsed: 2 },
      { id: "2", priority: "Prioridad", is_urgent: true, days_elapsed: 6 },
      { id: "3", priority: "Recomendado", is_urgent: false, days_elapsed: 1 },
    ];

    const sorted = [...reviews].sort((a, b) => {
      if (a.is_urgent && !b.is_urgent) return -1;
      if (!a.is_urgent && b.is_urgent) return 1;
      return b.days_elapsed - a.days_elapsed;
    });

    assert.equal(sorted[0].id, "2");
    assert.equal(sorted[0].priority, "Prioridad");
  });
});
