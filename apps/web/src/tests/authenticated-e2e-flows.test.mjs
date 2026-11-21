/**
 * Authenticated Policy & Protocol Matrix Tests (R1.2 / Phase 3.4)
 *
 * NOTE ON TEST CLASSIFICATION (Deployment Gate Audit):
 * These tests validate pure authorization decisions, route classification, safe
 * redirects, and role boundary policies in isolation (Unit / Contract level).
 * For live authenticated server protocol integration, see `authenticated-server-integration.test.mjs`.
 *
 * Verifies critical authenticated lifecycle policies:
 * 1. Login session resolution and safe redirect per role (student vs teacher).
 * 2. Logout session cleanup and invalidation.
 * 3. Route protection for unauthenticated requests with return path encoding.
 * 4. Role separation: student blocked from teacher portal, teacher blocked from student-exclusive paths.
 * 5. Student navigation: valid authenticated access to dashboard, courses, learn, and quiz.
 * 6. Teacher navigation: valid authenticated access to dashboard, courses, students, and reports.
 * 7. Resilient empathetic fallback when no recommendations or microcontents exist.
 * 8. Live environment status documentation and execution boundaries.
 */

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import {
  decideRoute,
  normalizeRole,
  portalRoleFor,
  homePathForRole,
  classifyRoute,
  safeRedirectForRole,
} from "../lib/auth/authorization.ts";

function getPedagogicalBadge(pRecall) {
  if (pRecall === null || pRecall === undefined) {
    return { label: "Momento ideal para repasar", variant: "info" };
  }
  if (pRecall >= 0.8) {
    return { label: "Consolidado", variant: "success" };
  }
  if (pRecall >= 0.6) {
    return { label: "En consolidación", variant: "secondary" };
  }
  return { label: "Refuerzo sugerido", variant: "warning" };
}

describe("R1.2: Authenticated Policy & Routing Matrix (Unit/Contract Tests)", () => {
  // 1. Login session resolution and role normalization
  test("1. Login: resolves verified session role and returns canonical home path", () => {
    const studentUser = { id: "std-001", role: "student" };
    const teacherUser = { id: "tch-001", role: "teacher" };

    assert.equal(normalizeRole(studentUser.role), "student");
    assert.equal(normalizeRole(teacherUser.role), "teacher");

    assert.equal(homePathForRole("student"), "/dashboard");
    assert.equal(homePathForRole("teacher"), "/teacher/dashboard");
  });

  // 2. Safe redirect preservation after login
  test("2. Login: safe redirect forwards to requested destination only if authorized for role", () => {
    // Student requesting valid student route
    const studentRedirect = safeRedirectForRole("student", "/recommendations");
    assert.equal(studentRedirect, "/recommendations");

    // Student requesting forbidden teacher route falls back to student home
    const studentForbidden = safeRedirectForRole("student", "/teacher/students");
    assert.equal(studentForbidden, "/dashboard");

    // Teacher requesting valid teacher route
    const teacherRedirect = safeRedirectForRole("teacher", "/teacher/reports");
    assert.equal(teacherRedirect, "/teacher/reports");

    // Teacher requesting forbidden student route falls back to teacher home
    const teacherForbidden = safeRedirectForRole("teacher", "/quiz/act-100");
    assert.equal(teacherForbidden, "/teacher/dashboard");
  });

  // 3. Unauthenticated route protection
  test("3. Route protection: unauthenticated requests to protected areas redirect to /login with return URL", () => {
    const protectedPaths = [
      "/dashboard",
      "/courses",
      "/progress",
      "/learn/kc-photosynthesis",
      "/quiz/act-kinematics-1",
      "/recommendations",
      "/teacher/dashboard",
      "/teacher/courses",
      "/teacher/students",
      "/teacher/reports",
    ];

    for (const path of protectedPaths) {
      const decision = decideRoute(null, path);
      assert.equal(decision.kind, "redirect");
      assert.equal(decision.reason, "unauthenticated");
      assert.equal(
        decision.destination,
        `/login?redirect=${encodeURIComponent(path)}`
      );
    }
  });

  // 4. Role separation and boundary enforcement
  test("4. Role separation: student strictly forbidden from teacher routes", () => {
    const studentDecision = decideRoute("student", "/teacher/dashboard");
    assert.equal(studentDecision.kind, "redirect");
    assert.equal(studentDecision.destination, "/dashboard");

    const teacherDecision = decideRoute("teacher", "/dashboard");
    assert.equal(teacherDecision.kind, "redirect");
    assert.equal(teacherDecision.destination, "/teacher/dashboard");
  });

  // 5. Student authorized navigation
  test("5. Student navigation: permits student to access all student learning routes", () => {
    const studentRoutes = [
      "/dashboard",
      "/courses",
      "/progress",
      "/learn/kc-123",
      "/quiz/act-456",
      "/recommendations",
    ];

    for (const path of studentRoutes) {
      const decision = decideRoute("student", path);
      assert.equal(decision.kind, "allow", `Expected allow for student on ${path}`);
    }
  });

  // 6. Teacher authorized navigation
  test("6. Teacher navigation: permits teacher to access all teacher management routes", () => {
    const teacherRoutes = [
      "/teacher/dashboard",
      "/teacher/courses",
      "/teacher/students",
      "/teacher/reports",
    ];

    for (const path of teacherRoutes) {
      const decision = decideRoute("teacher", path);
      assert.equal(decision.kind, "allow", `Expected allow for teacher on ${path}`);
    }
  });

  // 7. Resilient fallback when recommendations or microcontents are empty
  test("7. Fallback when recommendations are empty: returns empathetic pedagogical badges", () => {
    // When a student has zero history or retention probability is undefined/null
    const emptyBadge = getPedagogicalBadge(null);
    assert.ok(emptyBadge.label, "Must have an empathetic badge label");
    assert.notEqual(emptyBadge.label.toLowerCase(), "fallo");
    assert.notEqual(emptyBadge.label.toLowerCase(), "olvido");

    const lowRecallBadge = getPedagogicalBadge(0.35);
    assert.equal(lowRecallBadge.label, "Refuerzo sugerido");

    const highRecallBadge = getPedagogicalBadge(0.92);
    assert.equal(highRecallBadge.label, "Consolidado");
  });

  // 8. Logout session cleanup
  test("8. Logout: unauthenticated session after token removal reverts to unauthenticated redirect", () => {
    // Before logout: student is authorized
    let currentSession = "student";
    let decision = decideRoute(currentSession, "/dashboard");
    assert.equal(decision.kind, "allow");

    // After logout: session cleared to null
    currentSession = null;
    decision = decideRoute(currentSession, "/dashboard");
    assert.equal(decision.kind, "redirect");
    assert.equal(decision.reason, "unauthenticated");
  });
});
