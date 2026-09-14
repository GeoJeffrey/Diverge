import type { IndexMetricValue } from "@/types/api";

export function CoverageNote({
  label,
  coverageNote,
}: {
  label: string;
  coverageNote: string | null;
}) {
  return (
    <div
      className="rounded-xl border border-dashed border-[#c9b8a4] bg-[#f8f4ee] p-4"
      role="status"
    >
      <p className="text-sm font-semibold text-ink">
        {label}: not yet computable
        {coverageNote ? ` — ${coverageNote}` : " — This reading needs more overlapping coverage before it can be published."}
      </p>
    </div>
  );
}

export function IndexCard({
  metric,
  accent,
}: {
  metric: IndexMetricValue;
  accent: string;
}) {
  if (!metric.available) {
    return <CoverageNote label={metric.label} coverageNote={metric.coverage_note} />;
  }

  return (
    <article className="rounded-xl border border-[#e7e1d8] bg-white p-4">
      <p className="text-sm font-semibold text-ink">{metric.label}</p>
      <p className="mt-2 text-3xl font-bold tabular-nums" style={{ color: accent }}>
        {metric.score?.toFixed(2)}
      </p>
      <p className="mt-1 text-xs text-[#6b6b6b]">Narrative-strength reading</p>
    </article>
  );
}
