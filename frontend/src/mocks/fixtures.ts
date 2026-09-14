import type {
  AuthTokenResponse,
  CoordinationMetric,
  HealthResponse,
  IndexMetricValue,
  IndicesBreakdown,
  ReasoningTraceResponse,
  TickerAdvancedResponse,
  TickerSimpleItem,
  UserProfileResponse,
} from "@/types/api";

const WINDOW = "2026-06-11T19:40:24.121335Z";
const WINDOW_END = "2026-09-10T01:14:12.000000Z";

function metric(
  label: string,
  score: number | null,
  available: boolean,
  coverage_note: string | null,
): IndexMetricValue {
  return { label, score, available, coverage_note };
}

function indices(partial: Partial<IndicesBreakdown>): IndicesBreakdown {
  return {
    rn: partial.rn ?? metric("Contagion Core", 1.34, true, null),
    cirg: partial.cirg ?? metric("Reality Check", 0.62, true, null),
    cli: partial.cli ?? metric("Capitulation Signal", 0.29, true, null),
    cassi: partial.cassi ?? metric("Cross-Market Spillover", 0.71, true, null),
    vdi: partial.vdi ?? metric("Language Divergence", 0.44, true, null),
  };
}

function trust(score: number, flag: CoordinationMetric["confidence_flag"]): CoordinationMetric {
  return {
    label: "Trust Score",
    coordination_score: score,
    confidence_flag: flag,
    available: true,
    coverage_note: null,
  };
}

export const mockUsers: Array<UserProfileResponse & { password: string }> = [
  {
    id: "a1b2c3d4-e5f6-7a8b-9c0d-1e2f3a4b5c6d",
    email: "trader@example.com",
    password: "SecurePass123!",
    full_name: "Jane Doe",
    role: "pro",
    created_at: "2026-06-01T12:00:00.000Z",
  },
];

export const health: HealthResponse = {
  status: "healthy",
  version: "1.0.0",
  database: "connected",
  timestamp_utc: "2026-09-10T01:30:00.000Z",
};

