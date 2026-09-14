import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router";
import { Logo } from "@/components/Logo";
import { useAuth } from "@/auth/AuthProvider";
import { ApiError } from "@/lib/api";

export default function Login() {
  const navigate = useNavigate();
  const [params] = useSearchParams();
  const { login, signup } = useAuth();
  const [tab, setTab] = useState<"login" | "signup">(params.get("tab") === "signup" ? "signup" : "login");
  const [email, setEmail] = useState("trader@example.com");
  const [password, setPassword] = useState("SecurePass123!");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [pending, setPending] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setPending(true);
    try {
      if (tab === "signup") {
        await signup(email, password, fullName);
      } else {
        await login(email, password);
      }
      const next = params.get("next") || "/tickers";
      navigate(next.startsWith("/") ? next : "/tickers", { replace: true });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Something went wrong.");
    } finally {
      setPending(false);
    }
  }

  return (
    <div id="main" className="flex min-h-full bg-canvas">
      <div className="hidden w-[480px] flex-shrink-0 flex-col justify-between bg-ink p-12 lg:flex">
        <Logo light size={32} />
        <div>
          <div className="mb-10 flex gap-3" aria-hidden>
            <div className="h-16 w-16 rounded bg-terracotta" />
            <div className="h-16 w-16 rounded bg-amber" />
            <div className="h-16 w-8 rounded bg-crimson" />
          </div>
          <h2 className="mb-4 text-3xl font-bold leading-tight text-white" style={{ letterSpacing: "-0.03em" }}>
            Narrative readings<br />for listed names.
          </h2>
          <p className="text-sm leading-relaxed text-[#a87860]">
            Simple language when you want a verdict. Full index cards, trust, and a “Why this score” trail when you need the audit.
          </p>
        </div>
        <p className="text-xs text-[#4a2810]">Demo account: trader@example.com</p>
      </div>

      <div className="flex flex-1 items-center justify-center p-6 md:p-8">
        <div className="w-full max-w-[420px]">
          <div className="mb-8 lg:hidden">
            <Logo />
          </div>
          <h1 className="text-2xl font-bold" style={{ letterSpacing: "-0.03em" }}>
            {tab === "login" ? "Welcome back" : "Create your account"}
          </h1>
          <p className="mb-7 text-sm text-[#6b6b6b]">
            {tab === "login" ? "Sign in to your Diverge workspace." : "Start with Simple or Advanced on any tracked ticker."}
          </p>

          <div className="mb-7 flex rounded-lg bg-[#e8e3dc] p-1" role="tablist">
            {(["login", "signup"] as const).map((t) => (
              <button
                key={t}
                type="button"
                role="tab"
                aria-selected={tab === t}
                onClick={() => setTab(t)}
                className="flex-1 rounded-md py-2 text-sm font-semibold"
                style={{
                  background: tab === t ? "#fff" : "transparent",
                  color: tab === t ? "#1a0f0a" : "#777",
                  boxShadow: tab === t ? "0 1px 4px rgba(0,0,0,0.08)" : "none",
                }}
              >
                {t === "login" ? "Log in" : "Sign up"}
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {tab === "signup" && (
              <div>
                <label className="mb-1.5 block text-sm font-medium text-[#444]" htmlFor="full_name">
                  Full name
                </label>
                <input
                  id="full_name"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="w-full rounded-lg border-[1.5px] border-[#e0dbd4] bg-white px-4 py-3 text-sm"
                />
              </div>
            )}
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#444]" htmlFor="email">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-lg border-[1.5px] border-[#e0dbd4] bg-white px-4 py-3 text-sm"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-[#444]" htmlFor="password">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-lg border-[1.5px] border-[#e0dbd4] bg-white px-4 py-3 text-sm"
              />
            </div>
            {error && (
              <p className="rounded-lg bg-[#faf3ef] px-3 py-2 text-sm text-[#7a2e1a]" role="alert">
                {error}
              </p>
            )}
            <button
              type="submit"
              disabled={pending}
              className="mt-1 rounded-lg bg-ink py-3 text-sm font-bold text-white disabled:opacity-50"
            >
              {pending ? "Working…" : tab === "login" ? "Sign in" : "Create account"}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
