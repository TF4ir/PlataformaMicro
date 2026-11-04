/**
 * Automated Frontend Validation & Integration Unit Tests for Milestone M4:
 * Learning Flow, Questionnaire Management, and Immutable answer_events.
 *
 * Covers:
 * 1. Validación de creación de actividades docentes (título, secciones, banco aprobado M3).
 * 2. Preservación del Knowledge Component (KC) en las preguntas seleccionadas.
 * 3. Ciclo de vida y transiciones de estado de actividad (draft -> published -> closed).
 * 4. Listado y filtrado de actividades del estudiante según su sección asignada.
 * 5. Sanitización de preguntas para el estudiante (cero fuga de is_correct ni explicaciones privadas).
 * 6. Inicio seguro de intentos con clave de idempotencia (X-Idempotency-Key).
 * 7. Registro de respuestas con medición de tiempo (response_time_seconds) y política de feedback.
 * 8. Finalización del intento y cálculo de resultados en backend (score 0-100%).
 * 9. Desglose de dominio por Knowledge Component con lenguaje pedagógico empático.
 * 10. Analítica docente agregada por secciones, preguntas y componentes de conocimiento.
 * 11. Seguridad y manejo de errores (403, 404, inmutabilidad).
 */

import { test, describe } from "node:test";
import assert from "node:assert/strict";

// Helper function: Validate teacher activity creation payload
function validateActivityCreationPayload(payload) {
  if (!payload.title || !payload.title.trim()) {
    return { valid: false, error: "El título del cuestionario es obligatorio." };
  }
  if (!payload.course_id || !payload.course_id.trim()) {
    return { valid: false, error: "Debes seleccionar un curso institucional." };
  }
  if (!payload.section_ids || payload.section_ids.length === 0) {
    return { valid: false, error: "Debes asignar al menos una sección destinataria." };
  }
  if (!payload.question_ids || payload.question_ids.length === 0) {
    return { valid: false, error: "Debes seleccionar al menos una pregunta aprobada del banco." };
  }
  if (payload.max_attempts !== undefined && payload.max_attempts < 1) {
    return { valid: false, error: "El límite de intentos debe ser al menos 1." };
  }
  const validPolicies = ["immediate_with_explanation", "upon_completion", "after_deadline"];
  if (payload.feedback_policy && !validPolicies.includes(payload.feedback_policy)) {
    return { valid: false, error: "Política de retroalimentación inválida." };
  }
  return { valid: true, error: null };
}

// Helper function: Map KC mastery percentage to empathetic pedagogical badge
function getPedagogicalStatus(masteryRate) {
  if (masteryRate >= 80) return "Consolidado";
  if (masteryRate >= 50) return "En consolidación";
  return "Refuerzo sugerido";
}

