import { supabase } from "../supabase";
import type { AnalysisDetail, AnalysisSummary, FeatureRow, Health, ModelInfo } from "../types";

async function authHeaders(): Promise<Record<string, string>> {
  if (!supabase) return {};
  const { data } = await supabase.auth.getSession();
  const token = data.session?.access_token;
  return token ? { Authorization: `Bearer ${token}` } : {};
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(path, { ...init, headers: { ...(await authHeaders()), ...(init.headers ?? {}) } });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      detail = (await res.json()).detail ?? detail;
    } catch {
      /* body was not JSON */
    }
    throw new Error(`${res.status}: ${detail}`);
  }
  return res.status === 204 ? (undefined as T) : ((await res.json()) as T);
}

const form = (file: File) => {
  const f = new FormData();
  f.append("file", file);
  return f;
};

export const api = {
  health: () => request<Health>("/api/health"),
  model: () => request<ModelInfo>("/api/model"),
  list: (limit = 50, offset = 0) =>
    request<{ items: AnalysisSummary[]; total: number }>(`/api/analyses?limit=${limit}&offset=${offset}`),
  get: (id: string) => request<AnalysisDetail>(`/api/analyses/${id}`),
  features: (id: string) => request<FeatureRow[]>(`/api/analyses/${id}/features`),
  remove: (id: string) => request<void>(`/api/analyses/${id}`, { method: "DELETE" }),
  upload: (file: File) => request<AnalysisDetail>("/api/analyses/upload", { method: "POST", body: form(file) }),
  baseline: (file: File) =>
    request<{ sender: string; message_count: number; note: string }>("/api/baseline", { method: "POST", body: form(file) }),
  alias: () => request<{ address: string; token: string }>("/api/me/alias"),
};
