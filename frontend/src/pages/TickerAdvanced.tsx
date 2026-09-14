import { useEffect, useState } from "react";
import { Link, useOutletContext, useParams } from "react-router";
import { api, ApiError } from "@/lib/api";
import { INDEX_ACCENTS, formatRiskFlag, formatWindow, labelForIndexKey, labelForMutation } from "@/lib/labels";
import { CoverageNote, IndexCard } from "@/components/IndexCard";
import { TrustBadge, VerdictBadge } from "@/components/TrustBadge";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { IndexKey, TickerAdvancedResponse, TickerSimpleResponse } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

const INDEX_ORDER: IndexKey[] = ["rn", "cirg", "cli", "cassi", "vdi"];

export default function TickerAdvanced() {
  const { symbol: routeSymbol } = useParams();
  const { symbol: ctxSymbol, setSymbol } = useOutletContext<ShellContext>();
  const symbol = (routeSymbol ?? ctxSymbol).toUpperCase();
  const [detail, setDetail] = useState<TickerAdvancedResponse | null>(null);
  const [simple, setSimple] = useState<TickerSimpleResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [adv, smp] = await Promise.all([api.ticker(symbol), api.tickerSimple(symbol)]);
      setDetail(adv);
      setSimple(smp);
      setSymbol(symbol);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load ticker detail.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [symbol]);

  if (loading) return <LoadingState label="Loading advanced reading…" />;
  if (error || !detail) return <ErrorState message={error ?? "Missing ticker."} onRetry={() => void load()} />;

  const coord = detail.coordination;

  return (
    <div className="px-4 py-5 md:px-7">
      <div className="mb-5 flex flex-col gap-4 rounded-xl bg-ink p-5 text-white md:flex-row md:items-end md:justify-between">
        <div>
          <p className="font-mono text-xs text-[#c4a090]">{detail.symbol}</p>
          <h2 className="text-2xl font-bold" style={{ letterSpacing: "-0.02em" }}>
            {detail.name}
          </h2>
          <p className="mt-1 text-sm text-[#a87860]">{detail.sector}</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          {simple && <VerdictBadge verdict={simple.verdict_label} />}
          <p className="text-4xl font-bold tabular-nums">
            {detail.composite_score === null ? "—" : detail.composite_score.toFixed(1)}
          </p>
        </div>
      </div>

      <div className="mb-5 grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
          <p className="text-sm text-[#6b6b6b]">Composite</p>
          <p className="mt-1 text-3xl font-bold tabular-nums">
            {detail.composite_score === null ? "—" : detail.composite_score.toFixed(1)}
          </p>
          <p className="mt-2 text-xs text-[#6b6b6b]">{formatWindow(detail.window_start_utc)}</p>
        </article>
        <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
          <p className="text-sm text-[#6b6b6b]">Leading narrative driver</p>
          <p className="mt-1 text-xl font-bold">{labelForIndexKey(detail.dominant_index)}</p>
        </article>
        <article className="rounded-xl bg-[#eef0f6] p-5">
          <p className="text-sm text-[#3d4a66]">Trust Score</p>
          {coord.available ? (
            <>
              <p className="mt-1 text-3xl font-bold tabular-nums text-[#3d4a66]">{coord.coordination_score.toFixed(1)}</p>
              <div className="mt-2">
                <TrustBadge flag={coord.confidence_flag} />
              </div>
              <p className="mt-2 text-xs leading-relaxed text-[#4a5568]">
                Higher values mean the conversation looks more coordinated. This is not a bullish/bearish scale.
              </p>
            </>
          ) : (
            <div className="mt-3">
              <CoverageNote label={coord.label} coverageNote={coord.coverage_note} />
            </div>
          )}
        </article>
      </div>

      <h3 className="mb-3 text-base font-bold">Index cards</h3>
      <div className="mb-6 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
        {INDEX_ORDER.map((key) => (
          <IndexCard key={key} metric={detail.indices[key]} accent={INDEX_ACCENTS[key]} />
        ))}
      </div>

      {detail.risk_flags.length > 0 && (
        <div className="mb-6">
          <h3 className="mb-2 text-base font-bold">Risk flags</h3>
          <div className="flex flex-wrap gap-2">
            {detail.risk_flags.map((flag) => (
              <span key={flag} className="rounded-md bg-[#f3e4dc] px-2.5 py-1 text-xs font-semibold text-[#7a2e1a]">
                {formatRiskFlag(flag)}
              </span>
            ))}
          </div>
        </div>
      )}

      <div className="mb-6 rounded-xl border border-[#e7e1d8] bg-white p-5">
        <div className="mb-3 flex items-center justify-between gap-3">
          <h3 className="font-bold">Recent narrative transitions</h3>
          <Link className="text-sm font-semibold text-terracotta" to={`/explainability?symbol=${symbol}`}>
            Open Why this score
          </Link>
        </div>
        {detail.phylogeny_context.length === 0 ? (
          <p className="text-sm text-[#6b6b6b]">No transition history in this window yet.</p>
        ) : (
          <ol className="space-y-3">
            {detail.phylogeny_context.map((item) => (
              <li key={item.window_start_utc} className="flex flex-col gap-1 border-t border-[#f0ede8] pt-3 first:border-0 first:pt-0 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-sm font-semibold">{labelForMutation(item.mutation_type)}</p>
                  <p className="font-mono text-xs text-[#6b6b6b]">{formatWindow(item.window_start_utc)}</p>
                </div>
                <p className="text-sm tabular-nums text-[#555]">
                  {item.composite_delta === null
                    ? "No composite change"
                    : `${item.composite_delta > 0 ? "+" : ""}${item.composite_delta.toFixed(1)} composite`}
                </p>
              </li>
            ))}
          </ol>
        )}
      </div>
    </div>
  );
}
