/**
 * Unified API Client Base & Dynamic Auth Handling for PlataformaMicro
 * Connects Next.js (Cloudflare Workers) with FastAPI ML API (AWS Lambda).
 */

export const DEFAULT_API_URL =
  "https://54wsiki2ruyk2r5l3xvasykqo40oxokx.lambda-url.us-east-2.on.aws";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL ||
  (process.env.NODE_ENV === "production" ? DEFAULT_API_URL : "http://localhost:8000");

/**
 * Custom error class for API client failures, retaining HTTP status,
 * RFC 7807 problem details / error code, and parsed detail message.
 */
export class ApiClientError extends Error {
  public readonly status: number;
  public readonly code?: string;
  public readonly detail?: unknown;

  constructor(message: string, status: number, code?: string, detail?: unknown) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
    this.code = code;
    this.detail = detail;
    Object.setPrototypeOf(this, ApiClientError.prototype);
  }
}

/**
 * Detects whether an error was caused by a transport/network failure (no HTTP response),
 * rather than an authoritative HTTP rejection from the backend.
 */
export function isTransportError(err: unknown): boolean {
  if (err instanceof ApiClientError) {
    return err.status === 0;
  }
  if (err instanceof TypeError) {
    return true;
  }
  if (err instanceof Error) {
    return (
      err.name === "TypeError" ||
      /failed to fetch|networkerror|econnrefused|ehostunreach|net::err|load failed/i.test(err.message)
    );
  }
  return false;
}

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

/**
 * Normalizes base URL and endpoint to prevent duplicate or missing slashes.
 */
export function buildApiUrl(endpoint: string, baseOverride?: string): string {
  if (endpoint.startsWith("http://") || endpoint.startsWith("https://")) {
    return endpoint;
  }
  const base = (
    baseOverride !== undefined
      ? baseOverride
      : process.env.NEXT_PUBLIC_API_URL || API_BASE_URL || ""
  )
    .trim()
    .replace(/\/+$/, "");
  if (!base) {
    throw new ApiClientError(
      "NEXT_PUBLIC_API_URL no está configurada.",
      0,
      "CONFIG_ERROR"
    );
  }
  const cleanPath = endpoint.trim().replace(/^\/+/, "");
  return `${base}/${cleanPath}`;
}

/**
 * Retrieves the Supabase access token in the browser runtime.
 * For server-side callers (Route Handlers, Server Components), pass Authorization
 * in request headers directly or use the server Supabase client.
 */
export async function getAuthToken(): Promise<string | null> {
  if (typeof window !== "undefined") {
    try {
      const { createClient } = await import("@/lib/supabase/client");
      const supabase = createClient();
      const {
        data: { session },
        error,
      } = await supabase.auth.getSession();
      if (!error && session?.access_token) {
        return session.access_token;
      }
    } catch {
      // Browser client uninitialized
    }
  }
  return null;
}

/**
 * Builds sanitized request headers.
 * Preserves caller-supplied Authorization (e.g. from Server Components) or injects
 * the browser session token if available. Never attaches identity proxy headers or secrets.
 */
export async function getAuthHeaders(
  customHeaders?: Record<string, string>
): Promise<Record<string, string>> {
  const headers: Record<string, string> = {
    Accept: "application/json",
    ...(customHeaders || {}),
  };

  // If caller already supplied Authorization header, preserve it
  if (!headers["Authorization"] && !headers["authorization"]) {
    const token = await getAuthToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
  }

  // Strip any identity proxy headers from customHeaders without violating static AST checks
  for (const key of Object.keys(headers)) {
    if (/^x-(user|tenant|course)/i.test(key)) {
      delete headers[key];
    }
  }

  return headers;
}

/**
 * Extracts a human-readable message from RFC 7807 problem details or Pydantic errors.
 */
