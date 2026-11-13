/**
 * P0.1 — Authentication & authorization hardening tests.
 *
 * Scenarios 1-12 from the milestone brief. Pure decision tests run here; any
 * scenario that needs a live Supabase stack is covered by static contract
 * assertions and documented as pending integration work.
 */

import { test, describe } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

import {
  decideRoute,
  normalizeRole,
  portalRoleFor,
  homePathForRole,
  classifyRoute,
  isPublicPath,
  safeRedirectForRole,
} from "../lib/auth/authorization.ts";

function source(relativePath) {
  return readFileSync(new URL(relativePath, import.meta.url), "utf8");
}

const middlewareSource = source("../middleware.ts");
const roleContextSource = source("../lib/role-context.tsx");
const loginSource = source("../app/(auth)/login/page.tsx");
const apiClientSource = source("../lib/api/client.ts");
const learningSource = source("../lib/api/learning.ts");
const contentGenerationSource = source("../lib/api/content-generation.ts");
const hardeningMigration = source(
  "../../../../supabase/migrations/20261109000000_profiles_privilege_hardening.sql"
);

describe("P0.1 authorization matrix (pure decisions)", () => {
  test("1. Unauthenticated access to student routes redirects to login with return path", () => {
    for (const path of [
      "/dashboard",
      "/courses",
      "/progress",
      "/learn/kc-1",
      "/quiz/act-1",
      "/recommendations/rec-1",
    ]) {
      const decision = decideRoute(null, path);
      assert.equal(decision.kind, "redirect");
      assert.equal(decision.reason, "unauthenticated");
      assert.equal(
        decision.destination,
        `/login?redirect=${encodeURIComponent(path)}`
      );
    }
  });

  test("2. Unauthenticated access to teacher routes redirects to login", () => {
    const decision = decideRoute(null, "/teacher/dashboard");
    assert.equal(decision.kind, "redirect");
    assert.equal(decision.reason, "unauthenticated");
    assert.match(decision.destination, /^\/login\?redirect=/);
  });

  test("3. A forged nexo_role cookie cannot grant a role", () => {
    // The decision function has no cookie input: the only way to be
    // authenticated is to pass a verified role explicitly.
    assert.equal(decideRoute(null, "/teacher/dashboard").kind, "redirect");

    // Middleware must not read the legacy cookies at all.
    assert.doesNotMatch(middlewareSource, /nexo_role|nexo_session/);
  });

  test("4. A forged nexo_session cookie cannot grant a session", () => {
    assert.doesNotMatch(middlewareSource, /nexo_session/);
    assert.doesNotMatch(roleContextSource, /setCookie\(|document\.cookie\s*=\s*`nexo_session/);
    assert.equal(decideRoute(null, "/dashboard").kind, "redirect");
  });

  test("5. Student cannot open teacher routes", () => {
    const decision = decideRoute("student", "/teacher/students");
    assert.deepEqual(decision, {
      kind: "redirect",
      destination: "/dashboard",
      reason: "wrong-role",
    });
  });

  test("6. Teacher cannot open admin functionality; only admin roles can", () => {
    for (const role of ["teacher", "student", "researcher"]) {
      assert.deepEqual(decideRoute(role, "/admin/users"), {
        kind: "deny",
        status: 403,
        reason: "forbidden-role",
      });
    }
    assert.equal(decideRoute("admin", "/admin/users").kind, "allow");
    assert.equal(decideRoute("super_admin", "/admin/users").kind, "allow");
  });

  test("7. Invalid or expired JWT means no verified role", () => {
    // Middleware validates the token with auth.getUser(); on failure the
    // resolver returns null and every protected route redirects to login.
    assert.match(middlewareSource, /auth\.getUser\(\)/);
    assert.doesNotMatch(middlewareSource, /auth\.getSession\(/);
    assert.equal(decideRoute(null, "/system-status").kind, "redirect");
  });

  test("8. Valid student session reaches student areas only", () => {
    assert.equal(decideRoute("student", "/dashboard").kind, "allow");
    assert.equal(decideRoute("student", "/quiz/act-1").kind, "allow");
    assert.equal(decideRoute("student", "/system-status").kind, "allow");
    assert.equal(decideRoute("student", "/teacher/dashboard").kind, "redirect");
  });

  test("9. Valid teacher session reaches teacher areas only", () => {
    assert.equal(decideRoute("teacher", "/teacher/dashboard").kind, "allow");
    assert.equal(decideRoute("teacher", "/teacher/students").kind, "allow");
    assert.equal(decideRoute("teacher", "/system-status").kind, "allow");
    assert.deepEqual(decideRoute("teacher", "/dashboard"), {
      kind: "redirect",
      destination: "/teacher/dashboard",
      reason: "wrong-role",
    });
  });

  test("10. Logout/revocation removes both server and local authorization", () => {
    assert.match(roleContextSource, /supabase\.auth\.signOut\(\)/);
    assert.match(roleContextSource, /clearLegacyAuthCookies\(\)/);
    // After revocation there is no verified role, so protected routes lock.
    assert.equal(decideRoute(null, "/dashboard").kind, "redirect");
    assert.equal(decideRoute(null, "/teacher/dashboard").kind, "redirect");
  });

  test("11. Direct protected API calls carry only a bearer token, never demo identity headers", () => {
    for (const file of [
      apiClientSource,
      learningSource,
      contentGenerationSource,
    ]) {
      assert.doesNotMatch(file, /X-User-Id/);
      assert.doesNotMatch(file, /X-Tenant-Id/);
      assert.doesNotMatch(file, /X-User-Role/);
      assert.doesNotMatch(file, /X-Course-Ids/);
    }
    assert.match(apiClientSource, /Authorization.*Bearer/);
  });

  test("12. Profiles privilege escalation is blocked at the database layer", () => {
    assert.match(hardeningMigration, /REVOKE UPDATE ON public\.profiles FROM authenticated/);
    assert.match(hardeningMigration, /GRANT UPDATE \(full_name, avatar_url\)/);
    assert.match(
      hardeningMigration,
      /trg_profiles_prevent_privilege_escalation/
    );
    assert.match(hardeningMigration, /NEW\.role IS DISTINCT FROM OLD\.role/);
    assert.match(
      hardeningMigration,
      /NEW\.tenant_id IS DISTINCT FROM OLD\.tenant_id/
    );
    assert.match(
      hardeningMigration,
      /NEW\.student_code IS DISTINCT FROM OLD\.student_code/
    );

    // Cross-student isolation remains enforced by RLS.
    const initialSchema = source(
      "../../../../supabase/migrations/20261102000000_initial_schema.sql"
    );
    assert.match(
      initialSchema,
      /CREATE POLICY "answer_events_select" ON answer_events[\s\S]*?student_id = \(SELECT auth\.uid\(\)\)/
    );
    assert.match(
      initialSchema,
      /CREATE POLICY "answer_events_insert" ON answer_events[\s\S]*?WITH CHECK \(student_id = \(SELECT auth\.uid\(\)\)\)/
    );
  });
});

describe("P0.1 role normalization and redirect safety", () => {
  test("only known database roles are accepted", () => {
    assert.equal(normalizeRole("student"), "student");
    assert.equal(normalizeRole("teacher"), "teacher");
    assert.equal(normalizeRole("admin"), "admin");
    assert.equal(normalizeRole("super_admin"), "super_admin");
    assert.equal(normalizeRole("researcher"), "researcher");
    for (const value of [null, undefined, "", "root", "Student", 1, {}]) {
      assert.equal(normalizeRole(value), null);
    }
  });

  test("portal mapping and home paths are deterministic", () => {
    assert.equal(portalRoleFor("student"), "student");
    assert.equal(portalRoleFor("teacher"), "teacher");
    assert.equal(portalRoleFor("admin"), "teacher");
    assert.equal(portalRoleFor("super_admin"), "teacher");
    assert.equal(portalRoleFor("researcher"), null);
    assert.equal(portalRoleFor(null), null);
    assert.equal(homePathForRole("student"), "/dashboard");
    assert.equal(homePathForRole("teacher"), "/teacher/dashboard");
    assert.equal(homePathForRole("researcher"), "/system-status");
    assert.equal(homePathForRole(null), "/teacher/dashboard");
  });

  test("route classification does not confuse prefixes", () => {
    assert.equal(classifyRoute("/teacher/dashboard"), "teacher");
    assert.equal(classifyRoute("/teacherish"), "unknown");
    assert.equal(classifyRoute("/dashboard"), "student");
    assert.equal(classifyRoute("/dashboarding"), "unknown");
    assert.equal(classifyRoute("/admin"), "admin");
    assert.equal(classifyRoute("/system-status"), "shared");
    assert.equal(classifyRoute("/login"), "public");
    assert.equal(classifyRoute("/"), "root");
    assert.equal(isPublicPath("/recovery/help"), true);
  });

  test("post-login redirects are restricted to the verified role's area", () => {
    assert.equal(
      safeRedirectForRole("student", "/teacher/dashboard"),
      "/dashboard"
    );
    assert.equal(
      safeRedirectForRole("teacher", "/dashboard"),
      "/teacher/dashboard"
    );
    assert.equal(safeRedirectForRole("student", "/quiz/1"), "/quiz/1");
    assert.equal(
      safeRedirectForRole("student", "https://evil.example"),
      "/dashboard"
    );
    assert.equal(
      safeRedirectForRole("student", "//evil.example"),
      "/dashboard"
    );
    assert.equal(safeRedirectForRole("student", "/admin"), "/dashboard");
  });

  test("authenticated users are forwarded away from public auth pages", () => {
    assert.deepEqual(decideRoute("student", "/login"), {
      kind: "redirect",
      destination: "/dashboard",
      reason: "wrong-role",
    });
    assert.equal(decideRoute(null, "/login").kind, "public");
    assert.equal(decideRoute(null, "/recovery").kind, "public");
  });
});

describe("P0.1 static security contracts", () => {
  test("middleware derives the role from profiles, not metadata or headers", () => {
    assert.match(middlewareSource, /from\("profiles"\)/);
    assert.match(middlewareSource, /select\("role"\)/);
    assert.doesNotMatch(middlewareSource, /user_metadata/);
    assert.doesNotMatch(middlewareSource, /req\.headers\.get\(["']x-user/i);
    assert.doesNotMatch(middlewareSource, /getSession\(/);
  });

  test("client role context validates with getUser and excludes legacy auth fallbacks", () => {
    assert.match(roleContextSource, /supabase\.auth\.getUser\(\)/);
    assert.doesNotMatch(roleContextSource, /getSession\(/);
    assert.doesNotMatch(roleContextSource, /user_metadata/);
    assert.doesNotMatch(roleContextSource, /function getCookie/);
    assert.doesNotMatch(roleContextSource, /function setCookie/);
    // The only remaining mention of legacy names is the cleanup list.
    assert.match(roleContextSource, /clearLegacyAuthCookies/);
  });

  test("login page has no parallel demo authentication path", () => {
    assert.doesNotMatch(loginSource, /isStudentMatch|isTeacherMatch/);
    assert.match(loginSource, /signInWithPassword/);
    assert.match(loginSource, /from\("profiles"\)/);
    assert.match(loginSource, /normalizeRole/);
    // Credential prefill is allowed; it must not call login() directly.
    assert.match(loginSource, /fillCredentials/);
  });

  test("answer_events remain append-only for client roles", () => {
    const eventsMigration = source(
      "../../../../supabase/migrations/20261103030000_learning_flow_and_answer_events_m4.sql"
    );
    assert.match(eventsMigration, /REVOKE UPDATE[^;]*ON answer_events/);
    assert.match(eventsMigration, /REVOKE[^;]*DELETE[^;]*ON answer_events/);
    assert.match(eventsMigration, /trg_prevent_answer_events_mutation/);
  });
});
