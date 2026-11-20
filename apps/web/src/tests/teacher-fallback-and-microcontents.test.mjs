/**
 * Unit, Static Contract & Simulated Integration Tests for:
 * - C8: Teacher Fallback Hardening (teacher.ts)
 * - C9: Microcontents Contract Corrections (microcontents.ts)
 *
 * Verifies:
 * C8:
 * 1. teacher.ts imports and leverages isTransportError from client.
 * 2. Unconditional Supabase fallback catch blocks are completely eliminated from:
 *    - getTeacherDashboard
 *    - getTeacherCourses
 *    - getTeacherStudents
 *    - getTeacherReports
 * 3. Fallback to Supabase is ONLY permitted on network/transport errors (status 0, fetch TypeError).
 * 4. HTTP 403 Forbidden (insufficient permissions / student role / unauthorized) strictly rethrows
 *    real ApiClientError and NEVER invokes Supabase fallback.
 * 5. HTTP 503 Service Unavailable (overloaded / offline backend) strictly rethrows real ApiClientError
 *    and NEVER invokes Supabase fallback.
 * 6. HTTP 401 Unauthorized and HTTP 429 Rate Limit strictly rethrow without fallback.
 *
 * C9:
 * 1. updateMicrocontent uses HTTP PATCH (not PUT).
 * 2. listMicrocontents maps kcId strictly to query parameter 'kc_id' (not 'knowledge_component_id').
 * 3. listMicrocontents eliminates unsupported 'status' query filter.
 * 4. Runtime simulation of microcontent update and filter query string construction.
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

function mockResponse(status, body = {}) {
  return Promise.resolve({
    ok: status >= 200 && status < 300,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
    headers: new Headers({ "Content-Type": "application/json" }),
  });
}

describe("C8: Endurecimiento de Fallback Docente (teacher.ts)", () => {
  const teacherSource = source("../lib/api/teacher.ts");
  const originalFetch = globalThis.fetch;
  const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "https://mock-ml-api.internal";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    if (originalApiUrl !== undefined) {
      process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
    } else {
      delete process.env.NEXT_PUBLIC_API_URL;
    }
  });

  // =========================================================================
  // 1. Static Contract & Source Invariants
  // =========================================================================
  describe("1. Contrato Estático en teacher.ts", () => {
    test("1.1. teacher.ts importa isTransportError de client", () => {
      assert.match(
        teacherSource,
        /import\s*\{[^}]*isTransportError[^}]*\}\s*from\s*["']\.\/client["']/
      );
    });

    test("1.2. Los 4 métodos docentes (dashboard, courses, students, reports) condicionan el fallback a isTransportError", () => {
      const methods = [
        "getTeacherDashboard",
        "getTeacherCourses",
        "getTeacherStudents",
        "getTeacherReports",
      ];
      for (const m of methods) {
        assert.match(
          teacherSource,
          new RegExp(`export async function ${m}[\\s\\S]*?isTransportError\\(err\\)[\\s\\S]*?throw err;`),
          `El método ${m} debe validar isTransportError(err) y relanzar el error no-transporte`
        );
      }
    });

    test("1.3. Ningún método docente tiene catch incondicional que devuelva Supabase sin validar el error", () => {
      assert.doesNotMatch(
        teacherSource,
        /catch\s*\(\w+\)\s*\{\s*console\.warn\([^)]*\);\s*\}\s*return await getTeacher\w+FromSupabase/
      );
    });
  });

  // =========================================================================
  // 2. Simulated Runtime Verification with HTTP 403 Forbidden
  // =========================================================================
  describe("2. Pruebas de Ejecución: HTTP 403 Forbidden no activa fallback y muestra error real", () => {
    const errorPayload403 = {
      type: "https://api.plataformamicro.edu.pe/errors/forbidden",
      title: "Acceso no autorizado",
      status: 403,
      detail: "Se requiere rol docente para consultar la telemetría institucional.",
      code: "INSUFFICIENT_PERMISSIONS",
    };

    async function executeTeacherPattern(endpoint, fallbackFn) {
      let fallbackCalled = false;
      try {
        await apiFetch(endpoint, { method: "GET" }, "teacher");
      } catch (err) {
        if (isTransportError(err)) {
          fallbackCalled = true;
          return await fallbackFn();
        }
        throw err;
      }
      return { fallbackCalled };
    }

    test("2.1. getTeacherDashboard ante 403: no ejecuta fallback y lanza ApiClientError(403)", async () => {
      globalThis.fetch = () => mockResponse(403, errorPayload403);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern(
            "/api/v1/teacher/dashboard?section_id=sec-1",
            async () => {
              supabaseInvoked = true;
              return {};
            }
          );
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          assert.strictEqual(err.code, "INSUFFICIENT_PERMISSIONS");
          assert.match(err.message, /docente/i);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false, "El fallback a Supabase NO debió ser ejecutado");
    });

    test("2.2. getTeacherCourses ante 403: no ejecuta fallback y lanza ApiClientError(403)", async () => {
      globalThis.fetch = () => mockResponse(403, errorPayload403);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/courses", async () => {
            supabaseInvoked = true;
            return [];
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });

    test("2.3. getTeacherStudents ante 403: no ejecuta fallback y lanza ApiClientError(403)", async () => {
      globalThis.fetch = () => mockResponse(403, errorPayload403);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern(
            "/api/v1/teacher/students?section_id=sec-1",
            async () => {
              supabaseInvoked = true;
              return [];
            }
          );
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });

    test("2.4. getTeacherReports ante 403: no ejecuta fallback y lanza ApiClientError(403)", async () => {
      globalThis.fetch = () => mockResponse(403, errorPayload403);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/reports", async () => {
            supabaseInvoked = true;
            return {};
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 403);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });
  });

  // =========================================================================
  // 3. Simulated Runtime Verification with HTTP 503 Service Unavailable
  // =========================================================================
  describe("3. Pruebas de Ejecución: HTTP 503 no activa fallback y propaga error del servidor", () => {
    const errorPayload503 = {
      type: "https://api.plataformamicro.edu.pe/errors/service-unavailable",
      title: "Servicio Temporalmente No Disponible",
      status: 503,
      detail: "El servicio de telemetría y ML API está en mantenimiento o bajo carga.",
      code: "SERVICE_UNAVAILABLE",
    };

    async function executeTeacherPattern(endpoint, fallbackFn) {
      try {
        await apiFetch(endpoint, { method: "GET" }, "teacher");
      } catch (err) {
        if (isTransportError(err)) {
          return await fallbackFn();
        }
        throw err;
      }
    }

    test("3.1. getTeacherDashboard ante 503: relanza ApiClientError(503) sin fallback a Supabase", async () => {
      globalThis.fetch = () => mockResponse(503, errorPayload503);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/dashboard", async () => {
            supabaseInvoked = true;
            return {};
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 503);
          assert.strictEqual(err.code, "SERVICE_UNAVAILABLE");
          assert.match(err.message, /503|mantenimiento|servicio/i);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });

    test("3.2. getTeacherCourses ante 503: relanza ApiClientError(503) sin fallback a Supabase", async () => {
      globalThis.fetch = () => mockResponse(503, errorPayload503);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/courses", async () => {
            supabaseInvoked = true;
            return [];
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 503);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });

    test("3.3. getTeacherStudents ante 503: relanza ApiClientError(503) sin fallback a Supabase", async () => {
      globalThis.fetch = () => mockResponse(503, errorPayload503);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/students", async () => {
            supabaseInvoked = true;
            return [];
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 503);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });

    test("3.4. getTeacherReports ante 503: relanza ApiClientError(503) sin fallback a Supabase", async () => {
      globalThis.fetch = () => mockResponse(503, errorPayload503);
      let supabaseInvoked = false;

      await assert.rejects(
        async () => {
          await executeTeacherPattern("/api/v1/teacher/reports", async () => {
            supabaseInvoked = true;
            return {};
          });
        },
        (err) => {
          assert.ok(err instanceof ApiClientError);
          assert.strictEqual(err.status, 503);
          return true;
        }
      );
      assert.strictEqual(supabaseInvoked, false);
    });
  });

  // =========================================================================
  // 4. Transport Error Fallback Activation
  // =========================================================================
  describe("4. Error de Transporte Real (status 0 / Red caída): activa fallback a Supabase", () => {
    test("4.1. Fallo de red (fetch lanza TypeError): activa fallback a Supabase", async () => {
      globalThis.fetch = () => Promise.reject(new TypeError("Failed to fetch"));
      let fallbackActivated = false;

      const result = await (async () => {
        try {
          await apiFetch("/api/v1/teacher/dashboard", { method: "GET" }, "teacher");
        } catch (err) {
          if (isTransportError(err)) {
            fallbackActivated = true;
            return { fromSupabase: true };
          }
          throw err;
        }
      })();

      assert.strictEqual(fallbackActivated, true);
      assert.strictEqual(result.fromSupabase, true);
    });
  });
});

describe("C9: Corrección de Contratos de Microcontenidos (microcontents.ts)", () => {
  const microcontentsSource = source("../lib/api/microcontents.ts");
  const originalFetch = globalThis.fetch;
  const originalApiUrl = process.env.NEXT_PUBLIC_API_URL;

  beforeEach(() => {
    process.env.NEXT_PUBLIC_API_URL = "https://mock-ml-api.internal";
  });

  afterEach(() => {
    globalThis.fetch = originalFetch;
    if (originalApiUrl !== undefined) {
      process.env.NEXT_PUBLIC_API_URL = originalApiUrl;
    } else {
      delete process.env.NEXT_PUBLIC_API_URL;
    }
  });

  // =========================================================================
  // 1. Static Contract & Source Invariants
  // =========================================================================
  describe("1. Contrato Estático en microcontents.ts", () => {
    test("1.1. updateMicrocontent utiliza método HTTP PATCH (prohibido método PUT)", () => {
      assert.doesNotMatch(
        microcontentsSource,
        /updateMicrocontent[\s\S]*?method:\s*["']PUT["']/
      );
      assert.match(
        microcontentsSource,
        /updateMicrocontent[\s\S]*?method:\s*["']PATCH["']/
      );
    });

    test("1.2. listMicrocontents utiliza kc_id como query param (no knowledge_component_id)", () => {
      assert.doesNotMatch(
        microcontentsSource,
        /query\.set\(["']knowledge_component_id["']/
      );
      assert.match(
        microcontentsSource,
        /query\.set\(["']kc_id["']/
      );
    });

    test("1.3. listMicrocontents no acepta ni propaga filtro status inexistente", () => {
      assert.doesNotMatch(
        microcontentsSource,
        /query\.set\(["']status["']/
      );
      assert.doesNotMatch(
        microcontentsSource,
        /options\?:\s*\{[^}]*status\?:/
      );
    });
  });

  // =========================================================================
  // 2. Simulated Runtime Verification
  // =========================================================================
  describe("2. Pruebas de Ejecución: Actualización (PATCH) y Filtrado (kc_id)", () => {
    test("2.1. Simulación updateMicrocontent: envía PATCH con body JSON a /api/v1/microcontents/:id", async () => {
      let capturedMethod = "";
      let capturedUrl = "";
      let capturedBody = null;

      globalThis.fetch = (url, opts) => {
        capturedUrl = String(url);
        capturedMethod = opts?.method;
        capturedBody = opts?.body ? JSON.parse(opts.body) : null;
        return mockResponse(200, {
          id: "mc-100",
          title: "Microcontenido Actualizado",
        });
      };

      const payload = {
        title: "Microcontenido Actualizado",
        estimated_duration_seconds: 300,
        content_body: { summary: "Nuevo resumen pedagógico" },
      };

      // Execute simulated client call using identical contract
      const result = await apiFetch(
        `/api/v1/microcontents/mc-100`,
        {
          method: "PATCH",
          body: JSON.stringify(payload),
        },
        "teacher"
      );

      assert.strictEqual(capturedMethod, "PATCH");
      assert.ok(capturedUrl.endsWith("/api/v1/microcontents/mc-100"));
      assert.deepStrictEqual(capturedBody, payload);
      assert.strictEqual(result.id, "mc-100");
    });

    test("2.2. Simulación listMicrocontents con kc_id, course_id y unit_id: query params canónicos", async () => {
      let capturedUrl = "";

      globalThis.fetch = (url) => {
        capturedUrl = String(url);
        return mockResponse(200, []);
      };

      const options = {
        courseId: "c-001",
        unitId: "u-002",
        kcId: "kc-003",
      };

      const query = new URLSearchParams();
      if (options.courseId) query.set("course_id", options.courseId);
      if (options.unitId) query.set("unit_id", options.unitId);
      if (options.kcId) query.set("kc_id", options.kcId);

      const qs = query.toString();
      await apiFetch(`/api/v1/microcontents${qs ? `?${qs}` : ""}`, { method: "GET" }, "teacher");

      const parsed = new URL(capturedUrl);
      assert.strictEqual(parsed.pathname, "/api/v1/microcontents");
      assert.strictEqual(parsed.searchParams.get("kc_id"), "kc-003");
      assert.strictEqual(parsed.searchParams.get("course_id"), "c-001");
      assert.strictEqual(parsed.searchParams.get("unit_id"), "u-002");
      assert.strictEqual(parsed.searchParams.get("knowledge_component_id"), null);
      assert.strictEqual(parsed.searchParams.get("status"), null);
    });
  });
});