export const tickerList: TickerSimpleItem[] = [
  {
    id: "INFY",
    symbol: "INFY",
    name: "Infosys Ltd.",
    sector: "Information Technology",
    score: 54.6,
    verdict_label: "mixed",
    why_sentence:
      "Narrative momentum is building around digital pipeline commentary, while consumer reviews still lag investor optimism.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "TCS",
    symbol: "TCS",
    name: "Tata Consultancy Services",
    sector: "Information Technology",
    score: 61.2,
    verdict_label: "mixed",
    why_sentence:
      "Deal-win chatter is lifting the composite, with language between regional forums and English coverage starting to line up.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "RELIANCE",
    symbol: "RELIANCE",
    name: "Reliance Industries Ltd.",
    sector: "Conglomerate",
    score: 74.0,
    verdict_label: "building",
    why_sentence:
      "Cross-business narrative is strengthening: retail and energy commentary are reinforcing each other rather than competing.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "TATASTEEL",
    symbol: "TATASTEEL",
    name: "Tata Steel Ltd.",
    sector: "Basic Materials",
    score: 67.0,
    verdict_label: "building",
    why_sentence:
      "Infrastructure demand talk is spreading quickly, and reality-check signals from operations commentary are not contradicting it.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "HDFCBANK",
    symbol: "HDFCBANK",
    name: "HDFC Bank Ltd.",
    sector: "Financial Services",
    score: 38.4,
    verdict_label: "fading",
    why_sentence:
      "Deposit-growth worry is crowding out earlier optimism; trust in the conversation is lower because similar posts keep repeating.",
    trust_label: "Low confidence — possible manipulation detected",
    window_start_utc: WINDOW,
  },
  {
    id: "WIPRO",
    symbol: "WIPRO",
    name: "Wipro Ltd.",
    sector: "Information Technology",
    score: 55.1,
    verdict_label: "mixed",
    why_sentence:
      "The tape is split: some threads point to a pipeline recovery, others stay cautious on margins.",
    trust_label: "Moderate confidence — treat with caution",
    window_start_utc: WINDOW,
  },
  {
    id: "ONGC",
    symbol: "ONGC",
    name: "Oil and Natural Gas Corporation",
    sector: "Energy",
    score: 71.3,
    verdict_label: "building",
    why_sentence:
      "Energy-price narratives are consistent across platforms, with little sign of coordinated copy-paste activity.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "BAJFINANCE",
    symbol: "BAJFINANCE",
    name: "Bajaj Finance Ltd.",
    sector: "Financial Services",
    score: 48.2,
    verdict_label: "mixed",
    why_sentence:
      "Retail credit commentary is mixed: growth stories sit next to asset-quality caution.",
    trust_label: "Moderate confidence — treat with caution",
    window_start_utc: WINDOW,
  },
  {
    id: "HINDUNILVR",
    symbol: "HINDUNILVR",
    name: "Hindustan Unilever Ltd.",
    sector: "Consumer Goods",
    score: 59.8,
    verdict_label: "mixed",
    why_sentence:
      "Consumer-review tone is steadier than investor chatter, which keeps the reading in a mixed band.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "MARUTI",
    symbol: "MARUTI",
    name: "Maruti Suzuki India Ltd.",
    sector: "Automotive",
    score: 64.4,
    verdict_label: "mixed",
    why_sentence:
      "Demand-recovery language is building, especially in vernacular threads, while institutional coverage stays measured.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "TATAMOTORS",
    symbol: "TATAMOTORS",
    name: "Tata Motors Ltd.",
    sector: "Automotive",
    score: 52.0,
    verdict_label: "mixed",
    why_sentence:
      "EV narrative is loud, but reality-check signals from product reviews are keeping the composite from running ahead.",
    trust_label: "Moderate confidence — treat with caution",
    window_start_utc: WINDOW,
  },
  {
    id: "ITC",
    symbol: "ITC",
    name: "ITC Ltd.",
    sector: "Consumer Goods",
    score: 57.5,
    verdict_label: "mixed",
    why_sentence:
      "FMCG commentary is orderly; there is no strong contagion or capitulation overlay in this window.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "BHARTIARTL",
    symbol: "BHARTIARTL",
    name: "Bharti Airtel Ltd.",
    sector: "Consumer Discretionary",
    score: 66.1,
    verdict_label: "building",
    why_sentence:
      "Tariff and subscriber narratives are reinforcing each other without a spike in coordinated posting.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "SBIN",
    symbol: "SBIN",
    name: "State Bank of India",
    sector: "Financial Services",
    score: 44.7,
    verdict_label: "mixed",
    why_sentence:
      "Public-sector bank chatter is cautious on asset quality, offsetting pockets of dividend optimism.",
    trust_label: "High confidence",
    window_start_utc: WINDOW,
  },
  {
    id: "ADANIENT",
    symbol: "ADANIENT",
    name: "Adani Enterprises Ltd.",
    sector: "Conglomerate",
    score: 41.0,
    verdict_label: "mixed",
    why_sentence:
      "Trust in the conversation is thin: similar wording is repeating across accounts, so the composite is discounted.",
    trust_label: "Low confidence — possible manipulation detected",
    window_start_utc: WINDOW,
  },
  {
    id: "AAPL",
    symbol: "AAPL",
    name: "Apple Inc.",
    sector: "Information Technology",
    score: null,
    verdict_label: "insufficient_data",
    why_sentence: "Not enough overlapping coverage yet for a reliable reading on this name.",
    trust_label: "Not enough data",
    window_start_utc: WINDOW,
  },
];

const phylogenyBase: TickerAdvancedResponse["phylogeny_context"] = [
  {
    window_start_utc: "2026-06-04T19:40:24.121335Z",
    mutation_type: "stable",
    mutation_detail: { current_dominant: "rn", prior_dominant: "rn" },
    composite_delta: 0.4,
  },
  {
    window_start_utc: "2026-06-08T19:40:24.121335Z",
    mutation_type: "dominant_index_shift",
    mutation_detail: { current_dominant: "cirg", prior_dominant: "rn" },
    composite_delta: -1.8,
  },
  {
    window_start_utc: WINDOW,
    mutation_type: "new_risk_flag",
    mutation_detail: { flag: "consumer_reality_underpriced" },
    composite_delta: 1.1,
  },
];

function advanced(
  symbol: string,
  extras: Partial<TickerAdvancedResponse> & { indices?: IndicesBreakdown },
): TickerAdvancedResponse {
  const simple = tickerList.find((t) => t.symbol === symbol)!;
  return {
    symbol,
    name: simple.name,
    sector: simple.sector,
    window_start_utc: WINDOW,
    window_end_utc: WINDOW_END,
    composite_score: simple.score,
    dominant_index: "rn",
    risk_flags: [],
    aggregation_confidence: "high_trust",
    indices: extras.indices ?? indices({}),
    coordination: trust(32.5, "high_trust"),
    phylogeny_context: phylogenyBase,
    ...extras,
  };
}

