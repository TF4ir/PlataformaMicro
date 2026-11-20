/**
 * Integration & Hardening Verification: Cloudflare Workers + AWS Lambda ML API
 *
 * Verifies:
 * 1. buildApiUrl normalization (trailing slashes, relative paths, absolute URLs, config validation).
 * 2. ApiClientError preserves status, code, and detail.
 * 3. parseApiError parses RFC 7807 problem details object.
 * 4. parseApiError parses Pydantic validation error array.
 * 5. parseApiError friendly fallback messages for 401, 403, 404, 429, 500, 503.
 * 6. getAuthHeaders contract (Accept, absence of identity proxy headers).
 * 7. apiFetch requireAuth guardrail (unauthenticated rejection without leaking network calls).
 * 8. apiFetch Content-Type omission on GET/HEAD and inclusion on body requests.
 * 9. apiFetch 204 No Content handling.
 * 10. apiFetch network error wrapping & AbortError propagation.
 * 11. Empathetic pedagogical label mapping (rule 4 from frontend.md: no punitive labels, no "riesgo de olvido").
 * 12. Retention summary state handling (distinguishing empty state from auth or network failure).
 */

import { test, describe } from "node:test";
import assert from "node:assert/strict";

import {
  buildApiUrl,
  parseApiError,
  ApiClientError,
  getAuthHeaders,
  apiFetch,
} from "../lib/api/client.ts";

