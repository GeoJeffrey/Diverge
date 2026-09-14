import { useEffect, useMemo, useState } from "react";
import { useOutletContext, useSearchParams } from "react-router";
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from "recharts";
import { api, ApiError } from "@/lib/api";
import { INDEX_ACCENTS, INDEX_LABELS } from "@/lib/labels";
import { IndexCard } from "@/components/IndexCard";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { IndexKey, TickerAdvancedResponse } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

const KEYS: IndexKey[] = ["rn", "cirg", "cli", "cassi", "vdi"];

export default function IndicesPage() {
  const { symbol, symbols, setSymbol } = useOutletContext<ShellContext>();
  const [params] = useSearchParams();
  const active = (params.get("symbol") ?? symbol).toUpperCase();
  const compare = symbols.find((s) => s !== active) ?? active;
  const [primary, setPrimary] = useState<TickerAdvancedResponse | null>(null);
  const [secondary, setSecondary] = useState<TickerAdvancedResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const [a, b] = await Promise.all([api.ticker(active), api.ticker(compare)]);
      setPrimary(a);
      setSecondary(b);
      setSymbol(active);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load indices.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active, compare]);

  const radar = useMemo(() => {
    if (!primary || !secondary) return [];
    return KEYS.map((key) => ({
      label: INDEX_LABELS[key],
      [primary.symbol]: primary.indices[key].available ? (primary.indices[key].score ?? 0) : 0,
      [secondary.symbol]: secondary.indices[key].available ? (secondary.indices[key].score ?? 0) : 0,
    }));
  }, [primary, secondary]);

  if (loading) return <LoadingState label="Loading index cards…" />;
  if (error || !primary) return <ErrorState message={error ?? "Missing data."} onRetry={() => void load()} />;

  return (
    <div className="px-4 py-5 md:px-7">
      <h2 className="text-lg font-bold">Index cards · {primary.symbol}</h2>
      <p className="mb-5 text-sm text-[#6b6b6b]">
        Narrative-strength readings only. Unavailable indices show a coverage note instead of a blank.
      </p>

      <div className="mb-5 grid gap-4 lg:grid-cols-2">
        <div className="rounded-xl border border-[#e7e1d8] bg-white p-5">
          <h3 className="mb-1 font-bold">
            {primary.symbol} vs {secondary?.symbol}
          </h3>
          <p className="mb-4 text-xs text-[#6b6b6b]">Published scores only; missing values plot as zero and are called out in the cards.</p>
          <ResponsiveContainer width="100%" height={280}>
            <RadarChart data={radar}>
              <PolarGrid stroke="#e7e1d8" />
              <PolarAngleAxis dataKey="label" tick={{ fontSize: 10, fill: "#555" }} />
              <Radar dataKey={primary.symbol} stroke="#c4510b" fill="#c4510b" fillOpacity={0.12} strokeWidth={2} />
              {secondary && (
                <Radar dataKey={secondary.symbol} stroke="#3a6ea8" fill="#3a6ea8" fillOpacity={0.08} strokeWidth={2} />
              )}
              <Tooltip />
            </RadarChart>
          </ResponsiveContainer>
        </div>
        <div className="grid gap-3">
          {KEYS.map((key) => (
            <IndexCard key={key} metric={primary.indices[key]} accent={INDEX_ACCENTS[key]} />
          ))}
        </div>
      </div>
    </div>
  );
}
