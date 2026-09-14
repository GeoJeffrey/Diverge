import { useNavigate } from "react-router";
import { useEffect, useRef, useState } from "react";
import { Logo } from "@/components/Logo";

const TAPE = [
  { name: "TATASTEEL", score: 67, change: "+4.2" },
  { name: "RELIANCE", score: 74, change: "+2.8" },
  { name: "INFY", score: 42, change: "−3.1" },
  { name: "TCS", score: 61, change: "+1.5" },
  { name: "HDFCBANK", score: 38, change: "−5.0" },
  { name: "WIPRO", score: 55, change: "+0.9" },
  { name: "ONGC", score: 71, change: "+3.3" },
  { name: "BAJFINANCE", score: 48, change: "−1.8" },
];

const FEATURES = [
  {
    title: "Five narrative readings",
    desc: "Contagion Core, Reality Check, Capitulation Signal, Cross-Market Spillover, and Language Divergence — each with an explicit coverage state when a number cannot yet be computed.",
    color: "#c4510b",
  },
  {
    title: "Source coverage",
    desc: "Reddit, StockTwits, Telegram, filings, and search interest are parsed into windows so you can see what the conversation is doing before the tape reacts.",
    color: "#d4970f",
  },
  {
    title: "Trust, not a second score",
    desc: "Trust Score sits on a separate visual language from narrative strength. It tells you whether the conversation looks coordinated — not whether it is bullish.",
    color: "#3d4a66",
  },
  {
    title: "Why this score",
    desc: "Every advanced view includes an audit trail of source posts, grouped by driver: virality onset, cross-market sentiment, vernacular, capitulation, duplicates, and consensus outliers.",
    color: "#3d6b45",
  },
  {
    title: "Two reading modes",
    desc: "Simple mode is a plain-language summary. Advanced mode is the full card set — scores, confidence, and reasoning — on the same ticker.",
    color: "#3a6ea8",
  },
  {
    title: "Contract-stable API",
    desc: "The dashboard is built against a frozen OpenAPI shape, so swapping the mock layer for a live backend is a single environment change.",
    color: "#5a3d7a",
  },
];

function Stat({ target, suffix, label, start }: { target: number; suffix: string; label: string; start: boolean }) {
  const [val, setVal] = useState(0);
  useEffect(() => {
    if (!start) return;
    let t0: number | null = null;
    const step = (ts: number) => {
      if (!t0) t0 = ts;
      const p = Math.min((ts - t0) / 1400, 1);
      setVal(Math.floor(p * target));
      if (p < 1) requestAnimationFrame(step);
    };
    requestAnimationFrame(step);
  }, [start, target]);
  return (
    <div className="text-center">
      <p className="text-4xl font-bold tabular-nums text-white md:text-5xl">
        {val.toLocaleString()}
        {suffix}
      </p>
      <p className="mt-2 text-sm text-[#f5cdb0]">{label}</p>
    </div>
  );
}

