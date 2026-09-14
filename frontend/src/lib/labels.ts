import type {
  ConfidenceFlag,
  IndexKey,
  MutationType,
  Platform,
  ReasoningCategoryKey,
  VerdictLabel,
} from "@/types/api";

/** Approved human-readable labels. Never render IndexKey values in the UI. */
export const INDEX_LABELS: Record<IndexKey, string> = {
  rn: "Contagion Core",
  cirg: "Reality Check",
  cli: "Capitulation Signal",
  cassi: "Cross-Market Spillover",
  vdi: "Language Divergence",
};

export const INDEX_ACCENTS: Record<IndexKey, string> = {
  rn: "#c4510b",
  cirg: "#d4970f",
  cli: "#5a3d7a",
  cassi: "#2f6f7a",
  vdi: "#3a6ea8",
};

export function labelForIndexKey(key: string): string {
  if (key === "insufficient_data") return "Not yet available";
  if (key in INDEX_LABELS) {
    return INDEX_LABELS[key as IndexKey];
  }
  return "Narrative driver";
}

export const REASONING_CATEGORY_LABELS: Record<ReasoningCategoryKey, string> = {
  rn_onset: "Virality onset",
  cassi_sentiment: "Cross-market sentiment",
  vdi_divergence: "Regional vernacular",
  cli_capitulation: "Capitulation signals",
  duplicate_flag: "Near-duplicates",
  sentiment_variance_outlier: "Uncharacteristic consensus",
};

export function labelForReasoningCategory(key: string): string {
  if (key in REASONING_CATEGORY_LABELS) {
    return REASONING_CATEGORY_LABELS[key as ReasoningCategoryKey];
  }
  return "Source evidence";
}

export function labelForMutation(type: MutationType): string {
  const map: Record<MutationType, string> = {
    stable: "Stable narrative",
    dominant_index_shift: "Leading driver changed",
    composite_reversal: "Composite reversed",
    new_risk_flag: "New risk flag",
    flag_resolved: "Risk flag resolved",
  };
  return map[type];
}

export function labelForVerdict(verdict: VerdictLabel): string {
  const map: Record<VerdictLabel, string> = {
    building: "Building",
    mixed: "Mixed",
    fading: "Fading",
    insufficient_data: "Not enough data",
  };
  return map[verdict];
}

export function labelForConfidence(flag: ConfidenceFlag): string {
  const map: Record<ConfidenceFlag, string> = {
    high_trust: "High confidence",
    moderate: "Moderate confidence",
    low_trust: "Low confidence",
    insufficient_data: "Not enough data",
  };
  return map[flag];
}

export function labelForPlatform(platform: Platform): string {
  const map: Record<Platform, string> = {
    stocktwits: "StockTwits",
    reddit: "Reddit",
    telegram: "Telegram",
    rss_news: "News",
    google_trends: "Search trends",
  };
  return map[platform];
}

export function labelForRole(role: string): string {
  if (role === "pro") return "Pro";
  if (role === "admin") return "Admin";
  return "Standard";
}

export function formatWindow(iso: string | null | undefined): string {
  if (!iso) return "Latest window";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return new Intl.DateTimeFormat("en-IN", {
    dateStyle: "medium",
    timeStyle: "short",
    timeZone: "UTC",
  }).format(d) + " UTC";
}

export function formatRiskFlag(flag: string): string {
  return flag
    .split("_")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1))
    .join(" ");
}
