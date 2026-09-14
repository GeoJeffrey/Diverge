export type HealthStatus = "healthy" | "degraded" | "unhealthy";
export type DatabaseStatus = "connected" | "disconnected";
export type VerdictLabel = "building" | "mixed" | "fading" | "insufficient_data";
export type ConfidenceFlag = "high_trust" | "moderate" | "low_trust" | "insufficient_data";
export type UserRole = "standard" | "pro" | "admin";
export type MutationType =
  | "stable"
  | "dominant_index_shift"
  | "composite_reversal"
  | "new_risk_flag"
  | "flag_resolved";
export type Platform =
  | "stocktwits"
  | "reddit"
  | "telegram"
  | "rss_news"
  | "google_trends";

export interface HealthResponse {
  status: HealthStatus;
  version: string;
  database: DatabaseStatus;
  timestamp_utc: string;
}

export interface ErrorResponse {
  error_code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface SignupRequest {
  email: string;
  password: string;
  full_name: string;
}

export interface LoginRequest {
  email: string;
  password: string;
}

export interface RefreshTokenRequest {
  refresh_token: string;
}

export interface AuthTokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

export interface UserProfileResponse {
  id: string;
  email: string;
  full_name: string;
  role: UserRole;
  created_at: string;
}

export interface IndexMetricValue {
  label: string;
  score: number | null;
  available: boolean;
  coverage_note: string | null;
}

export interface TickerSimpleItem {
  id: string;
  symbol: string;
  name: string;
  sector: string;
  score: number | null;
  verdict_label: VerdictLabel;
  why_sentence: string;
  trust_label: string;
  window_start_utc: string;
}

export interface TickerListResponse {
  total: number;
  tickers: TickerSimpleItem[];
}

export type TickerSimpleResponse = TickerSimpleItem;

export interface IndicesBreakdown {
  rn: IndexMetricValue;
  cirg: IndexMetricValue;
  cli: IndexMetricValue;
  cassi: IndexMetricValue;
  vdi: IndexMetricValue;
}

export interface CoordinationMetric {
  label: string;
  coordination_score: number;
  confidence_flag: ConfidenceFlag;
  available: boolean;
  coverage_note: string | null;
}

export interface PhylogenyTransitionItem {
  window_start_utc: string;
  mutation_type: MutationType;
  mutation_detail: Record<string, unknown>;
  composite_delta: number | null;
}

export interface TickerAdvancedResponse {
  symbol: string;
  name: string;
  sector: string;
  window_start_utc: string;
  window_end_utc: string | null;
  composite_score: number | null;
  dominant_index: string;
  risk_flags: string[];
  aggregation_confidence: ConfidenceFlag;
  indices: IndicesBreakdown;
  coordination: CoordinationMetric;
  phylogeny_context: PhylogenyTransitionItem[];
}

export interface ReasoningTraceItem {
  trace_id: number;
  post_id: string;
  account_id: string;
  platform: Platform;
  weight: number;
  upvotes: number;
  text_preview: string;
}

export type ReasoningCategoryKey =
  | "rn_onset"
  | "cassi_sentiment"
  | "vdi_divergence"
  | "cli_capitulation"
  | "duplicate_flag"
  | "sentiment_variance_outlier";

export interface ReasoningTraceResponse {
  symbol: string;
  window_start_utc: string | null;
  total_traces: number;
  categories: Partial<Record<ReasoningCategoryKey, ReasoningTraceItem[]>> &
    Record<string, ReasoningTraceItem[] | undefined>;
}

export type IndexKey = keyof IndicesBreakdown;
