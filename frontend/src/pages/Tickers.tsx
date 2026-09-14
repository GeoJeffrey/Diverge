import { useEffect, useState } from "react";
import { useNavigate, useOutletContext } from "react-router";
import { api, ApiError } from "@/lib/api";
import { formatWindow } from "@/lib/labels";
import { TrustBadge, VerdictBadge } from "@/components/TrustBadge";
import { ErrorState, LoadingState } from "@/components/StatusStates";
import type { TickerSimpleItem } from "@/types/api";
import type { ShellContext } from "@/pages/Layout";

export default function TickersPage() {
  const { setSymbol } = useOutletContext<ShellContext>();
  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [rows, setRows] = useState<TickerSimpleItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const res = await api.tickers();
      setRows(res.tickers);
    } catch (e) {
      setError(e instanceof ApiError ? e.message : "Could not load tickers.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  if (loading) return <LoadingState label="Loading tracked names…" />;
  if (error) return <ErrorState message={error} onRetry={() => void load()} />;

  const filtered = rows.filter(
    (t) =>
      t.symbol.toLowerCase().includes(query.toLowerCase()) ||
      t.name.toLowerCase().includes(query.toLowerCase()) ||
      t.sector.toLowerCase().includes(query.toLowerCase()),
  );

  return (
    <div className="px-4 py-5 md:px-7">
      <div className="mb-5 flex flex-col gap-3 md:flex-row md:items-end md:justify-between">
        <div>
          <h2 className="text-lg font-bold" style={{ letterSpacing: "-0.02em" }}>
            Tracked tickers
          </h2>
          <p className="text-sm text-[#6b6b6b]">{rows.length} names with a published window</p>
        </div>
        <label className="sr-only" htmlFor="filter-tickers">
          Filter tickers
        </label>
        <input
          id="filter-tickers"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Filter by name, symbol, or sector"
          className="w-full rounded-lg border-[1.5px] border-[#e0dbd4] bg-white px-4 py-2 text-sm md:w-72"
        />
      </div>

      <div className="overflow-x-auto rounded-xl border border-[#e7e1d8] bg-white">
        <table className="min-w-[720px] w-full text-left">
          <thead>
            <tr className="border-b border-[#f0ede8] text-xs text-[#6b6b6b]">
              <th className="px-5 py-3 font-semibold">Ticker</th>
              <th className="px-5 py-3 font-semibold">Sector</th>
              <th className="px-5 py-3 font-semibold">Composite</th>
              <th className="px-5 py-3 font-semibold">Verdict</th>
              <th className="px-5 py-3 font-semibold">Trust</th>
              <th className="px-5 py-3 font-semibold">Window</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((t) => (
              <tr
                key={t.symbol}
                className="cursor-pointer border-t border-[#f0ede8] hover:bg-[#faf7f2]"
                onClick={() => {
                  setSymbol(t.symbol);
                  navigate(`/ticker/${t.symbol}`);
                }}
              >
                <td className="px-5 py-4">
                  <p className="font-mono text-sm font-bold">{t.symbol}</p>
                  <p className="text-xs text-[#6b6b6b]">{t.name}</p>
                </td>
                <td className="px-5 py-4 text-sm text-[#555]">{t.sector}</td>
                <td className="px-5 py-4 font-bold tabular-nums">
                  {t.score === null ? "—" : t.score.toFixed(1)}
                </td>
                <td className="px-5 py-4">
                  <VerdictBadge verdict={t.verdict_label} />
                </td>
                <td className="px-5 py-4">
                  <TrustBadge label={t.trust_label} />
                </td>
                <td className="px-5 py-4 font-mono text-xs text-[#6b6b6b]">{formatWindow(t.window_start_utc)}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {filtered.length === 0 && (
          <p className="px-5 py-8 text-sm text-[#6b6b6b]">No tickers match that filter.</p>
        )}
      </div>
    </div>
  );
}
