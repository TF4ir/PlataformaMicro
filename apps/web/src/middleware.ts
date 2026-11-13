import { createServerClient, type CookieOptions } from "@supabase/ssr";
import { NextResponse, type NextRequest } from "next/server";
import {
  decideRoute,
  normalizeRole,
  type AppRole,
} from "@/lib/auth/authorization";

const DEFAULT_SUPABASE_URL = "https://oqjahhbqcethwgpufgnm.supabase.co";
const DEFAULT_SUPABASE_ANON_KEY = "sb_publishable_u5AIwepBNqqKzQPxVtg5QQ_d_IQ3yrX";

function supabaseUrl(): string {
  return process.env.NEXT_PUBLIC_SUPABASE_URL || DEFAULT_SUPABASE_URL;
}

function supabaseAnonKey(): string {
  return (
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    DEFAULT_SUPABASE_ANON_KEY
  );
}

/**
 * Fast path: without a Supabase auth cookie there is no session to verify.
 * Cookie *presence* is not an authorization signal; it only avoids a network
 * round-trip when there is provably nothing to validate.
 */
function hasSupabaseAuthCookie(req: NextRequest): boolean {
  return req.cookies
    .getAll()
    .some((cookie) => cookie.name.includes("-auth-token"));
}

function copyCookies(target: NextResponse, source: NextResponse): void {
  source.cookies.getAll().forEach((cookie) => target.cookies.set(cookie));
}

/**
 * Resolves the role from a cryptographically verified Supabase session.
 *
 * 1. `auth.getUser()` validates the JWT against Supabase Auth (never the
 *    local-only session accessor, which merely decodes the cookie).
 * 2. The role is read from `public.profiles` under the user's own RLS
 *    context. Client-controlled metadata, `nexo_*` cookies and request
 *    headers are never consulted.
 */
async function resolveVerifiedRole(
  req: NextRequest,
  response: NextResponse
): Promise<AppRole | null> {
  if (!hasSupabaseAuthCookie(req)) return null;

  const supabase = createServerClient(supabaseUrl(), supabaseAnonKey(), {
    cookies: {
      get(name: string) {
        return req.cookies.get(name)?.value;
      },
      set(name: string, value: string, options: CookieOptions) {
        req.cookies.set({ name, value, ...options });
        response.cookies.set({ name, value, ...options });
      },
      remove(name: string, options: CookieOptions) {
        req.cookies.set({ name, value: "", ...options });
        response.cookies.set({ name, value: "", ...options });
      },
    },
  });

  const {
    data: { user },
    error: userError,
  } = await supabase.auth.getUser();

  if (userError || !user) return null;

  const { data: profile, error: profileError } = await supabase
    .from("profiles")
    .select("role")
    .eq("id", user.id)
    .maybeSingle();

  if (profileError || !profile) return null;

  return normalizeRole(profile.role);
}

export async function middleware(req: NextRequest) {
  const { pathname } = req.nextUrl;

  // 1. Bypass static resources and internal Next.js paths.
  //    `/api/*` is intentionally excluded here; FastAPI/Route Handlers perform
  //    their own JWT validation and must not be protected by UI redirects.
  const isStaticAsset =
    /\.(?:avif|css|gif|ico|jpe?g|js|json|map|mjs|otf|png|svg|ttf|txt|webmanifest|webp|woff2?|xml)$/i.test(
      pathname
    );

  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/api") ||
    isStaticAsset ||
    pathname === "/favicon.ico"
  ) {
    return NextResponse.next();
  }

  // Response that carries any refreshed Supabase auth cookies.
  const response = NextResponse.next({ request: req });
  const role = await resolveVerifiedRole(req, response);
  const decision = decideRoute(role, pathname);

  switch (decision.kind) {
    case "public":
    case "allow":
      return response;

    case "redirect": {
      const redirectResponse = NextResponse.redirect(
        new URL(decision.destination, req.url)
      );
      copyCookies(redirectResponse, response);
      return redirectResponse;
    }

    case "deny": {
      const forbidden = new NextResponse("Forbidden", {
        status: decision.status,
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
      copyCookies(forbidden, response);
      return forbidden;
    }
  }
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
