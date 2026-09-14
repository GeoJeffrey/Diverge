import type { ConfidenceFlag, VerdictLabel } from "@/types/api";
import { labelForConfidence, labelForVerdict } from "@/lib/labels";

export function VerdictBadge({ verdict }: { verdict: VerdictLabel }) {
  const styles: Record<VerdictLabel, { bg: string; fg: string }> = {
    building: { bg: "#e7f0e4", fg: "#2d5a34" },
    mixed: { bg: "#f3ead4", fg: "#6a5208" },
    fading: { bg: "#f3e4dc", fg: "#7a2e1a" },
    insufficient_data: { bg: "#eceae6", fg: "#555" },
  };
  const s = styles[verdict];
  return (
    <span className="inline-flex rounded-md px-2.5 py-1 text-xs font-semibold" style={{ background: s.bg, color: s.fg }}>
      {labelForVerdict(verdict)}
    </span>
  );
}

export function TrustBadge({
  flag,
  label,
}: {
  flag?: ConfidenceFlag;
  label?: string;
}) {
  const text = label ?? (flag ? labelForConfidence(flag) : "Trust unread");
  const inferred: ConfidenceFlag | undefined = flag
    ? flag
    : text.toLowerCase().includes("not enough")
      ? "insufficient_data"
      : text.toLowerCase().includes("low")
        ? "low_trust"
        : text.toLowerCase().includes("high")
          ? "high_trust"
          : text.toLowerCase().includes("moderate")
            ? "moderate"
            : undefined;
  const tone = inferred ?? "moderate";
  const styles: Record<string, { bg: string; fg: string }> = {
    high_trust: { bg: "#e4e8f3", fg: "#2f3d5c" },
    moderate: { bg: "#ece8f4", fg: "#4a3d66" },
    low_trust: { bg: "#eadfe8", fg: "#5c2f55" },
    insufficient_data: { bg: "#eceae6", fg: "#555" },
  };
  const s = styles[tone] ?? styles.moderate;
  return (
    <span className="inline-flex rounded-md px-2.5 py-1 text-xs font-semibold" style={{ background: s.bg, color: s.fg }}>
      {text}
    </span>
  );
}
