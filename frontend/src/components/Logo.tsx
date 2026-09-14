export function Logo({ light = false, size = 28 }: { light?: boolean; size?: number }) {
  return (
    <div className="flex items-center gap-2">
      <div
        className="flex items-center justify-center rounded"
        style={{ width: size, height: size, background: "#c4510b" }}
        aria-hidden
      >
        <svg width={size * 0.55} height={size * 0.55} viewBox="0 0 14 14" fill="none">
          <path d="M2 12L7 2L12 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          <path d="M4 9H10" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
        </svg>
      </div>
      <span className={`font-bold ${light ? "text-white" : "text-ink"}`} style={{ letterSpacing: "-0.02em" }}>
        Diverge
      </span>
    </div>
  );
}