export default function Landing() {
  const navigate = useNavigate();
  const statsRef = useRef<HTMLDivElement>(null);
  const [statsVisible, setStatsVisible] = useState(false);

  useEffect(() => {
    const el = statsRef.current;
    if (!el) return;
    const obs = new IntersectionObserver(([e]) => {
      if (e.isIntersecting) setStatsVisible(true);
    }, { threshold: 0.3 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  const items = [...TAPE, ...TAPE];

  return (
    <div id="main" className="min-h-full bg-canvas">
      <nav className="sticky top-0 z-40 flex items-center justify-between border-b border-[#2a1510] bg-ink px-4 py-4 md:px-8">
        <Logo light />
        <div className="hidden items-center gap-8 md:flex">
          <a href="#features" className="text-sm text-[#a87860] hover:text-white">Features</a>
          <a href="#how-it-works" className="text-sm text-[#a87860] hover:text-white">How it works</a>
        </div>
        <div className="flex items-center gap-2">
          <button type="button" onClick={() => navigate("/login")} className="rounded-lg px-3 py-2 text-sm font-semibold text-[#a87860]">
            Log in
          </button>
          <button type="button" onClick={() => navigate("/login?tab=signup")} className="rounded-lg bg-terracotta px-4 py-2 text-sm font-bold text-white">
            Create account
          </button>
        </div>
      </nav>

      <div className="overflow-hidden bg-ink" aria-hidden>
        <div className="flex w-max gap-8 px-4 py-2" style={{ animation: "marquee 28s linear infinite" }}>
          {items.map((t, i) => (
            <div key={i} className="flex flex-shrink-0 items-center gap-2">
              <span className="font-mono text-xs font-bold text-[#c4a090]">{t.name}</span>
              <span className="text-xs font-bold text-white">{t.score}</span>
              <span className="text-xs" style={{ color: t.change.startsWith("+") ? "#7aad72" : "#e08a5a" }}>
                {t.change}
              </span>
            </div>
          ))}
        </div>
      </div>

      <section className="bg-ink px-6 pb-20 pt-20 text-center">
        <p className="mx-auto mb-8 inline-flex items-center gap-2 rounded-full border border-[#3a2010] bg-[#2a1510] px-3 py-1.5 text-xs text-[#c4a090]">
          Live coverage · NSE and BSE names
        </p>
        <h1 className="mx-auto max-w-3xl text-4xl font-bold leading-tight text-white md:text-6xl" style={{ letterSpacing: "-0.04em" }}>
          Narrative that moves <span className="text-terracotta">before the price does.</span>
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-base leading-relaxed text-[#a87860] md:text-lg">
          Diverge turns market conversation into readable verdicts for everyone, and full index cards for people who need the audit trail.
        </p>
        <div className="mt-10 flex flex-wrap justify-center gap-3">
          <button type="button" onClick={() => navigate("/login?tab=signup")} className="rounded-xl bg-terracotta px-7 py-3.5 text-sm font-bold text-white">
            Start with an account
          </button>
          <button type="button" onClick={() => navigate("/login")} className="rounded-xl border border-[#3a2010] bg-[#2a1510] px-7 py-3.5 text-sm font-bold text-[#c4a090]">
            Log in to the dashboard
          </button>
        </div>
      </section>

      <section ref={statsRef} className="bg-terracotta px-6 py-16">
        <div className="mx-auto grid max-w-4xl grid-cols-2 gap-8 md:grid-cols-4">
          <Stat target={16} suffix="" label="Tracked names" start={statsVisible} />
          <Stat target={5} suffix="" label="Narrative readings" start={statsVisible} />
          <Stat target={2} suffix="" label="Reading modes" start={statsVisible} />
          <Stat target={6} suffix="" label="Evidence categories" start={statsVisible} />
        </div>
      </section>

      <section id="features" className="px-6 py-20">
        <div className="mx-auto max-w-5xl">
          <h2 className="text-center text-3xl font-bold md:text-4xl" style={{ letterSpacing: "-0.03em" }}>
            Built for two kinds of readers
          </h2>
          <div className="mt-12 grid grid-cols-1 gap-5 md:grid-cols-3">
            {FEATURES.map((f) => (
              <article key={f.title} className="rounded-xl border border-[#e7e1d8] bg-white p-6">
                <div className="mb-4 h-1.5 w-10 rounded" style={{ background: f.color }} />
                <h3 className="mb-2 text-base font-bold">{f.title}</h3>
                <p className="text-sm leading-relaxed text-[#5c5c5c]">{f.desc}</p>
              </article>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="bg-ink px-6 py-20">
        <div className="mx-auto max-w-2xl">
          <h2 className="mb-12 text-center text-3xl font-bold text-white">From posts to a published reading</h2>
          <ol className="space-y-8">
            {[
              { n: "01", title: "Ingest", desc: "Posts and filings land in a window. Nothing is shown as a score until coverage rules are met." },
              { n: "02", title: "Read", desc: "Each index either publishes a number or an explicit coverage note — never a blank card." },
              { n: "03", title: "Judge trust separately", desc: "Coordination and duplication inform Trust Score, kept visually distinct from narrative strength." },
              { n: "04", title: "Explain", desc: "Why this score groups source evidence so you can audit the reading, not just consume it." },
            ].map((s) => (
              <li key={s.n} className="flex gap-5">
                <span className="font-mono text-sm text-terracotta">{s.n}</span>
                <div>
                  <h3 className="font-bold text-white">{s.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-[#a87860]">{s.desc}</p>
                </div>
              </li>
            ))}
          </ol>
        </div>
      </section>

      <section className="bg-terracotta px-6 py-20 text-center">
        <h2 className="text-3xl font-bold text-white">The market is talking. Read it clearly.</h2>
        <button type="button" onClick={() => navigate("/login?tab=signup")} className="mt-8 rounded-xl bg-ink px-8 py-4 text-sm font-bold text-white">
          Create your account
        </button>
      </section>

      <footer className="border-t border-[#2a1510] bg-ink px-8 py-10">
        <div className="mx-auto flex max-w-5xl flex-col justify-between gap-6 md:flex-row">
          <div>
            <Logo light />
            <p className="mt-3 max-w-xs text-xs leading-relaxed text-[#7a5040]">
              Narrative analysis for listed names. Not investment advice.
            </p>
          </div>
          <p className="text-xs text-[#4a2810]">© 2026 Diverge</p>
        </div>
      </footer>
    </div>
  );
}
