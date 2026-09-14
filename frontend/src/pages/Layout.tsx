import { NavLink, Outlet, useLocation, useNavigate, useParams } from "react-router";
import { useEffect, useState } from "react";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/auth/AuthProvider";
import { labelForRole } from "@/lib/labels";
import { api } from "@/lib/api";

const NAV = [
  { label: "Overview", to: (s: string) => `/ticker/${s}` },
  { label: "Tickers", to: () => "/tickers" },
  { label: "Indices", to: (s: string) => `/indices?symbol=${s}` },
  { label: "Integrity", to: (s: string) => `/integrity?symbol=${s}` },
  { label: "Why this score", to: (s: string) => `/explainability?symbol=${s}` },
  { label: "Settings", to: () => "/settings" },
];

export interface ShellContext {
  symbol: string;
  setSymbol: (s: string) => void;
  symbols: string[];
}

export default function Layout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const params = useParams();
  const [symbols, setSymbols] = useState<string[]>(["TATASTEEL", "RELIANCE", "INFY", "TCS", "HDFCBANK"]);
  const [symbol, setSymbol] = useState((params.symbol ?? "TATASTEEL").toUpperCase());
  const [menuOpen, setMenuOpen] = useState(false);
  const [query, setQuery] = useState("");

  useEffect(() => {
    if (params.symbol) setSymbol(params.symbol.toUpperCase());
  }, [params.symbol]);

  useEffect(() => {
    void api.tickers().then((res) => {
      setSymbols(res.tickers.map((t) => t.symbol));
    });
  }, []);

  const isSimple = location.pathname.endsWith("/simple");
  const onTickerView = location.pathname.startsWith("/ticker/");

  function pickSymbol(next: string) {
    setSymbol(next);
    if (onTickerView) {
      navigate(isSimple ? `/ticker/${next}/simple` : `/ticker/${next}`);
    }
  }

  const initials = (user?.full_name ?? "U")
    .split(" ")
    .map((p) => p[0])
    .slice(0, 2)
    .join("")
    .toUpperCase();

  return (
    <div className="flex h-full min-h-0 flex-col md:flex-row" style={{ background: "#f0ede8" }}>
      <header className="flex items-center justify-between bg-ink px-4 py-3 md:hidden">
        <Logo light />
        <button
          type="button"
          className="rounded-md px-3 py-2 text-sm text-[#c4a090]"
          aria-expanded={menuOpen}
          onClick={() => setMenuOpen((v) => !v)}
        >
          Menu
        </button>
      </header>

      <aside
        className={`${menuOpen ? "flex" : "hidden"} md:flex w-full flex-col md:h-full md:w-[220px] md:flex-shrink-0`}
        style={{ background: "#1a0f0a" }}
      >
        <div className="hidden px-6 pb-6 pt-7 md:block">
          <Logo light />
          <p className="mt-1.5 font-mono text-xs text-[#7a5040]">Narrative intelligence</p>
        </div>

        <div className="mb-4 px-4">
          <div className="rounded p-2" style={{ background: "#2a1510" }}>
            <p className="mb-2 text-xs text-[#7a5040]">Active ticker</p>
            <label className="sr-only" htmlFor="ticker-select">
              Active ticker
            </label>
            <select
              id="ticker-select"
              value={symbol}
              onChange={(e) => pickSymbol(e.target.value)}
              className="w-full rounded border-0 px-2 py-1 text-sm font-semibold text-white outline-none"
              style={{ background: "#3a1e14" }}
            >
              {symbols.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
        </div>

        <nav className="flex-1 px-3" aria-label="Primary">
          {NAV.map((item) => {
            const to = item.to(symbol);
            return (
              <NavLink
                key={item.label}
                to={to}
                onClick={() => setMenuOpen(false)}
                className={({ isActive }) =>
                  `mb-0.5 block w-full rounded px-3 py-2.5 text-left text-sm font-medium ${
                    isActive ? "text-white" : "text-[#a87860]"
                  }`
                }
                style={({ isActive }) => ({ background: isActive ? "#c4510b" : "transparent" })}
                end={item.label === "Overview"}
              >
                {item.label}
              </NavLink>
            );
          })}
        </nav>

        <div className="px-3 pb-6">
          <div className="mb-4 h-px w-full" style={{ background: "#2a1510" }} />
          {user ? (
            <>
              <div className="mb-2 flex items-center gap-2 px-3">
                <div className="flex h-6 w-6 items-center justify-center rounded text-xs font-bold text-white" style={{ background: "#c4510b" }}>
                  {initials}
                </div>
                <div>
                  <p className="text-xs font-semibold text-[#d0b8a8]">{user.full_name}</p>
                  <p className="text-[10px] text-[#7a5040]">{labelForRole(user.role)}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => {
                  logout();
                  navigate("/");
                }}
                className="w-full rounded px-3 py-2 text-left text-sm text-[#7a5040]"
              >
                Log out
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => navigate("/login")}
              className="w-full rounded px-3 py-2 text-left text-sm text-[#c4a090]"
            >
              Log in
            </button>
          )}
        </div>
      </aside>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <header
          className="flex h-16 flex-shrink-0 items-center gap-4 border-b border-[#e0dbd4] px-4 md:px-7"
          style={{ background: "#f0ede8" }}
        >
          <h1 className="flex-1 text-lg font-bold md:text-xl" style={{ letterSpacing: "-0.02em" }}>
            {isSimple
              ? "Simple"
              : NAV.find((n) => {
                  const base = n.to(symbol).split("?")[0];
                  if (n.label === "Overview") return /^\/ticker\/[^/]+$/.test(location.pathname);
                  return location.pathname === base;
                })?.label ?? "Dashboard"}
          </h1>
          {onTickerView && (
            <>
              <form
                className="relative hidden w-[280px] md:block"
                onSubmit={(e) => {
                  e.preventDefault();
                  const hit = symbols.find((s) => s.includes(query.toUpperCase()));
                  if (hit) pickSymbol(hit);
                }}
              >
                <label className="sr-only" htmlFor="ticker-search">
                  Search ticker
                </label>
                <input
                  id="ticker-search"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  placeholder="Search ticker, e.g. RELIANCE"
                  className="w-full rounded-lg border border-[#d8d3cc] bg-[#e8e3dc] py-2 pl-3 pr-4 text-sm outline-none"
                />
              </form>
              <div className="flex rounded-full bg-[#e0dbd4] p-0.5" role="tablist" aria-label="View mode">
                {(["Simple", "Advanced"] as const).map((m) => {
                  const active = m === "Simple" ? isSimple : !isSimple;
                  return (
                    <button
                      key={m}
                      type="button"
                      role="tab"
                      aria-selected={active}
                      onClick={() => navigate(m === "Simple" ? `/ticker/${symbol}/simple` : `/ticker/${symbol}`)}
                      className="rounded-full px-4 py-1.5 text-sm font-semibold"
                      style={{ background: active ? "#1a0f0a" : "transparent", color: active ? "#fff" : "#666" }}
                    >
                      {m}
                    </button>
                  );
                })}
              </div>
            </>
          )}
        </header>
        <main id="main" className="min-h-0 flex-1 overflow-y-auto">
          <Outlet context={{ symbol, setSymbol: pickSymbol, symbols } satisfies ShellContext} />
        </main>
      </div>
    </div>
  );
}
