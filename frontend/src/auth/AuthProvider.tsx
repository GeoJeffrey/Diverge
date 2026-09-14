import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { api } from "@/lib/api";
import { sessionStore } from "@/lib/session";
import type { UserProfileResponse } from "@/types/api";

interface AuthContextValue {
  user: UserProfileResponse | null;
  loading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<UserProfileResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function boot() {
      if (!sessionStore.isAuthenticated()) {
        setLoading(false);
        return;
      }
      try {
        const me = await api.me();
        if (!cancelled) setUser(me);
      } catch {
        sessionStore.clear();
        if (!cancelled) setUser(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    void boot();
    return () => {
      cancelled = true;
    };
  }, []);

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      loading,
      isAuthenticated: Boolean(user),
      login: async (email, password) => {
        const tokens = await api.login(email, password);
        sessionStore.setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
        setUser(await api.me());
      },
      signup: async (email, password, fullName) => {
        const tokens = await api.signup(email, password, fullName);
        sessionStore.setTokens(tokens.access_token, tokens.refresh_token, tokens.expires_in);
        setUser(await api.me());
      },
      logout: () => {
        sessionStore.clear();
        setUser(null);
      },
    }),
    [user, loading],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