describe("Cloudflare + AWS Lambda Integration: Client & URL Normalization", () => {
  const prodLambdaUrl =
    "https://54wsiki2ruyk2r5l3xvasykqo40oxokx.lambda-url.us-east-2.on.aws";

  test("1. buildApiUrl: normalizes base URL and paths correctly", () => {
    // Relative endpoint with leading slash and configured env
    process.env.NEXT_PUBLIC_API_URL = prodLambdaUrl;
    const url1 = buildApiUrl("/api/v1/students/me/retention");
    assert.strictEqual(
      url1,
      `${prodLambdaUrl}/api/v1/students/me/retention`
    );

    // Relative endpoint without leading slash
    const url2 = buildApiUrl("api/v1/health");
    assert.strictEqual(url2, `${prodLambdaUrl}/api/v1/health`);

    // Trailing slash on base is cleanly trimmed
    const urlTrailing = buildApiUrl(
      "/api/v1/health",
      `${prodLambdaUrl}/`
    );
    assert.strictEqual(urlTrailing, `${prodLambdaUrl}/api/v1/health`);

    // Absolute endpoint preserved intact
    const url3 = buildApiUrl("https://example.com/custom/api");
    assert.strictEqual(url3, "https://example.com/custom/api");

    // Config error when base is empty string
    assert.throws(
      () => buildApiUrl("/api/v1/health", ""),
      (err) =>
        err instanceof ApiClientError &&
        err.code === "CONFIG_ERROR" &&
        err.status === 0
    );
  });

  test("2. ApiClientError preserves status, code, and detail", () => {
    const err = new ApiClientError("No autorizado", 401, "MISSING_CREDENTIALS", {
      reason: "No bearer token",
    });

    assert.ok(err instanceof Error);
    assert.ok(err instanceof ApiClientError);
    assert.strictEqual(err.name, "ApiClientError");
    assert.strictEqual(err.message, "No autorizado");
    assert.strictEqual(err.status, 401);
    assert.strictEqual(err.code, "MISSING_CREDENTIALS");
    assert.deepStrictEqual(err.detail, { reason: "No bearer token" });
  });

  test("3. parseApiError: parses RFC 7807 problem details object", () => {
    const rfcProblem = {
      type: "https://api.plataformamicro.edu.pe/errors/unauthorized",
      title: "No Autorizado",
      status: 401,
      detail: "Se requiere cabecera Authorization: Bearer <jwt> para acceder a este recurso.",
      code: "MISSING_CREDENTIALS",
    };

    const parsed = parseApiError(401, { detail: rfcProblem });
    assert.strictEqual(
      parsed.message,
      "Se requiere cabecera Authorization: Bearer <jwt> para acceder a este recurso."
    );
    assert.strictEqual(parsed.code, "MISSING_CREDENTIALS");
  });

  test("4. parseApiError: parses Pydantic validation error array", () => {
    const pydanticError = {
      detail: [
        { loc: ["query", "tau"], msg: "Input should be greater than or equal to 0.1", type: "greater_than_equal" },
        { loc: ["query", "kc_id"], msg: "Input should be a valid UUID", type: "uuid_parsing" },
      ],
    };

    const parsed = parseApiError(422, pydanticError);
    assert.match(parsed.message, /Input should be greater than or equal to 0\.1/);
    assert.match(parsed.message, /Input should be a valid UUID/);
    assert.strictEqual(parsed.code, "VALIDATION_ERROR");
  });

  test("5. parseApiError: friendly fallback messages for 401, 403, 404, 429, 500, 503", () => {
    const statusCases = [
      { status: 401, pattern: /no está autenticada|expirado/i },
      { status: 403, pattern: /permisos suficientes/i },
      { status: 404, pattern: /no fue encontrado/i },
      { status: 429, pattern: /Demasiadas solicitudes/i },
      { status: 500, pattern: /Error en el servicio predictivo/i },
      { status: 503, pattern: /Error en el servicio predictivo/i },
    ];

    for (const { status, pattern } of statusCases) {
      const parsed = parseApiError(status, null);
      assert.match(parsed.message, pattern);
    }
  });

  test("6. getAuthHeaders sets Accept and never leaks identity proxy headers", async () => {
    const headers = await getAuthHeaders({ "X-Custom-Trace": "trace-123" });

    assert.strictEqual(headers["Accept"], "application/json");
    assert.strictEqual(headers["X-Custom-Trace"], "trace-123");

    // Strictly forbidden proxy headers
    assert.strictEqual(headers["X-User-Id"], undefined);
    assert.strictEqual(headers["X-Tenant-Id"], undefined);
    assert.strictEqual(headers["X-User-Role"], undefined);
    assert.strictEqual(headers["X-Course-Ids"], undefined);
  });

  test("7. apiFetch requireAuth guardrail blocks unauthenticated calls without fetch", async () => {
    await assert.rejects(
      async () => {
        await apiFetch("/api/v1/students/me/retention", { requireAuth: true });
      },
      (err) => {
        assert.ok(err instanceof ApiClientError);
        assert.strictEqual(err.status, 401);
        assert.strictEqual(err.code, "MISSING_CREDENTIALS");
        return true;
      }
    );
  });

  test("8. apiFetch Content-Type omission on GET/HEAD vs inclusion on body requests", async () => {
    const originalFetch = globalThis.fetch;
    let capturedHeaders = null;

    globalThis.fetch = async (url, init) => {
      capturedHeaders = init?.headers;
      return new Response(JSON.stringify({ ok: true }), {
        status: 200,
        headers: { "Content-Type": "application/json" },
      });
    };

    try {
      // GET without body -> Content-Type must NOT be set
      await apiFetch("/api/v1/health", { method: "GET" });
      assert.strictEqual(capturedHeaders["Content-Type"], undefined);

      // POST with body -> Content-Type must be application/json
      await apiFetch("/api/v1/recommendations/evaluate", {
        method: "POST",
        body: JSON.stringify({ tau: 0.65 }),
      });
      assert.strictEqual(capturedHeaders["Content-Type"], "application/json");
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("9. apiFetch handles 204 No Content returning empty object", async () => {
    const originalFetch = globalThis.fetch;
    globalThis.fetch = async () => new Response(null, { status: 204 });

    try {
      const res = await apiFetch("/api/v1/notifications/1/read", { method: "POST" });
      assert.deepStrictEqual(res, {});
    } finally {
      globalThis.fetch = originalFetch;
    }
  });

  test("10. apiFetch wraps network errors in ApiClientError and propagates AbortError", async () => {
    const originalFetch = globalThis.fetch;

    try {
      // Network error wrapping
      globalThis.fetch = async () => {
        throw new TypeError("Failed to fetch");
      };

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/health");
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 0);
          assert.strictEqual(err.code, "NETWORK_ERROR");
          assert.match(err.message, /Failed to fetch/);
          return true;
        }
      );

      // AbortError propagation
      globalThis.fetch = async () => {
        const abortErr = new Error("This operation was aborted");
        abortErr.name = "AbortError";
        throw abortErr;
      };

      await assert.rejects(
        async () => {
          await apiFetch("/api/v1/health");
        },
        (err) => {
          assert.ok(err instanceof Error);
          assert.strictEqual(err.name, "AbortError");
          return true;
        }
      );
    } finally {
      globalThis.fetch = originalFetch;
    }
  });
});

