import { useEffect, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router";
import { api, ApiError } from "@/lib/api";
import { TrustBadge } from "@/components/TrustBadge";
import { CoverageNote } from "@/components/IndexCard";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { TickerAdvancedResponse } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

export default function IntegrityPage() {
  const { symbol, setSymbol } = useOutletContext<ShellContext>();
  const [params] = useSearchParams();
  const active = (params.get("symbol") ?? symbol).toUpperCase();
  const [detail, setDetail] = useState<TickerAdvancedResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.ticker(active);
      setDetail(res);
      setSymbol(active);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load trust reading.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  if (loading) return <LoadingState label="Loading trust reading…" />;
  if (error || !detail) return <ErrorState message={error ?? "Missing data."} onRetry={() => void load()} />;

  const coord = detail.coordination;

  return (
    <div className="px-4 py-5 md:px-7">
      <h2 className="text-lg font-bold">Integrity · {detail.symbol}</h2>
      <p className="mb-5 text-sm text-[#6b6b6b]">
        Trust Score is a coordination reading. It is not a red-to-green narrative scale.
      </p>

      {coord.available ? (
        <div className="mb-5 grid gap-4 md:grid-cols-3">
          <article className="rounded-xl bg-[#eef0f6] p-5">
            <p className="text-sm text-[#3d4a66]">{coord.label}</p>
            <p className="mt-2 text-4xl font-bold tabular-nums text-[#3d4a66]">{coord.coordination_score.toFixed(1)}</p>
            <p className="mt-2 text-xs text-[#4a5568]">0–100 · higher means more coordinated posting</p>
          </article>
          <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
            <p className="text-sm text-[#6b6b6b]">Confidence</p>
            <div className="mt-3">
              <TrustBadge flag={coord.confidence_flag} />
            </div>
          </article>
          <article className="rounded-xl border border-[#e7e1d8] bg-white p-5">
            <p className="text-sm text-[#6b6b6b]">Aggregation confidence</p>
            <div className="mt-3">
              <TrustBadge flag={detail.aggregation_confidence} />
            </div>
          </article>
        </div>
      ) : (
        <div className="mb-5">
          <CoverageNote label={coord.label} coverageNote={coord.coverage_note} />
        </div>
      )}

      <div className="rounded-xl border border-[#e7e1d8] bg-white p-5">
        <h3 className="mb-3 font-bold">How to read this</h3>
        <div className="grid gap-4 md:grid-cols-3">
          <p className="text-sm leading-relaxed text-[#555]">
            Coordination looks at whether many accounts are saying the same thing at the same time.
          </p>
          <p className="text-sm leading-relaxed text-[#555]">
            Near-duplicates show up in Why this score under their own evidence group, not as a second composite.
          </p>
          <p className="text-sm leading-relaxed text-[#555]">
            A high Trust Score suspicion does not mean “sell.” It means “this conversation may not be organic.”
          </p>
        </div>
      </div>
    </div>
  );
}
