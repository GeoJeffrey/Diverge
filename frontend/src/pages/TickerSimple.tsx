import { useEffect, useState } from "react";
import { useOutletContext, useParams } from "react-router";
import { api, ApiError } from "@/lib/api";
import { formatWindow } from "@/lib/labels";
import { TrustBadge, VerdictBadge } from "@/components/TrustBadge";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { TickerSimpleResponse } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

export default function TickerSimple() {
  const { symbol: routeSymbol } = useParams();
  const { symbol: ctxSymbol, setSymbol } = useOutletContext<ShellContext>();
  const symbol = (routeSymbol ?? ctxSymbol).toUpperCase();
  const [data, setData] = useState<TickerSimpleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.tickerSimple(symbol);
      setData(res);
      setSymbol(symbol);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load summary.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  if (loading) return <LoadingState label="Loading plain-language summary…" />;
  if (error || !data) return <ErrorState message={error ?? "Missing ticker."} onRetry={() => void load()} />;

  return (
    <div className="px-4 py-5 md:px-7">
      <div className="mb-5 rounded-xl bg-ink p-6 text-white">
        <p className="font-mono text-xs text-[#c4a090]">
          {data.symbol} · {data.name}
        </p>
        <p className="mt-3 text-6xl font-bold tabular-nums" style={{ letterSpacing: "-0.04em" }}>
          {data.score === null ? "—" : Math.round(data.score)}
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <VerdictBadge verdict={data.verdict_label} />
          <TrustBadge label={data.trust_label} />
        </div>
        <p className="mt-4 max-w-2xl text-sm leading-relaxed text-[#d0b8a8]">{data.why_sentence}</p>
        <p className="mt-3 font-mono text-xs text-[#7a5040]">{formatWindow(data.window_start_utc)}</p>
      </div>

      <div className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
          <p className="text-sm font-semibold">What the number is saying</p>
          <p className="mt-2 text-sm leading-relaxed text-[#555]">
            {data.verdict_label === "building" && "The conversation is gathering strength rather than fading."}
            {data.verdict_label === "mixed" && "Bullish and cautious threads are both present. Treat this as a split tape, not a clean call."}
            {data.verdict_label === "fading" && "The conversation is losing energy relative to the prior window."}
            {data.verdict_label === "insufficient_data" && "There is not yet enough overlapping coverage to publish a reliable composite."}
          </p>
        </article>
        <article className="rounded-xl bg-[#eef0f6] p-5">
          <p className="text-sm font-semibold text-[#3d4a66]">How much to trust it</p>
          <p className="mt-2 text-sm leading-relaxed text-[#4a5568]">{data.trust_label}</p>
          <p className="mt-2 text-xs leading-relaxed text-[#5c6578]">
            Trust is about whether the conversation looks organic. It is not the same thing as a high or low composite.
          </p>
        </article>
        <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
          <p className="text-sm font-semibold">Sector</p>
          <p className="mt-2 text-sm text-[#555]">{data.sector}</p>
        </article>
      </div>
    </div>
  );
}
