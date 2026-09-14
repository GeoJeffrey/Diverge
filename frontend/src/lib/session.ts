const ACCESS_KEY = "diverge.session.access";
const REFRESH_KEY = "diverge.session.refresh";
const EXPIRY_KEY = "diverge.session.expiry";

/** Session storage only — schema uses Bearer JWTs, not localStorage. */
export const sessionStore = {
  getAccessToken(): string | null {
    return sessionStorage.getItem(ACCESS_KEY);
  },
  getRefreshToken(): string | null {
    return sessionStorage.getItem(REFRESH_KEY);
  },
  isAuthenticated(): boolean {
    return Boolean(sessionStorage.getItem(ACCESS_KEY));
  },
  setTokens(access: string, refresh: string, expiresIn: number) {
    sessionStorage.setItem(ACCESS_KEY, access);
    sessionStorage.setItem(REFRESH_KEY, refresh);
    sessionStorage.setItem(EXPIRY_KEY, String(Date.now() + expiresIn * 1000));
  },
  clear() {
    sessionStorage.removeItem(ACCESS_KEY);
    sessionStorage.removeItem(REFRESH_KEY);
    sessionStorage.removeItem(EXPIRY_KEY);
  },
  isAccessExpired(): boolean {
    const raw = sessionStorage.getItem(EXPIRY_KEY);
    if (!raw) return true;
    return Date.now() > Number(raw) - 15_000;
  },
};
