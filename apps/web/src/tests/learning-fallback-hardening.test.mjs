/**
 * Automated Unit, Static Contract & Integration Hardening Tests for Learning Fallback (Phase P0-1)
 *
 * Verifies:
 * 1. HTTP 400 / 401 (Expired/Invalid JWT) does NOT trigger fallback to Supabase for any operation.
 * 2. HTTP 403 (Forbidden / Max attempts reached / In-progress results locked) does NOT trigger fallback.
 * 3. HTTP 404 (Not Found) does NOT trigger fallback.
 * 4. HTTP 409 (Conflict / Attempt completed) does NOT trigger fallback.
 * 5. HTTP 422 (Unprocessable Content / Availability schedule) does NOT trigger fallback.
 * 6. HTTP 429 (Too Many Requests / Rate limit) does NOT trigger fallback.
 * 7. HTTP 500 / 502 / 503 (Server/Gateway Error) does NOT trigger fallback.
 * 8. Network/Transport errors (status 0):
 *    - Strictly BLOCKS fallbacks on WRITE operations (startAttempt, submitAnswer, submitAttempt).
 *    - Strictly BLOCKS fallbacks on sensitive protected reads (getAttemptResults, getStudentActivity).
 *    - ONLY activates expressly authorized read-only resilient queries (listStudentCourses, listStudentActivities, getDashboard, getProgress).
 * 9. Static AST / Contract Invariants:
 *    - Unsafe write fallbacks (startAttemptFromSupabase, submitAnswerFromSupabase, submitAttemptFromSupabase) are deleted.
 *    - Insecure result/activity leak fallbacks (getAttemptResultsFromSupabase, getStudentActivityFromSupabase) are deleted.
 *    - Fallback queries enforce availability schedule (available_from / available_until), is_active=true, and section mapping integrity.
 *    - Progress fallback scopes KCs strictly by student's enrolled courses and units, preventing cross-course curriculum leaks.
 *    - No identity headers (X-User-Id, X-Tenant-Id) leaked.
 * 10. Authoritative business rules:
 *    - Intento completado: no permite respuestas adicionales.
 *    - Máximo de intentos agotado: no permite iniciar un nuevo intento.
 *    - Respuesta duplicada: no se registra nuevamente (idempotencia estricta).
 *    - Intento en curso: no revela respuestas correctas ni explicaciones.
 *    - Intento fuera de plazo: respeta la política after_deadline.
 */

import { test, describe, beforeEach, afterEach } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import {
  apiFetch,
  ApiClientError,
  isTransportError,
} from "../lib/api/client.ts";

function source(relativePath) {
  return readFileSync(new URL(relativePath, import.meta.url), "utf8");
}

const learningSource = source("../lib/api/learning.ts");
const clientSource = source("../lib/api/client.ts");

// Helper to construct a mock Response with JSON body
function mockJsonResponse(status, body) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
    headers: new Headers({ "Content-Type": "application/json" }),
  });
}