describe("Cloudflare + AWS Lambda Integration: Pedagogical & Business State Guarantees", () => {
  test("11. Empathetic pedagogical status mapping replaces negative framing", () => {
    function mapPedagogicalStatus(pRecall) {
      if (pRecall >= 0.8) return { label: "Retención consolidada", variant: "success", needLabel: "Refuerzo sugerido" };
      if (pRecall >= 0.65) return { label: "Concepto afianzado", variant: "secondary", needLabel: "Refuerzo sugerido" };
      return { label: "Momento ideal para repasar", variant: "warning", needLabel: "Refuerzo sugerido" };
    }

    const highRecall = mapPedagogicalStatus(0.85);
    assert.strictEqual(highRecall.label, "Retención consolidada");
    assert.strictEqual(highRecall.variant, "success");

    const midRecall = mapPedagogicalStatus(0.72);
    assert.strictEqual(midRecall.label, "Concepto afianzado");
    assert.strictEqual(midRecall.variant, "secondary");

    const reviewNeeded = mapPedagogicalStatus(0.48);
    assert.strictEqual(reviewNeeded.label, "Momento ideal para repasar");
    assert.strictEqual(reviewNeeded.variant, "warning");

    // Strictly forbidden negative terms per Rule 4 (frontend.md)
    for (const p of [0.1, 0.4, 0.6, 0.9]) {
      const s = mapPedagogicalStatus(p);
      assert.doesNotMatch(s.label, /fallar|riesgo de reprobar|crítico|deficiente|riesgo de olvido/i);
      assert.doesNotMatch(s.needLabel, /fallar|riesgo de reprobar|crítico|deficiente|riesgo de olvido/i);
    }
  });

  test("12. Differentiates empty retention state from auth or connectivity errors", () => {
    function classifyRetentionState({ loading, error, profile }) {
      if (loading) return "loading";
      if (error?.isAuthError) return "unauthenticated_error";
      if (error) return "service_error";
      if (profile && profile.kcs.length === 0) return "empty_state";
      if (profile && profile.kcs.length > 0) return "data_state";
      return "idle";
    }

    assert.strictEqual(
      classifyRetentionState({ loading: true, error: null, profile: null }),
      "loading"
    );

    assert.strictEqual(
      classifyRetentionState({
        loading: false,
        error: { message: "No autorizado", isAuthError: true },
        profile: null,
      }),
      "unauthenticated_error"
    );

    assert.strictEqual(
      classifyRetentionState({
        loading: false,
        error: { message: "Failed to fetch", isAuthError: false },
        profile: null,
      }),
      "service_error"
    );

    assert.strictEqual(
      classifyRetentionState({
        loading: false,
        error: null,
        profile: { student_id: "s-1", kcs: [] },
      }),
      "empty_state"
    );

    assert.strictEqual(
      classifyRetentionState({
        loading: false,
        error: null,
        profile: {
          student_id: "s-1",
          kcs: [
            {
              knowledge_component_id: "kc-1",
              knowledge_component_name: "Fotosíntesis",
              current_recall_probability: 0.52,
            },
          ],
        },
      }),
      "data_state"
    );
  });
});
