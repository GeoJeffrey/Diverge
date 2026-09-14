import type { ErrorResponse } from "@/types/api";
import { mockRequest } from "@/mocks/handler";
import { sessionStore } from "@/lib/session";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "mock";

export class ApiError extends Error {
  status: number;
  payload: ErrorResponse;

  constructor(status: number, payload: ErrorResponse) {
    super(payload.message);
    this.status = status;
    this.payload = payload;
  }
}

function isMock(): boolean {
  return API_BASE_URL === "mock" || API_BASE_URL.startsWith("mock:");
}

async function parseBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) return null;
  try {
    return JSON.parse(text);
  } catch {
    return { error_code: "UNPARSEABLE", message: text };
  }
}

async function liveFetch(path: string, init: RequestInit): Promise<{ status: number; body: unknown }> {
  const res = await fetch(`${API_BASE_URL}${path}`, init);
  const body = await parseBody(res);
  return { status: res.status, body };
}

export async function apiFetch<T>(
  path: string,
  options: {
    method?: string;
    body?: unknown;
    auth?: boolean;
    query?: Record<string, string | undefined>;
  } = {},
): Promise<T> {
  const method = options.method ?? "GET";
  const params = new URLSearchParams();
  if (options.query) {
    for (const [k, v] of Object.entries(options.query)) {
      if (v) params.set(k, v);
    }
  }
  const qs = params.toString();
  const urlPath = qs ? `${path}?${qs}` : path;

  if (options.auth && sessionStore.isAccessExpired()) {
    const refresh = sessionStore.getRefreshToken();
    if (refresh) {
      try {
        const tokens = await apiFetch<{
          access_token: string;
          refresh_token: string;
          expires_in: number;
        }>("/auth/refresh", { method: "POST", body: { refresh_token: refresh } });
        sessionStore.setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
      } catch {
        sessionStore.clear();
      }
    }
  }

  const access = sessionStore.getAccessToken();
  const headers: Record<string, string> = {
    Accept: "application/json",
  };
  if (options.body !== undefined) headers["Content-Type"] = "application/json";
  if (access) headers.Authorization = `Bearer ${access}`;

  let status: number;
  let body: unknown;

  if (isMock()) {
    const result = await mockRequest(method, urlPath, options.body, access);
    status = result.status;
    body = result.body;
  } else {
    const result = await liveFetch(urlPath, {
      method,
      headers,
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
    });
    status = result.status;
    body = result.body;
  }

  if (status === 401 && !urlPath.startsWith("/auth/login") && !urlPath.startsWith("/auth/signup")) {
    sessionStore.clear();
    if (typeof window !== "undefined" && !window.location.pathname.startsWith("/login")) {
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.assign(`/login?next=${next}`);
    }
  }

  if (status >= 400) {
    const err = (body ?? {}) as ErrorResponse;
    throw new ApiError(status, {
      error_code: err.error_code ?? "ERROR",
      message: err.message ?? "Request failed",
      details: err.details ?? null,
    });
  }

  return body as T;
}

export const api = {
  health: () => apiFetch("/health"),
  tickers: () => apiFetch<{ total: number; tickers: import("@/types/api").TickerSimpleItem[] }>("/tickers"),
  ticker: (symbol: string, window?: string) =>
    apiFetch<import("@/types/api").TickerAdvancedResponse>(`/ticker/${encodeURIComponent(symbol)}`, {
      query: { window },
      auth: true,
    }),
  tickerSimple: (symbol: string, window?: string) =>
    apiFetch<import("@/types/api").TickerSimpleResponse>(`/ticker/${encodeURIComponent(symbol)}/simple`, {
      query: { window },
    }),
  reasoning: (symbol: string, window?: string) =>
    apiFetch<import("@/types/api").ReasoningTraceResponse>(`/ticker/${encodeURIComponent(symbol)}/reasoning`, {
      query: { window },
      auth: true,
    }),
  login: (email: string, password: string) =>
    apiFetch<import("@/types/api").AuthTokenResponse>("/auth/login", {
      method: "POST",
      body: { email, password },
    }),
  signup: (email: string, password: string, full_name: string) =>
    apiFetch<import("@/types/api").AuthTokenResponse>("/auth/signup", {
      method: "POST",
      body: { email, password, full_name },
    }),
  me: () => apiFetch<import("@/types/api").UserProfileResponse>("/auth/me", { auth: true }),
};
