/**
 * Pure authorization decisions shared by middleware, Route Handlers and tests.
 *
 * Security invariant: a role MUST come from a server-verified source
 * (`auth.getUser()` + `public.profiles.role`). This module never reads
 * cookies, headers or user metadata, so it cannot turn untrusted input into
 * an authenticated identity on its own.
 */

/** Roles declared by the database enum `public.user_role`. */
export type AppRole =
  | "student"
  | "teacher"
  | "admin"
  | "super_admin"
  | "researcher";

/** Roles with a rendered web portal. */
export type PortalRole = "student" | "teacher";

export type RouteKind =
  | "public"
  | "root"
  | "teacher"
  | "student"
  | "admin"
  | "shared"
  | "unknown";

export type RouteDecision =
  | { kind: "public" }
  | { kind: "allow"; route: Exclude<RouteKind, "public" | "root"> }
  | {
      kind: "redirect";
      destination: string;
      reason: "unauthenticated" | "wrong-role";
    }
  | { kind: "deny"; status: 403; reason: "forbidden-role" };

const PUBLIC_PATHS = ["/login", "/recovery"] as const;

const STUDENT_PREFIXES = [
  "/dashboard",
  "/courses",
  "/progress",
  "/learn",
  "/quiz",
  "/recommendations",
] as const;

const ADMIN_ROLES: readonly AppRole[] = ["admin", "super_admin"];
const TEACHER_AREA_ROLES: readonly AppRole[] = [
  "teacher",
  "admin",
  "super_admin",
];

/** Normalizes an untrusted value into a known database role. */
export function normalizeRole(value: unknown): AppRole | null {
  if (typeof value !== "string") return null;
  switch (value) {
    case "student":
    case "teacher":
    case "admin":
    case "super_admin":
    case "researcher":
      return value;
    default:
      return null;
  }
}

/** Maps an app role to the only two portals the web app renders. */
export function portalRoleFor(role: AppRole | null): PortalRole | null {
  if (role === "student") return "student";
  if (role === "teacher" || role === "admin" || role === "super_admin") {
    // Admin roles have no dedicated portal yet and use the teacher shell.
    return "teacher";
  }
  // `researcher` and unknown roles have no web portal in P0.1.
  return null;
}

export function homePathForRole(role: AppRole | null): string {
  if (role === "student") return "/dashboard";
  if (role === "researcher") return "/system-status";
  return "/teacher/dashboard";
}

function matchesPrefix(pathname: string, prefix: string): boolean {
  return pathname === prefix || pathname.startsWith(`${prefix}/`);
}

export function isPublicPath(pathname: string): boolean {
  return PUBLIC_PATHS.some((path) => matchesPrefix(pathname, path));
}

export function classifyRoute(pathname: string): RouteKind {
  if (pathname === "/") return "root";
  if (isPublicPath(pathname)) return "public";
  if (matchesPrefix(pathname, "/teacher")) return "teacher";
  if (matchesPrefix(pathname, "/admin")) return "admin";
  if (STUDENT_PREFIXES.some((prefix) => matchesPrefix(pathname, prefix))) {
    return "student";
  }
  if (matchesPrefix(pathname, "/system-status")) return "shared";
  return "unknown";
}

function loginRedirect(pathname: string): string {
  return pathname && pathname !== "/"
    ? `/login?redirect=${encodeURIComponent(pathname)}`
    : "/login";
}

/**
 * Decides how a request must be handled given a *verified* role.
 *
 * `role === null` means "no verified session"; it must never be inferred from
 * cookies or client state.
 */
export function decideRoute(
  role: AppRole | null,
  pathname: string
): RouteDecision {
  const route = classifyRoute(pathname);
  const authenticated = role !== null;

  if (route === "public") {
    return authenticated
      ? {
          kind: "redirect",
          destination: homePathForRole(role),
          reason: "wrong-role",
        }
      : { kind: "public" };
  }

  if (route === "root") {
    return authenticated
      ? {
          kind: "redirect",
          destination: homePathForRole(role),
          reason: "wrong-role",
        }
      : {
          kind: "redirect",
          destination: "/login",
          reason: "unauthenticated",
        };
  }

  if (!authenticated) {
    return {
      kind: "redirect",
      destination: loginRedirect(pathname),
      reason: "unauthenticated",
    };
  }

  switch (route) {
    case "teacher":
      if (TEACHER_AREA_ROLES.includes(role)) {
        return { kind: "allow", route: "teacher" };
      }
      if (role === "student") {
        return {
          kind: "redirect",
          destination: "/dashboard",
          reason: "wrong-role",
        };
      }
      return { kind: "deny", status: 403, reason: "forbidden-role" };

    case "admin":
      if (ADMIN_ROLES.includes(role)) {
        return { kind: "allow", route: "admin" };
      }
      return { kind: "deny", status: 403, reason: "forbidden-role" };

    case "student":
      if (role === "student" || ADMIN_ROLES.includes(role)) {
        return { kind: "allow", route: "student" };
      }
      if (role === "teacher") {
        return {
          kind: "redirect",
          destination: "/teacher/dashboard",
          reason: "wrong-role",
        };
      }
      return { kind: "deny", status: 403, reason: "forbidden-role" };

    case "shared":
    case "unknown":
      return { kind: "allow", route: route };

    default:
      return { kind: "deny", status: 403, reason: "forbidden-role" };
  }
}

/**
 * Sanitizes a post-login redirect. Only same-origin absolute paths that the
 * verified role is allowed to open are accepted.
 */
export function safeRedirectForRole(
  role: AppRole | null,
  candidate: string | null | undefined
): string {
  const fallback = homePathForRole(role);
  if (!candidate) return fallback;
  if (!candidate.startsWith("/") || candidate.startsWith("//")) return fallback;

  // Strip query/hash before classifying the path.
  const pathname = candidate.split(/[?#]/, 1)[0] || "/";
  const decision = decideRoute(role, pathname);
  if (decision.kind === "allow") return candidate;
  if (decision.kind === "public") return fallback;
  return fallback;
}