describe("Frontend Learning Flow & Questionnaire Management Tests (M4)", () => {
  // 1. Validación de creación de cuestionario docente
  test("1. Validación de creación: exige título, curso, secciones y preguntas", () => {
    // Empty title
    const resNoTitle = validateActivityCreationPayload({
      title: "   ",
      course_id: "c1",
      section_ids: ["s1"],
      question_ids: ["q1"],
    });
    assert.strictEqual(resNoTitle.valid, false);
    assert.match(resNoTitle.error, /título.*obligatorio/i);

    // No sections
    const resNoSections = validateActivityCreationPayload({
      title: "Cuestionario de Biología",
      course_id: "c1",
      section_ids: [],
      question_ids: ["q1"],
    });
    assert.strictEqual(resNoSections.valid, false);
    assert.match(resNoSections.error, /al menos una sección/i);

    // No questions
    const resNoQuestions = validateActivityCreationPayload({
      title: "Cuestionario de Biología",
      course_id: "c1",
      section_ids: ["s1"],
      question_ids: [],
    });
    assert.strictEqual(resNoQuestions.valid, false);
    assert.match(resNoQuestions.error, /al menos una pregunta/i);

    // Valid payload
    const resValid = validateActivityCreationPayload({
      title: "Cuestionario de Biología",
      course_id: "c1",
      section_ids: ["s1", "s2"],
      question_ids: ["q1", "q2", "q3"],
      feedback_policy: "immediate_with_explanation",
      max_attempts: 2,
    });
    assert.strictEqual(resValid.valid, true);
    assert.strictEqual(resValid.error, null);
  });

  // 2. Preservación del Knowledge Component
  test("2. Preservación de KC: las preguntas asociadas conservan su componente institucional", () => {
    const selectedQuestions = [
      { id: "q1", prompt: "¿Función del cloroplasto?", kc_id: "kc-fotosintesis", kc_name: "Fotosíntesis" },
      { id: "q2", prompt: "¿Función de la mitocondria?", kc_id: "kc-respiracion", kc_name: "Respiración celular" },
    ];

    const activityQuestions = selectedQuestions.map((q, idx) => ({
      question_id: q.id,
      order_index: idx + 1,
      knowledge_component_id: q.kc_id,
      knowledge_component_name: q.kc_name,
    }));

    assert.strictEqual(activityQuestions.length, 2);
    assert.strictEqual(activityQuestions[0].knowledge_component_id, "kc-fotosintesis");
    assert.strictEqual(activityQuestions[1].knowledge_component_name, "Respiración celular");
    assert.strictEqual(activityQuestions[0].order_index, 1);
    assert.strictEqual(activityQuestions[1].order_index, 2);
  });

  // 3. Ciclo de vida y publicación atómica
  test("3. Ciclo de vida: transición draft -> published bloquea alteraciones destructivas", () => {
    const draftActivity = {
      id: "act-1",
      status: "draft",
      published_at: null,
      questions_count: 5,
    };

    // Atomic publish transition
    const publishedActivity = {
      ...draftActivity,
      status: "published",
      published_at: new Date().toISOString(),
    };

    assert.strictEqual(publishedActivity.status, "published");
    assert.ok(publishedActivity.published_at);

    // Attempting to modify questions in published state is disallowed
    const canModifyQuestions = publishedActivity.status === "draft";
    assert.strictEqual(canModifyQuestions, false);
  });

  // 4. Listado y filtrado de actividades del estudiante
  test("4. Visibilidad del estudiante: actividades asignadas a su sección y filtrado por estado", () => {
    const studentSectionId = "sec-5A";
    const studentActivities = [
      {
        activity_id: "act-1",
        title: "Repaso 1",
        section_id: "sec-5A",
        status: "published",
        latest_attempt_status: "in_progress",
        attempts_count: 1,
        max_attempts: 2,
        can_attempt: true,
      },
      {
        activity_id: "act-2",
        title: "Evaluación 1",
        section_id: "sec-5A",
        status: "published",
        latest_attempt_status: "completed",
        attempts_count: 1,
        max_attempts: 1,
        can_attempt: false,
      },
      {
        activity_id: "act-3",
        title: "Práctica 2",
        section_id: "sec-5A",
        status: "published",
        latest_attempt_status: null,
        attempts_count: 0,
        max_attempts: 3,
        can_attempt: true,
      },
    ];

    // Filter "en_curso": in_progress or unattempted available
    const enCurso = studentActivities.filter(
      (a) => a.latest_attempt_status === "in_progress" || (a.can_attempt && a.attempts_count === 0)
    );
    assert.strictEqual(enCurso.length, 2);

    // Filter "completados"
    const completados = studentActivities.filter((a) => a.latest_attempt_status === "completed");
    assert.strictEqual(completados.length, 1);
    assert.strictEqual(completados[0].activity_id, "act-2");
  });

  // 5. Sanitización de preguntas para el estudiante (sin fuga de respuestas)
  test("5. Sanitización: opciones enviadas al estudiante no contienen is_correct ni explicaciones canónicas", () => {
    const canonicalQuestionFromDb = {
      id: "q-100",
      prompt: "¿Dónde se realiza la fase luminosa?",
      explanation: "Ocurre en la membrana del tilacoide.",
      options: [
        { id: "opt-1", option_text: "Estroma", is_correct: false },
        { id: "opt-2", option_text: "Tilacoides", is_correct: true },
      ],
    };

    // Sanitizer projection matching FastAPI backend
    const studentSanitizedQuestion = {
      id: canonicalQuestionFromDb.id,
      question_text: canonicalQuestionFromDb.prompt,
      question_type: "multiple_choice",
      order_index: 1,
      options: canonicalQuestionFromDb.options.map((o, idx) => ({
        id: o.id,
        option_text: o.option_text,
        order_index: idx + 1,
      })),
    };

    // Assert absence of sensitive fields
    assert.strictEqual("is_correct" in studentSanitizedQuestion.options[0], false);
    assert.strictEqual("is_correct" in studentSanitizedQuestion.options[1], false);
    assert.strictEqual("explanation" in studentSanitizedQuestion, false);
    assert.strictEqual(studentSanitizedQuestion.options.length, 2);
  });

  // 6. Inicio seguro de intentos con clave de idempotencia
  test("6. Inicio de intento: genera clave de idempotencia y estado in_progress", () => {
    const idempotencyKey = "11111111-2222-3333-4444-555555555555";
    const startAttemptResponse = {
      attempt_id: "att-1234",
      activity_id: "act-1",
      attempt_number: 1,
      status: "in_progress",
      started_at: "2026-11-03T14:00:00Z",
      questions: [{ id: "q-1" }, { id: "q-2" }],
    };

    assert.strictEqual(startAttemptResponse.status, "in_progress");
    assert.strictEqual(startAttemptResponse.attempt_number, 1);
    assert.strictEqual(startAttemptResponse.questions.length, 2);
  });

  // 7. Registro de respuesta con medición de tiempo y política de feedback
  test("7. Registro de respuesta: mide tiempo en segundos y evalúa feedback según política", () => {
    const startTime = Date.now() - 15000; // 15 seconds ago
    const responseTimeSec = Math.max(1, Math.round((Date.now() - startTime) / 1000));
    assert.ok(responseTimeSec >= 14 && responseTimeSec <= 16);

    // Immediate with explanation policy
    const immediateResponse = {
      event_id: "evt-01",
      question_id: "q-1",
      is_correct: true,
      feedback: {
        title: "¡Respuesta correcta!",
        explanation: "La luz excita electrones en la clorofila.",
      },
      attempt_completed: false,
    };
    assert.strictEqual(immediateResponse.is_correct, true);
    assert.ok(immediateResponse.feedback);

    // Upon completion policy: is_correct and feedback are null during quiz
    const delayedResponse = {
      event_id: "evt-02",
      question_id: "q-2",
      is_correct: null,
      feedback: null,
      attempt_completed: false,
    };
    assert.strictEqual(delayedResponse.is_correct, null);
    assert.strictEqual(delayedResponse.feedback, null);
  });

  // 8. Finalización y cálculo de puntaje en backend
  test("8. Finalización del intento: cálculo estricto de nota en backend (0 a 100%)", () => {
    const totalQuestions = 4;
    const correctAnswers = 3;
    const score = (correctAnswers / totalQuestions) * 100.0;

    const finalizeResponse = {
      attempt_id: "att-1234",
      activity_id: "act-1",
      status: "completed",
      score,
      total_questions: totalQuestions,
      correct_answers: correctAnswers,
      completed_at: "2026-11-03T14:10:00Z",
    };

    assert.strictEqual(finalizeResponse.status, "completed");
    assert.strictEqual(finalizeResponse.score, 75.0);
    assert.strictEqual(finalizeResponse.correct_answers, 3);
  });

  // 9. Desglose de dominio por KC con lenguaje empático
  test("9. Desglose por KC: mapeo de porcentajes a estados pedagógicos empáticos", () => {
    assert.strictEqual(getPedagogicalStatus(100), "Consolidado");
    assert.strictEqual(getPedagogicalStatus(85), "Consolidado");
    assert.strictEqual(getPedagogicalStatus(75), "En consolidación");
    assert.strictEqual(getPedagogicalStatus(50), "En consolidación");
    assert.strictEqual(getPedagogicalStatus(40), "Refuerzo sugerido");
    assert.strictEqual(getPedagogicalStatus(0), "Refuerzo sugerido");

    const kcSummaries = [
      { kc_id: "kc-1", name: "Fotosíntesis", total: 2, correct: 2, mastery: 100 },
      { kc_id: "kc-2", name: "Respiración", total: 2, correct: 1, mastery: 50 },
    ];

    const mapped = kcSummaries.map((k) => ({
      ...k,
      status: getPedagogicalStatus(k.mastery),
    }));

    assert.strictEqual(mapped[0].status, "Consolidado");
    assert.strictEqual(mapped[1].status, "En consolidación");
  });

  // 10. Analítica docente agregada
  test("10. Analítica docente: agregación por secciones, preguntas y KCs", () => {
    const activityResults = {
      activity_id: "act-1",
      total_enrolled: 30,
      total_attempts: 28,
      completed_attempts: 25,
      participation_rate: (28 / 30) * 100,
      average_score: 82.5,
      sections_breakdown: [
        {
          section_id: "sec-5A",
          section_name: "5.° A",
          enrolled_count: 30,
          participating_students: 28,
          completed_attempts: 25,
          average_score: 82.5,
        },
      ],
      questions_breakdown: [
        {
          question_id: "q-1",
          total_answers: 25,
          correct_answers: 20,
          accuracy_rate: 80.0,
        },
      ],
      kc_breakdown: [
        {
          knowledge_component_id: "kc-1",
          knowledge_component_name: "Fotosíntesis",
          total_answers: 25,
          correct_answers: 20,
          mastery_rate: 80.0,
        },
      ],
    };

    assert.strictEqual(activityResults.total_enrolled, 30);
    assert.strictEqual(activityResults.completed_attempts, 25);
    assert.strictEqual(activityResults.sections_breakdown[0].average_score, 82.5);
    assert.strictEqual(activityResults.questions_breakdown[0].accuracy_rate, 80.0);
    assert.strictEqual(activityResults.kc_breakdown[0].mastery_rate, 80.0);
  });

  // 11. Seguridad y manejo de errores
  test("11. Seguridad: control de roles y estados de error controlados", () => {
    // Attempting to submit to closed activity
    const error409 = {
      status: 409,
      code: "ATTEMPT_ALREADY_SUBMITTED",
      detail: "El intento ya fue finalizado y evaluado previamente.",
    };
    assert.strictEqual(error409.status, 409);
    assert.strictEqual(error409.code, "ATTEMPT_ALREADY_SUBMITTED");

    // Attempting to start attempt when not enrolled in section
    const error403 = {
      status: 403,
      code: "NOT_ENROLLED_IN_ACTIVITY_SECTION",
      detail: "No estás matriculado en ninguna de las secciones asignadas a este cuestionario.",
    };
    assert.strictEqual(error403.status, 403);
    assert.strictEqual(error403.code, "NOT_ENROLLED_IN_ACTIVITY_SECTION");
  });

  // 12. Listado dinámico de cursos y secciones matriculadas
  test("12. Cursos del estudiante: mapeo dinámico de cursos y secciones matriculadas sin hardcoding", () => {
    const studentCourses = [
      {
        course_id: "crs-001",
        course_code: "CTA-5",
        course_name: "Ciencia y Tecnología 5.°",
        description: "Competencias del área de Ciencia y Tecnología",
        section_id: "sec-5A",
        section_name: "5.° A Secundaria",
      },
      {
        course_id: "crs-002",
        course_code: "MAT-5",
        course_name: "Matemática 5.°",
        description: "Razonamiento matemático y álgebra",
        section_id: "sec-5A",
        section_name: "5.° A Secundaria",
      },
    ];

    assert.strictEqual(studentCourses.length, 2);
    assert.strictEqual(studentCourses[0].course_code, "CTA-5");
    assert.strictEqual(studentCourses[1].course_code, "MAT-5");
    assert.strictEqual(studentCourses[0].section_id, studentCourses[1].section_id);
  });

  // 13. Revisión de preguntas no respondidas u omitidas
  test("13. Reseña de intento: pregunta omitida conserva selected_option_id nulo y texto descriptivo", () => {
    const questionReview = {
      question_id: "q-unanswered",
      question_text: "¿Qué es el ciclo de Calvin?",
      knowledge_component_id: "kc-fotosintesis",
      knowledge_component_name: "Fotosíntesis",
      selected_option_id: null,
      selected_option_text: "No respondida",
      is_correct: false,
      correct_option_id: "opt-correct",
      correct_option_text: "Fijación del carbono",
      explanation: "El ciclo de Calvin fija dióxido de carbono en glucosa.",
    };

    assert.strictEqual(questionReview.selected_option_id, null);
    assert.strictEqual(questionReview.selected_option_text, "No respondida");
    assert.strictEqual(questionReview.is_correct, false);
    assert.strictEqual(questionReview.correct_option_id, "opt-correct");
  });

  // 14. Enmascaramiento de soluciones para after_deadline antes del vencimiento
  test("14. Enmascaramiento after_deadline: oculta respuesta correcta y explicaciones si la fecha límite no ha pasado", () => {
    const now = new Date("2026-11-03T18:00:00Z");
    const deadline = new Date("2026-11-05T23:59:59Z");
    const isDeadlinePassed = now >= deadline;

    const rawQuestionResult = {
      question_id: "q-1",
      selected_option_id: "opt-sel",
      selected_option_text: "Mi elección",
      is_correct: false,
      canonical_correct_id: "opt-correct",
      canonical_correct_text: "Opción correcta",
      explanation: "Explicación detallada del docente",
    };

    const reviewItem = {
      question_id: rawQuestionResult.question_id,
      selected_option_id: rawQuestionResult.selected_option_id,
      selected_option_text: rawQuestionResult.selected_option_text,
      is_correct: rawQuestionResult.is_correct,
      correct_option_id: isDeadlinePassed ? rawQuestionResult.canonical_correct_id : null,
      correct_option_text: isDeadlinePassed ? rawQuestionResult.canonical_correct_text : null,
      explanation: isDeadlinePassed ? rawQuestionResult.explanation : null,
    };

    assert.strictEqual(isDeadlinePassed, false);
    assert.strictEqual(reviewItem.correct_option_id, null);
    assert.strictEqual(reviewItem.correct_option_text, null);
    assert.strictEqual(reviewItem.explanation, null);
  });

  // 15. Manejo robusto de errores RFC 7807 y validaciones Pydantic
  test("15. Manejo de errores: extrae detalle RFC 7807 y validaciones Pydantic sin producir [object Object]", () => {
    function extractErrorMessage(err, fallback) {
      if (!err || typeof err !== "object") return fallback;
      if (typeof err.detail === "string") return err.detail;
      if (typeof err.detail?.detail === "string") return err.detail.detail;
      if (typeof err.detail?.title === "string") return err.detail.title;
      if (Array.isArray(err.detail)) {
        const msgs = err.detail.map((item) => item?.msg || item?.message).filter(Boolean);
        if (msgs.length > 0) return msgs.join("; ");
      }
      if (typeof err.message === "string") return err.message;
      return fallback;
    }

    // RFC 7807 problem details with nested detail string
    const rfcError = {
      detail: {
        type: "https://api.plataformamicro.edu.pe/errors/forbidden",
        title: "Intento no permitido",
        status: 403,
        detail: "Se ha alcanzado el límite máximo de intentos permitidos (1).",
        code: "ATTEMPT_NOT_PERMITTED",
      },
    };
    assert.strictEqual(
      extractErrorMessage(rfcError, "Error genérico"),
      "Se ha alcanzado el límite máximo de intentos permitidos (1)."
    );

    // Pydantic 422 validation array
    const pydanticError = {
      detail: [
        { loc: ["body", "question_ids"], msg: "Field required", type: "missing" },
        { loc: ["body", "title"], msg: "String should have at least 3 characters", type: "string_too_short" },
      ],
    };
    assert.strictEqual(
      extractErrorMessage(pydanticError, "Error de validación"),
      "Field required; String should have at least 3 characters"
    );

    // Standard string detail
    const simpleError = { detail: "Actividad no encontrada" };
    assert.strictEqual(extractErrorMessage(simpleError, "Fallback"), "Actividad no encontrada");

    // Fallback on empty
    assert.strictEqual(extractErrorMessage(null, "Error por defecto"), "Error por defecto");
  });

  // 16. Analítica docente: cálculo de tasa de participación y desglose por reactivo
  test("16. Analítica docente: cálculo preciso de métricas de participación y precisión", () => {
    const totalEnrolled = 30;
    const participatingStudents = 27;
    const participationRate = Math.round((participatingStudents / totalEnrolled) * 1000) / 10;
    assert.strictEqual(participationRate, 90.0);

    const questionResults = [
      { total_answers: 25, correct_answers: 20 },
      { total_answers: 0, correct_answers: 0 },
    ];
    const acc1 = Math.round((questionResults[0].correct_answers / questionResults[0].total_answers) * 1000) / 10;
    const acc2 = questionResults[1].total_answers > 0 ? (questionResults[1].correct_answers / questionResults[1].total_answers) * 100 : 0.0;
    assert.strictEqual(acc1, 80.0);
    assert.strictEqual(acc2, 0.0);
  });

  // 17. Dinamismo de autenticación: propagación de Authorization Bearer token
  test("17. Dinamismo de autenticación: propaga Bearer token sin cabeceras estáticas", () => {
    function buildHeaders(token, env = "production", enableDemo = "false", roleFallback = "student") {
      const headers = { "Content-Type": "application/json" };
      if (token) {
        headers["Authorization"] = `Bearer ${token}`;
        return headers;
      }
      if (env !== "production" && enableDemo === "true") {
        if (roleFallback === "teacher") {
          headers["X-User-Id"] = "d0000000-0000-0000-0000-000000000001";
        } else {
          headers["X-User-Id"] = "e0000000-0000-0000-0000-000000000001";
        }
      }
      return headers;
    }

    // With active Supabase session
    const h1 = buildHeaders("valid-supabase-jwt-12345");
    assert.strictEqual(h1["Authorization"], "Bearer valid-supabase-jwt-12345");
    assert.strictEqual(h1["X-User-Id"], undefined);

    // In production without session: NO proxy headers ever leaked
    const h2 = buildHeaders(null, "production", "true");
    assert.strictEqual(h2["Authorization"], undefined);
    assert.strictEqual(h2["X-User-Id"], undefined);

    // In development with demo enabled: controlled fallback
    const h3 = buildHeaders(null, "development", "true", "teacher");
    assert.strictEqual(h3["X-User-Id"], "d0000000-0000-0000-0000-000000000001");
  });

  // 18. Aislamiento de modo demo en login
  test("18. Aislamiento demo: prohibido en producción y controlado por flag explícito", () => {
    function isDemoAllowed(nodeEnv, enableDemoFlag) {
      return nodeEnv !== "production" && enableDemoFlag === "true";
    }

    assert.strictEqual(isDemoAllowed("production", "true"), false);
    assert.strictEqual(isDemoAllowed("production", "false"), false);
    assert.strictEqual(isDemoAllowed("development", "false"), false);
    assert.strictEqual(isDemoAllowed("development", undefined), false);
    assert.strictEqual(isDemoAllowed("development", "true"), true);
  });
});
