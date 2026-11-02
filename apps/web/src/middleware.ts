import { NextResponse, type NextRequest } from "next/server";

export function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // 1. Bypass static resources and internal Next.js paths
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    pathname.includes(".") ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // 2. Read session & role cookies
  const sessionToken = req.cookies.get("nexo_session")?.value;
  const role = req.cookies.get("nexo_role")?.value;

  const isAuthenticated = Boolean(
    sessionToken && (role === "student" || role === "teacher")
  );

  // 3. Define public routes
  const isAuthRoute =
    pathname === "/login" ||
    pathname.startsWith("/login/") ||
    pathname === "/recovery" ||
    pathname.startsWith("/recovery/");

  // 4. Root "/" redirection
  if (pathname === "/") {
    if (isAuthenticated) {
      const target = role === "teacher" ? "/teacher/dashboard" : "/dashboard";
      return NextResponse.redirect(new URL(target, req.url));
    }
    return NextResponse.redirect(new URL("/login", req.url));
  }

  // 5. If already authenticated and trying to visit login/recovery, forward to role dashboard
  if (isAuthRoute) {
    if (isAuthenticated) {
      const target = role === "teacher" ? "/teacher/dashboard" : "/dashboard";
      return NextResponse.redirect(new URL(target, req.url));
    }
    return NextResponse.next();
  }

  // 6. Teacher protected routes (/teacher/*)
  if (pathname.startsWith("/teacher")) {
    if (!isAuthenticated) {
      const loginUrl = new URL("/login", req.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Role privilege check: Students CANNOT access teacher dashboard
    if (role !== "teacher") {
      return NextResponse.redirect(new URL("/dashboard", req.url));
    }

    return NextResponse.next();
  }

  // 7. Student learning routes (/dashboard, /courses, /progress, /learn, /quiz, /recommendations)
  const isStudentRoute =
    pathname.startsWith("/dashboard") ||
    pathname.startsWith("/courses") ||
    pathname.startsWith("/progress") ||
    pathname.startsWith("/learn") ||
    pathname.startsWith("/quiz") ||
    pathname.startsWith("/recommendations");

  if (isStudentRoute) {
    if (!isAuthenticated) {
      const loginUrl = new URL("/login", req.url);
      loginUrl.searchParams.set("redirect", pathname);
      return NextResponse.redirect(loginUrl);
    }

    // Role privilege check: Teachers stay in their management area
    if (role !== "student") {
      return NextResponse.redirect(new URL("/teacher/dashboard", req.url));
    }

    return NextResponse.next();
  }

  // 8. Shared authenticated route (/system-status)
  if (pathname.startsWith("/system-status")) {
    if (!isAuthenticated) {
      return NextResponse.redirect(new URL("/login", req.url));
    }
    return NextResponse.next();
  }

  // Fallback for any other route
  if (!isAuthenticated) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     */
    "/((?!_next/static|_next/image|favicon.ico).*)",
  ],
};