export const advancedBySymbol: Record<string, TickerAdvancedResponse> = {
  INFY: advanced("INFY", {
    dominant_index: "rn",
    risk_flags: ["consumer_reality_underpriced"],
    aggregation_confidence: "high_trust",
    indices: indices({
      rn: metric("Contagion Core", 1.34, true, null),
      cirg: metric("Reality Check", 0.62, true, null),
      cli: metric("Capitulation Signal", 0.29, true, null),
      cassi: metric(
        "Cross-Market Spillover",
        null,
        false,
        "Needs 30+ days of overlapping multi-ticker data, currently at 12 days",
      ),
      vdi: metric("Language Divergence", 0.44, true, null),
    }),
    coordination: trust(28.0, "high_trust"),
  }),
  TCS: advanced("TCS", {
    dominant_index: "vdi",
    indices: indices({
      rn: metric("Contagion Core", 1.18, true, null),
      cirg: metric("Reality Check", 0.55, true, null),
      cli: metric("Capitulation Signal", 0.22, true, null),
      cassi: metric("Cross-Market Spillover", 0.66, true, null),
      vdi: metric("Language Divergence", 0.71, true, null),
    }),
  }),
  RELIANCE: advanced("RELIANCE", {
    dominant_index: "cassi",
    aggregation_confidence: "high_trust",
    indices: indices({
      rn: metric("Contagion Core", 1.41, true, null),
      cirg: metric("Reality Check", 0.7, true, null),
      cli: metric("Capitulation Signal", 0.18, true, null),
      cassi: metric("Cross-Market Spillover", 0.83, true, null),
      vdi: metric("Language Divergence", 0.61, true, null),
    }),
    coordination: trust(22.0, "high_trust"),
  }),
  TATASTEEL: advanced("TATASTEEL", {
    dominant_index: "rn",
    indices: indices({
      rn: metric("Contagion Core", 1.27, true, null),
      cirg: metric("Reality Check", 0.65, true, null),
      cli: metric("Capitulation Signal", 0.29, true, null),
      cassi: metric("Cross-Market Spillover", 0.74, true, null),
      vdi: metric("Language Divergence", 0.55, true, null),
    }),
    coordination: trust(19.4, "high_trust"),
  }),
  HDFCBANK: advanced("HDFCBANK", {
    dominant_index: "cli",
    risk_flags: ["coordination_spike", "duplicate_cluster"],
    aggregation_confidence: "low_trust",
    indices: indices({
      rn: metric("Contagion Core", 0.94, true, null),
      cirg: metric("Reality Check", 0.41, true, null),
      cli: metric("Capitulation Signal", 0.71, true, null),
      cassi: metric("Cross-Market Spillover", 0.38, true, null),
      vdi: metric("Language Divergence", 0.33, true, null),
    }),
    coordination: trust(72.4, "low_trust"),
    phylogeny_context: [
      {
        window_start_utc: "2026-06-04T19:40:24.121335Z",
        mutation_type: "stable",
        mutation_detail: {},
        composite_delta: -0.2,
      },
      {
        window_start_utc: "2026-06-08T19:40:24.121335Z",
        mutation_type: "composite_reversal",
        mutation_detail: {},
        composite_delta: -6.1,
      },
      {
        window_start_utc: WINDOW,
        mutation_type: "new_risk_flag",
        mutation_detail: { flag: "coordination_spike" },
        composite_delta: -3.4,
      },
    ],
  }),
  WIPRO: advanced("WIPRO", {
    dominant_index: "cirg",
    aggregation_confidence: "moderate",
    indices: indices({
      rn: metric("Contagion Core", 1.02, true, null),
      cirg: metric("Reality Check", 0.58, true, null),
      cli: metric("Capitulation Signal", 0.34, true, null),
      cassi: metric(
        "Cross-Market Spillover",
        null,
        false,
        "Needs 30+ days of overlapping multi-ticker data, currently at 18 days",
      ),
      vdi: metric("Language Divergence", 0.49, true, null),
    }),
    coordination: trust(41.2, "moderate"),
  }),
  ONGC: advanced("ONGC", {
    dominant_index: "cassi",
    indices: indices({
      rn: metric("Contagion Core", 1.22, true, null),
      cirg: metric("Reality Check", 0.6, true, null),
      cli: metric("Capitulation Signal", 0.21, true, null),
      cassi: metric("Cross-Market Spillover", 0.79, true, null),
      vdi: metric("Language Divergence", 0.4, true, null),
    }),
  }),
  BAJFINANCE: advanced("BAJFINANCE", {
    dominant_index: "cli",
    aggregation_confidence: "moderate",
    coordination: trust(46.8, "moderate"),
  }),
  HINDUNILVR: advanced("HINDUNILVR", {
    dominant_index: "cirg",
    indices: indices({
      rn: metric("Contagion Core", 0.88, true, null),
      cirg: metric("Reality Check", 0.73, true, null),
      cli: metric("Capitulation Signal", 0.19, true, null),
      cassi: metric("Cross-Market Spillover", 0.52, true, null),
      vdi: metric("Language Divergence", 0.36, true, null),
    }),
  }),
  MARUTI: advanced("MARUTI", {
    dominant_index: "vdi",
  }),
  TATAMOTORS: advanced("TATAMOTORS", {
    dominant_index: "cirg",
    aggregation_confidence: "moderate",
    risk_flags: ["consumer_reality_underpriced"],
    coordination: trust(44.0, "moderate"),
  }),
  ITC: advanced("ITC", {
    dominant_index: "cirg",
  }),
  BHARTIARTL: advanced("BHARTIARTL", {
    dominant_index: "rn",
  }),
  SBIN: advanced("SBIN", {
    dominant_index: "cli",
  }),
  ADANIENT: advanced("ADANIENT", {
    dominant_index: "rn",
    aggregation_confidence: "low_trust",
    risk_flags: ["coordination_spike"],
    coordination: trust(81.2, "low_trust"),
  }),
  AAPL: advanced("AAPL", {
    composite_score: null,
    dominant_index: "insufficient_data",
    aggregation_confidence: "insufficient_data",
    indices: {
      rn: metric(
        "Contagion Core",
        null,
        false,
        "Needs 14+ days of overlapping source coverage, currently at 3 days",
      ),
      cirg: metric(
        "Reality Check",
        null,
        false,
        "Needs paired consumer-review and investor-thread coverage, currently unmatched",
      ),
      cli: metric(
        "Capitulation Signal",
        null,
        false,
        "Needs 200+ scored posts in-window, currently at 41 posts",
      ),
      cassi: metric(
        "Cross-Market Spillover",
        null,
        false,
        "Needs 30+ days of overlapping multi-ticker data, currently at 3 days",
      ),
      vdi: metric(
        "Language Divergence",
        null,
        false,
        "Needs bilingual vernacular and English samples in the same window",
      ),
    },
    coordination: {
      label: "Trust Score",
      coordination_score: 0,
      confidence_flag: "insufficient_data",
      available: false,
      coverage_note: "Needs a larger unique-author set before a trust reading is published",
    },
    phylogeny_context: [],
  }),
};

