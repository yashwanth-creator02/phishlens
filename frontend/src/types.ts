export type Band = "LOW" | "MEDIUM" | "HIGH";

export interface Reason {
  rank: number;
  rule_key: string;
  group: string;
  contribution: number;
  sentence: string;
}

export interface AnalysisSummary {
  id: string;
  created_at: string;
  sender_address: string;
  sender_name: string;
  subject: string;
  scope: "direct" | "forward_attachment" | "forward_inline";
  risk_score: number;
  risk_band: Band;
  model_version: string;
}

export interface AnalysisDetail extends AnalysisSummary {
  probability: number;
  forwarded_by: string;
  auth: Record<string, string>;
  guidance: string;
  reasons: Reason[];
  links: { href: string; text: string }[];
  attachments: { filename: string; content_type: string; size: number; sha256: string }[];
  text_preview: string;
  headers: Record<string, string>;
  history_message_count: number;
}

export interface FeatureRow {
  name: string;
  group: string;
  value: number;
  contribution: number;
}

export interface ModelInfo {
  version_tag: string;
  algorithm: string;
  trained_at: string | null;
  metrics: Record<string, number>;
  data_source: string;
  n_features: number;
}

export interface Health {
  status: string;
  model_loaded: boolean;
  model?: string;
  detail?: string;
  auth_mode: string;
}

export interface ForwardingConfig {
  alias_domain: string;
  alias_pattern: string;
  inbound_configured: boolean;
}
