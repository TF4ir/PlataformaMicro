/**
 * Unified API Client Base & Dynamic Auth Handling for PlataformaMicro
 */

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Returns false when running in an HTTPS production browser and API_BASE_URL
 * points to insecure localhost/127.0.0.1, which browsers automatically block
 * due to Mixed Content security policy.
 */
export function isBackendConfigured(): boolean {
  if (typeof window !== "undefined") {
    if (
      window.location.protocol === "https:" &&
      (!API_BASE_URL ||
        API_BASE_URL.startsWith("http://localhost") ||
        API_BASE_URL.startsWith("http://127.0.0.1"))
    ) {
      return false;
    }
  }
  return true;
}

export async function getAuthToken(): Promise<string | null> {
  if (typeof window === "undefined") return null;
  try {
    const { createClient } = await import("@/lib/supabase/client");
    const supabase = createClient();
    const { data: { session }, error } = await supabase.auth.getSession();
    if (!error && session?.access_token) {
      return session.access_token;
    }
  } catch {
    // SSR or uninitialized client
  }
  return null;
}

export async function getAuthHeaders(
  roleFallback: "teacher" | "student" = "student"
): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  const token = await getAuthToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
    return headers;
  }

  // Development/Test fallback only when explicitly enabled and NOT in production
  if (process.env.NODE_ENV !== "production" && process.env.NEXT_PUBLIC_ENABLE_DEMO_AUTH === "true") {
    if (roleFallback === "teacher") {
      headers["X-User-Id"] = "d0000000-0000-0000-0000-000000000001";
      headers["X-Tenant-Id"] = "a0000000-0000-0000-0000-000000000001";
      headers["X-User-Role"] = "teacher";
      headers["X-Course-Ids"] = "c0000000-0000-0000-0000-000000000001";
    } else {
      headers["X-User-Id"] = "e0000000-0000-0000-0000-000000000001";
      headers["X-Tenant-Id"] = "a0000000-0000-0000-0000-000000000001";
      headers["X-User-Role"] = "student";
    }
  }

  return headers;
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {},
  roleFallback: "teacher" | "student" = "student"
): Promise<T> {
  const url = endpoint.startsWith("http") ? endpoint : `${API_BASE_URL}${endpoint}`;
  const authHeaders = await getAuthHeaders(roleFallback);
  const headers = {
    ...authHeaders,
    ...((options.headers as Record<string, string>) || {}),
  };

  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `Request failed with status ${response.status}`;
    try {
      const errJson = await response.json();
      if (errJson.detail) {
        errorDetail = typeof errJson.detail === "string" ? errJson.detail : JSON.stringify(errJson.detail);
      }
    } catch {
      // Body not JSON
    }
    throw new Error(errorDetail);
  }

  return response.json() as Promise<T>;
}