function traces(symbol: string): ReasoningTraceResponse {
  return {
    symbol,
    window_start_utc: WINDOW,
    total_traces: 6,
    categories: {
      rn_onset: [
        {
          trace_id: 1042,
          post_id: "tw_182937461928",
          account_id: "trader_daily_in",
          platform: "stocktwits",
          weight: 0.85,
          upvotes: 14,
          text_preview: `${symbol} Q2 margins expanding faster than expected, digital cloud pipeline strong into next quarter...`,
        },
      ],
      cassi_sentiment: [
        {
          trace_id: 1043,
          post_id: "rd_99812",
          account_id: "infra_watch",
          platform: "reddit",
          weight: 0.72,
          upvotes: 41,
          text_preview: "Domestic demand commentary is lining up with commodity threads rather than fighting them...",
        },
      ],
      vdi_divergence: [
        {
          trace_id: 1044,
          post_id: "tg_44190",
          account_id: "market_se_baat",
          platform: "telegram",
          weight: 0.66,
          upvotes: 9,
          text_preview: "Regional chats are more optimistic than English coverage on the same name this week...",
        },
      ],
      cli_capitulation: [
        {
          trace_id: 1045,
          post_id: "rss_2211",
          account_id: "desk_notes",
          platform: "rss_news",
          weight: 0.4,
          upvotes: 0,
          text_preview: "Management tone on the call was cautious; stop-loss language is picking up in comments...",
        },
      ],
      duplicate_flag: [
        {
          trace_id: 1046,
          post_id: "rd_dup_12",
          account_id: "copy_cluster_a",
          platform: "reddit",
          weight: 0.31,
          upvotes: 2,
          text_preview: "Near-identical wording appearing across newly created accounts within minutes...",
        },
      ],
      sentiment_variance_outlier: [
        {
          trace_id: 1047,
          post_id: "gt_3301",
          account_id: "search_pulse",
          platform: "google_trends",
          weight: 0.22,
          upvotes: 0,
          text_preview: "Search interest jumped without a matching news event in the same hour...",
        },
      ],
    },
  };
}

export const reasoningBySymbol: Record<string, ReasoningTraceResponse> = Object.fromEntries(
  tickerList.map((t) => [t.symbol, traces(t.symbol)]),
);

export function issueTokens(userId: string): AuthTokenResponse {
  return {
    access_token: `mock-access.${userId}.${Date.now()}`,
    refresh_token: `mock-refresh.${userId}.${Date.now()}`,
    token_type: "Bearer",
    expires_in: 3600,
  };
}