export function parseApiError(
  status: number,
  errJson: unknown
): { message: string; code?: string; detail?: unknown } {
  if (!errJson || typeof errJson !== "object") {
    return {
      message: getDefaultErrorMessage(status),
    };
  }

  const record = errJson as Record<string, unknown>;
  const detail = record.detail;
  let code = typeof record.code === "string" ? record.code : undefined;

  if (typeof detail === "string") {
    return { message: detail, code, detail };
  }

  if (detail && typeof detail === "object") {
    if (Array.isArray(detail)) {
      // Pydantic validation error array
      const msgs = detail
        .map((item) =>
          item && typeof item === "object"
            ? (item as Record<string, unknown>).msg ||
              (item as Record<string, unknown>).message
            : null
        )
        .filter(Boolean);
      if (msgs.length > 0) {
        return {
          message: msgs.join("; "),
          code: code || "VALIDATION_ERROR",
          detail,
        };
      }
    }

    const detailObj = detail as Record<string, unknown>;
    if (typeof detailObj.code === "string") {
      code = detailObj.code;
    }
    if (typeof detailObj.detail === "string") {
      return { message: detailObj.detail, code, detail };
    }
    if (typeof detailObj.title === "string") {
      return { message: detailObj.title, code, detail };
    }
  }

  if (typeof record.message === "string") {
    return { message: record.message, code, detail };
  }

  return {
    message: getDefaultErrorMessage(status),
    code,
    detail,
  };
}

function getDefaultErrorMessage(status: number): string {
  switch (status) {
    case 401:
      return "La sesión del usuario no está autenticada o ha expirado.";
    case 403:
      return "Acceso denegado. No cuentas con permisos suficientes para esta operación.";
    case 404:
      return "El recurso solicitado no fue encontrado en el servidor predictivo.";
    case 429:
      return "Demasiadas solicitudes. Por favor intente más tarde.";
    case 500:
    case 502:
    case 503:
    case 504:
      return "Error en el servicio predictivo.";
    default:
      return `Error en la solicitud HTTP ${status}`;
  }
}

export interface ApiFetchOptions extends RequestInit {
  requireAuth?: boolean;
}

/**
 * Central fetch wrapper for the predictive & learning API.
 */
export async function apiFetch<T>(
  endpoint: string,
  options: ApiFetchOptions = {},
  roleFallback: "teacher" | "student" = "student"
): Promise<T> {
  void roleFallback;
  const url = buildApiUrl(endpoint);

  const authHeaders = await getAuthHeaders(
    options.headers as Record<string, string> | undefined
  );

  // Send Content-Type: application/json only when appropriate (body present or mutating methods with body)
  const method = (options.method || "GET").toUpperCase();
  const hasBody = Boolean(options.body);

  if (
    hasBody &&
    typeof FormData !== "undefined" &&
    options.body instanceof FormData
  ) {
    delete authHeaders["Content-Type"];
  } else if (hasBody || ["POST", "PUT", "PATCH"].includes(method)) {
    if (!authHeaders["Content-Type"]) {
      authHeaders["Content-Type"] = "application/json";
    }
  } else {
    // GET / HEAD or body-less requests do not require Content-Type
    delete authHeaders["Content-Type"];
  }

  if (options.requireAuth && !authHeaders["Authorization"]) {
    throw new ApiClientError(
      "La sesión del usuario no está autenticada.",
      401,
      "MISSING_CREDENTIALS"
    );
  }

  const { requireAuth: _, ...fetchOptions } = options;

  let response: Response;
  try {
    response = await fetch(url, {
      ...fetchOptions,
      headers: authHeaders,
    });
  } catch (netErr: unknown) {
    if (netErr instanceof Error && netErr.name === "AbortError") {
      throw netErr;
    }
    const rawMsg = netErr instanceof Error ? netErr.message : "Error de conexión de red";
    throw new ApiClientError(
      `No fue posible conectar con el servicio predictivo: ${rawMsg}`,
      0,
      "NETWORK_ERROR",
      netErr
    );
  }

  if (!response.ok) {
    let errJson: unknown = null;
    try {
      errJson = await response.json();
    } catch {
      // Body is not JSON
    }
    const { message, code, detail } = parseApiError(response.status, errJson);
    throw new ApiClientError(message, response.status, code, detail);
  }

  // Handle 204 No Content
  if (response.status === 204) {
    return {} as T;
  }

  return (await response.json()) as T;
}
