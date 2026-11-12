import { supabase } from "../supabase";
import type { AnalysisDetail, AnalysisSummary, FeatureRow, ForwardingConfig, Health, ModelInfo } from "../types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined) ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

type ApiInit = RequestInit & { token?: string };

async function authHeaders(token?: string): Promise<Record<string, string>> {
  if (token) return { Authorization: `Bearer ${token}` };
  if (!supabase) return {};
  const { data } = await supabase.auth.getSession();
  const accessToken = data.session?.access_token;
  return accessToken ? { Authorization: `Bearer ${accessToken}` } : {};
}

export async function apiFetch<T>(path: string, init: ApiInit = {}): Promise<T> {
  const { token, ...requestInit } = init;
  const res = await fetch(`${API_BASE_URL}${path}`, {
    ...requestInit,
    headers: { ...(await authHeaders(token)), ...(requestInit.headers ?? {}) },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    if (res.status === 401 && supabase) await supabase.auth.signOut();
    throw new ApiError(res.status, detail);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const form = (file: File) => {
  const f = new FormData();
  f.append("file", file);
  return f;
};

export const api = {
  health: () => apiFetch<Health>("/api/health"),
  model: () => apiFetch<ModelInfo>("/api/model"),
  list: (limit = 50, offset = 0) =>
    apiFetch<{ items: AnalysisSummary[]; total: number }>(`/api/analyses?limit=${limit}&offset=${offset}`),
  get: (id: string) => apiFetch<AnalysisDetail>(`/api/analyses/${id}`),
  features: (id: string) => apiFetch<FeatureRow[]>(`/api/analyses/${id}/features`),
  remove: (id: string) => apiFetch<void>(`/api/analyses/${id}`, { method: "DELETE" }),
  upload: (file: File) => apiFetch<AnalysisDetail>("/api/analyses/upload", { method: "POST", body: form(file) }),
  baseline: (file: File) =>
    apiFetch<{ sender: string; message_count: number; note: string }>("/api/baseline", { method: "POST", body: form(file) }),
  alias: () => apiFetch<{ address: string; token: string }>("/api/me/alias"),
  forwardingConfig: () => apiFetch<ForwardingConfig>("/api/forwarding"),
};