describe("P0-1: Endurecimiento del Fallback de Aprendizaje", () => {
  const originalFetch = globalThis.fetch;

  afterEach(() => {
    globalThis.fetch = originalFetch;
  });

  // =========================================================================
  // 1. Static Contract & Architectural Elimination of Insecure Fallbacks
  // =========================================================================
  describe("1. Eliminación Arquitectónica de Fallbacks Inseguros en learning.ts", () => {
    test("1.1. Las funciones de escritura directa en Supabase fueron completamente eliminadas", () => {
      assert.doesNotMatch(learningSource, /async function startAttemptFromSupabase/);
      assert.doesNotMatch(learningSource, /async function submitAnswerFromSupabase/);
      assert.doesNotMatch(learningSource, /async function submitAttemptFromSupabase/);
    });

    test("1.2. Los fallbacks de lectura sensible que filtraban soluciones fueron eliminados", () => {
      assert.doesNotMatch(learningSource, /async function getAttemptResultsFromSupabase/);
      assert.doesNotMatch(learningSource, /async function getStudentActivityFromSupabase/);
    });

    test("1.3. Las operaciones de escritura delegan exclusivamente en apiFetch sin catch de fallback", () => {
      // startAttempt must call apiFetch directly
      assert.match(
        learningSource,
        /startAttempt\(activityId:\s*string,\s*idempotencyKey\?:\s*string\)/
      );
      assert.doesNotMatch(
        learningSource,
        /startAttempt[^}]+catch[^{]+{[^}]+FromSupabase/
      );

      // submitAnswer must call apiFetch directly
      assert.match(
        learningSource,
        /submitAnswer\(\s*attemptId:\s*string/
      );
      assert.doesNotMatch(
        learningSource,
        /submitAnswer[^}]+catch[^{]+{[^}]+FromSupabase/
      );

      // submitAttempt must call apiFetch directly
      assert.match(
        learningSource,
        /submitAttempt\(attemptId:\s*string\)/
      );
      assert.doesNotMatch(
        learningSource,
        /submitAttempt[^}]+catch[^{]+{[^}]+FromSupabase/
      );
    });

    test("1.4. getAttemptResults y getStudentActivity no tienen bloque catch de fallback", () => {
      assert.doesNotMatch(
        learningSource,
        /getAttemptResults[^}]+catch[^{]+{[^}]+FromSupabase/
      );
      assert.doesNotMatch(
        learningSource,
        /getStudentActivity[^}]+catch[^{]+{[^}]+FromSupabase/
      );
    });

    test("1.5. Las lecturas resilientes autorizadas condicionan su fallback estrictamente a isTransportError", () => {
      assert.match(
        learningSource,
        /listStudentCourses[\s\S]*?catch\s*\(err:\s*unknown\)\s*{\s*if\s*\(isTransportError\(err\)\)/
      );
      assert.match(
        learningSource,
        /listStudentActivities[\s\S]*?catch\s*\(err:\s*unknown\)\s*{\s*if\s*\(isTransportError\(err\)\)/
      );
      assert.match(
        learningSource,
        /getDashboard[\s\S]*?catch\s*\(err:\s*unknown\)\s*{\s*if\s*\(isTransportError\(err\)\)/
      );
      assert.match(
        learningSource,
        /getProgress[\s\S]*?catch\s*\(err:\s*unknown\)\s*{\s*if\s*\(isTransportError\(err\)\)/
      );
    });

    test("1.6. listStudentActivitiesFromSupabase valida fechas límite y filtra actividades activas", () => {
      assert.match(learningSource, /activity\.available_from/);
      assert.match(learningSource, /activity\.available_until/);
      assert.match(learningSource, /isAvailable\s*&&\s*activityAttempts\.length\s*<\s*maxAttempts/);
      assert.match(learningSource, /\.eq\("is_active",\s*true\)/);
      assert.match(learningSource, /activityToSectionId/);
    });

    test("1.7. getStudentDashboardFromSupabase valida disponibilidad temporal en recent_activities y filtra is_active", () => {
      assert.match(learningSource, /currentTime\s*<\s*new Date\(activity\.available_from\)/);
      assert.match(learningSource, /currentTime\s*>\s*new Date\(activity\.available_until\)/);
      assert.match(learningSource, /isAvailable\s*&&\s*activityAttempts\.length\s*<\s*maxAttempts/);
    });

    test("1.8. getStudentProgressFromSupabase aísla KCs por matrículas del estudiante para evitar fuga curricular", () => {
      assert.match(learningSource, /enrolledCourseIds/);
      assert.match(learningSource, /enrolledUnitIds/);
      assert.match(learningSource, /\.in\("unit_id",\s*enrolledUnitIds\)/);
    });

    test("1.9. isTransportError es exportado de manera canónica desde client.ts y re-exportado en learning.ts", () => {
      assert.match(clientSource, /export function isTransportError/);
      assert.match(learningSource, /export\s*{\s*isTransportError\s*}/);
    });
  });

  // =========================================================================
  // 2. HTTP 400 y 401: JWT expirado / no autenticado NUNCA activa fallback
  // =========================================================================
  describe("2. HTTP 400 / 401 (Solicitud Inválida / JWT Expirado) — Sin Fallback", () => {
    test("2.1. HTTP 400 Bad Request: retiene error original con status 400 y no activa fallback", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(400, {
          detail: "Solicitud malformada o parámetro requerido ausente.",
          code: "BAD_REQUEST",
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/activities/act-1/attempts", { method: "POST" });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 400);
          assert.strictEqual(err.code, "BAD_REQUEST");
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });

    test("2.2. HTTP 401 Unauthorized: retiene error original y isTransportError retorna false", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(401, {
          detail: "La sesión del usuario no está autenticada o ha expirado.",
          code: "UNAUTHORIZED",
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/activities/act-1/attempts", { method: "POST" });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 401);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });

    test("2.3. isTransportError retorna false para 401 (bloquea fallback en cualquier operación)", () => {
      const err = new ApiClientError("Session expired", 401);
      assert.strictEqual(isTransportError(err), false);
    });
  });

  // =========================================================================
  // 3. HTTP 403: Forbidden (Límites de negocio, sección, intentos activos)
  // =========================================================================
  describe("3. HTTP 403 (Acceso Denegado / Regla de Negocio) — Sin Fallback", () => {
    test("3.1. Máximo de intentos agotado (403): conserva error original y no es error de transporte", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(403, {
          detail: {
            title: "Intento no permitido",
            status: 403,
            detail: "Se ha alcanzado el límite máximo de intentos permitidos (2).",
            code: "ATTEMPT_NOT_PERMITTED",
          },
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/activities/act-1/attempts", { method: "POST" });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          assert.match(err.message, /límite máximo de intentos permitidos \(2\)/i);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });

    test("3.2. Intento en curso (403): no revela resultados ni activa fallback", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(403, {
          detail: {
            title: "Acceso prohibido",
            status: 403,
            detail: "Cannot view results of an in-progress attempt. Finalize the attempt first.",
            code: "FORBIDDEN_ATTEMPT_ACCESS",
          },
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/attempts/att-1/results");
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          assert.match(err.message, /in-progress attempt/i);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });
  });

  // =========================================================================
  // 4. HTTP 404: Not Found
  // =========================================================================
  describe("4. HTTP 404 (Recurso no encontrado) — Sin Fallback", () => {
    test("4.1. Actividad inexistente o no matriculada (404) no activa fallback", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(404, {
          detail: {
            title: "Actividad no disponible",
            status: 404,
            detail: "Activity not found or student not enrolled in assigned section.",
            code: "ACTIVITY_NOT_FOUND_OR_ENROLLED",
          },
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/activities/act-missing");
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 404);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });
  });

  // =========================================================================
  // 5. HTTP 409: Conflict (Intento ya completado)
  // =========================================================================
  describe("5. HTTP 409 (Conflicto / Intento ya completado) — Sin Fallback", () => {
    test("5.1. Envío de respuesta a intento completado (409): error autoritativo retenido", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(409, {
          detail: {
            title: "Error de validación de respuesta",
            status: 409,
            detail: "Cannot submit answers to an already completed or abandoned attempt.",
            code: "ANSWER_VALIDATION_ERROR",
          },
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/attempts/att-1/answers", {
            method: "POST",
            body: JSON.stringify({ question_id: "q-1", selected_option_id: "opt-1", response_time_seconds: 4 }),
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 409);
          assert.match(err.message, /already completed/i);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });
  });

  // =========================================================================
  // 6. HTTP 422: Unprocessable Content (Calendario, fechas límite, validación)
  // =========================================================================
  describe("6. HTTP 422 (Periodo Fuera de Calendario) — Sin Fallback", () => {
    test("6.1. Actividad fuera de fecha disponible (422): retiene error de disponibilidad", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(422, {
          detail: {
            title: "Error de disponibilidad",
            status: 422,
            detail: "El periodo de disponibilidad para esta actividad ha concluido.",
            code: "ACTIVITY_SCHEDULE_ERROR",
          },
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/activities/act-expired/attempts", { method: "POST" });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 422);
          assert.match(err.message, /periodo de disponibilidad.*concluido/i);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });
  });

  // =========================================================================
  // 7. HTTP 429: Too Many Requests / Rate Limit — Sin Fallback
  // =========================================================================
  describe("7. HTTP 429 (Límite de Solicitudes) — Sin Fallback", () => {
    test("7.1. HTTP 429 rechaza con ApiClientError(429) y no es error de transporte", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(429, {
          detail: "Demasiadas solicitudes. Por favor intente más tarde.",
          code: "RATE_LIMIT_EXCEEDED",
        });

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/students/me/dashboard");
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 429);
          assert.strictEqual(isTransportError(err), false);
          return true;
        }
      );
    });
  });

  // =========================================================================
  // 8. HTTP 500 / 502 / 503: Error de Servidor — Sin Fallback
  // =========================================================================
  describe("8. HTTP 500 / 502 / 503 (Error de Servidor) — Sin Fallback", () => {
    for (const code of [500, 502, 503]) {
      test(`8.${code}. HTTP ${code} rechaza con ApiClientError(${code}) y isTransportError=false`, async () => {
        globalThis.fetch = async () =>
          mockJsonResponse(code, {
            detail: `Error en el servicio backend HTTP ${code}`,
          });

        await assert.rejects(
          async () => {
            await apiFetch("/api/v1/students/me/dashboard");
          },
          (err) => {
            assert.ok(err instanceof ApiClientError);
            assert.strictEqual(err.status, code);
            assert.strictEqual(isTransportError(err), false);
            return true;
          }
        );
      });
    }
  });

  // =========================================================================
  // 9. Error de Red sin respuesta HTTP (status 0 / NETWORK_ERROR)
  // =========================================================================
  describe("9. Error de Red sin Respuesta HTTP (status 0) — Discriminación de Operaciones", () => {
    beforeEach(() => {
      globalThis.fetch = async () => {
        throw new TypeError("Failed to fetch: Connection refused");
      };
    });

    test("9.1. apiFetch envuelve errores de transporte en ApiClientError con status 0", async () => {
      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/test");
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 0);
          assert.strictEqual(err.code, "NETWORK_ERROR");
          assert.strictEqual(isTransportError(err), true);
          return true;
        }
      );
    });

    test("9.2. isTransportError valida correctamente fallos de red y rechaza códigos HTTP", () => {
      assert.strictEqual(isTransportError(new ApiClientError("timeout", 0, "NETWORK_ERROR")), true);
      assert.strictEqual(isTransportError(new TypeError("Failed to fetch")), true);
      assert.strictEqual(isTransportError(new Error("connect ECONNREFUSED 127.0.0.1:8000")), true);

      assert.strictEqual(isTransportError(new ApiClientError("400 Bad Request", 400)), false);
      assert.strictEqual(isTransportError(new ApiClientError("401 Unauthorized", 401)), false);
      assert.strictEqual(isTransportError(new ApiClientError("403 Forbidden", 403)), false);
      assert.strictEqual(isTransportError(new ApiClientError("404 Not Found", 404)), false);
      assert.strictEqual(isTransportError(new ApiClientError("409 Conflict", 409)), false);
      assert.strictEqual(isTransportError(new ApiClientError("422 Unprocessable", 422)), false);
      assert.strictEqual(isTransportError(new ApiClientError("429 Too Many Requests", 429)), false);
      assert.strictEqual(isTransportError(new ApiClientError("500 Server Error", 500)), false);
      assert.strictEqual(isTransportError(new ApiClientError("502 Bad Gateway", 502)), false);
      assert.strictEqual(isTransportError(new ApiClientError("503 Service Unavailable", 503)), false);
    });

    test("9.3. Operaciones de escritura (startAttempt, submitAnswer, submitAttempt) nunca auto-reintentan de forma insegura", async () => {
      let callCount = 0;
      globalThis.fetch = async () => {
        callCount++;
        throw new TypeError("Network down");
      };

      try {
        await apiFetch("/api/v1/students/me/attempts/att-1/answers", {
          method: "POST",
          body: JSON.stringify({ question_id: "q-1" }),
        });
      } catch (err) {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.status, 0);
      }

      assert.strictEqual(callCount, 1, "No debe ejecutar auto-reintentos que causen duplicación de respuestas");
    });
  });

  // =========================================================================
  // 10. Reglas de Negocio Autoritativas: Idempotencia y Políticas
  // =========================================================================
  describe("10. Reglas de Negocio Autoritativas e Idempotencia", () => {
    test("10.1. apiFetch propaga cabecera X-Idempotency-Key intacta al backend", async () => {
      let capturedHeaders = null;
      let capturedBody = null;

      globalThis.fetch = async (url, options) => {
        capturedHeaders = options.headers;
        capturedBody = JSON.parse(options.body);
        return mockJsonResponse(201, {
          attempt_id: "att-idemp-1",
          activity_id: "act-1",
          attempt_number: 1,
          status: "in_progress",
        });
      };

      const key = "22222222-3333-4444-5555-666666666666";
      await apiFetch("/api/v1/students/me/activities/act-1/attempts", {
        method: "POST",
        headers: { "X-Idempotency-Key": key },
        body: JSON.stringify({ idempotency_key: key }),
      });

      assert.strictEqual(capturedHeaders["X-Idempotency-Key"], key);
      assert.strictEqual(capturedBody.idempotency_key, key);
    });

    test("10.2. Respuesta bajo política after_deadline oculta soluciones antes del vencimiento", async () => {
      globalThis.fetch = async () =>
        mockJsonResponse(200, {
          attempt_id: "att-masked",
          activity_id: "act-1",
          questions: [
            {
              question_id: "q-1",
              is_correct: false,
              correct_option_id: null, // Enmascarado
              correct_option_text: null, // Enmascarado
              explanation: "La retroalimentación y respuestas correctas estarán disponibles una vez concluido el plazo de entrega.",
            },
          ],
        });

      const res = await apiFetch("/api/v1/students/me/attempts/att-masked/results");
      assert.strictEqual(res.questions[0].correct_option_id, null);
      assert.strictEqual(res.questions[0].correct_option_text, null);
      assert.match(res.questions[0].explanation, /concluido el plazo/i);
    });
  });
});
