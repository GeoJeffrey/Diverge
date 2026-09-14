import { useEffect, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router";
import { api, ApiError } from "@/lib/api";
import { formatWindow, labelForPlatform, labelForReasoningCategory } from "@/lib/labels";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { ReasoningCategoryKey, ReasoningTraceResponse } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

const CATEGORY_ORDER: ReasoningCategoryKey[] = [
  "rn_onset",
  "cassi_sentiment",
  "vdi_divergence",
  "cli_capitulation",
  "duplicate_flag",
  "sentiment_variance_outlier",
];

export default function ExplainabilityPage() {
  const { symbol, setSymbol } = useOutletContext<ShellContext>();
  const [params] = useSearchParams();
  const active = (params.get("symbol") ?? symbol).toUpperCase();
  const [data, setData] = useState<ReasoningTraceResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.reasoning(active);
      setData(res);
      setSymbol(active);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load reasoning.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (loading) return <LoadingState label="Loading Why this score…" />;
  if (error || !data) return <ErrorState message={error ?? "Missing data."} onRetry={() => void load()} />;

  return (
    <div className="px-4 py-5 md:px-7">
      <h2 className="text-lg font-bold">Why this score · {data.symbol}</h2>
      <p className="mb-5 text-sm text-[#6b6b6b]">
        {data.total_traces} evidence posts · {formatWindow(data.window_start_utc)}
      </p>

      <div className="grid gap-4">
        {CATEGORY_ORDER.map((key) => {
          const items = data.categories[key] ?? [];
          return (
            <section key={key} className="rounded-xl border border-[#e7e1d8] bg-white p-5">
              <h3 className="font-bold">{labelForReasoningCategory(key)}</h3>
              {items.length === 0 ? (
                <p className="mt-2 text-sm text-[#6b6b6b]">No posts in this driver for the current window.</p>
              ) : (
                <ul className="mt-3 divide-y divide-[#f0ede8]">
                  {items.map((item) => (
                    <li key={item.trace_id} className="py-3">
                      <p className="text-sm leading-relaxed text-[#333]">{item.text_preview}</p>
                      <p className="mt-1 font-mono text-xs text-[#6b6b6b]">
                        {labelForPlatform(item.platform)} · {item.account_id} · weight {item.weight.toFixed(2)} · {item.upvotes} upvotes
                      </p>
                    </li>
                  ))}
                </ul>
              )}
            </section>
          );
        })}
      </div>
    </div>
  );
}
