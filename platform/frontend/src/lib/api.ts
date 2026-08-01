import type {
  CoverageMatrix,
  RunResponse,
  RunSummaryResponse,
  ScenarioSummary,
} from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
const TOKEN_STORAGE_KEY = "eadadl_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(TOKEN_STORAGE_KEY);
}

export function setToken(token: string): void {
  window.localStorage.setItem(TOKEN_STORAGE_KEY, token);
}

export function clearToken(): void {
  window.localStorage.removeItem(TOKEN_STORAGE_KEY);
}

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken();
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (options.body && !(options.body instanceof URLSearchParams)) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(`${API_BASE_URL}${path}`, { ...options, headers });

  if (!response.ok) {
    const body = await response.json().catch(() => ({ detail: response.statusText }));
    throw new ApiError(response.status, body.detail ?? "Request failed");
  }

  return (await response.json()) as T;
}

export async function login(username: string, password: string): Promise<void> {
  const body = new URLSearchParams({ username, password });
  const result = await request<{ access_token: string }>("/auth/login", {
    method: "POST",
    body,
  });
  setToken(result.access_token);
}

export function listScenarios(): Promise<ScenarioSummary[]> {
  return request<ScenarioSummary[]>("/scenarios");
}

export function listRuns(): Promise<RunSummaryResponse[]> {
  return request<RunSummaryResponse[]>("/runs");
}

export function getRun(id: string): Promise<RunResponse> {
  return request<RunResponse>(`/runs/${id}`);
}

export function createRun(scenario: string, mode: "dry_run" | "live" = "dry_run"): Promise<RunResponse> {
  return request<RunResponse>("/runs", {
    method: "POST",
    body: JSON.stringify({ scenario, mode }),
  });
}

export function getCoverage(): Promise<CoverageMatrix> {
  return request<CoverageMatrix>("/coverage");
}

export { ApiError };
