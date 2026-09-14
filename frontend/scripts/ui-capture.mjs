import { chromium } from "playwright";
import { writeFileSync } from "node:fs";

const BASE = process.env.APP_URL ?? "http://127.0.0.1:5173";
const captures = [];

async function main() {
  const browser = await chromium.launch({ headless: true, channel: "chrome" });
  const page = await browser.newPage();
  page.on("response", async (res) => {
    const url = res.url();
    if (!url.includes("localhost:8000")) return;
    let body = null;
    try {
      body = await res.json();
    } catch {
      try {
        body = await res.text();
      } catch {
        body = null;
      }
    }
    captures.push({
      url,
      method: res.request().method(),
      status: res.status(),
      body,
      headers: res.request().headers(),
    });
  });

  const step = process.argv[2] ?? "signup";
  const email = process.env.TEST_EMAIL ?? `wire.${Date.now()}@example.com`;
  const password = process.env.TEST_PASSWORD ?? "SecurePass123!";
  const fullName = process.env.TEST_NAME ?? "Wire Test";

  async function loginViaUi() {
    await page.goto(`${BASE}/login`);
    await page.locator("#email").fill(email);
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForURL("**/tickers", { timeout: 15000 });
  }

  if (step === "signup") {
    await page.goto(`${BASE}/login?tab=signup`);
    await page.getByRole("tab", { name: "Sign up" }).click();
    await page.locator("#full_name").fill(fullName);
    await page.locator("#email").fill(email);
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: "Create account" }).click();
    await page.waitForTimeout(2500);
  } else if (step === "login") {
    await page.goto(`${BASE}/login`);
    await page.locator("#email").fill(email);
    await page.locator("#password").fill(password);
    await page.getByRole("button", { name: "Sign in" }).click();
    await page.waitForTimeout(2500);
  } else if (step === "tickers") {
    await loginViaUi();
    await page.goto(`${BASE}/tickers`);
    await page.waitForTimeout(2500);
  } else if (step === "ticker") {
    const symbol = process.env.TEST_SYMBOL ?? "INFY";
    await loginViaUi();
    await page.goto(`${BASE}/ticker/${symbol}`);
    await page.waitForTimeout(3000);
  } else if (step === "simple") {
    const symbol = process.env.TEST_SYMBOL ?? "INFY";
    await loginViaUi();
    await page.goto(`${BASE}/ticker/${symbol}/simple`);
    await page.waitForTimeout(3000);
  } else if (step === "reasoning") {
    const symbol = process.env.TEST_SYMBOL ?? "INFY";
    await loginViaUi();
    await page.goto(`${BASE}/explainability?symbol=${symbol}`);
    await page.waitForTimeout(3000);
  } else if (step === "settings") {
    await loginViaUi();
    await page.goto(`${BASE}/settings`);
    await page.waitForTimeout(2500);
  } else if (step === "public-tickers") {
    await page.goto(`${BASE}/tickers`);
    await page.waitForTimeout(2500);
  } else if (step === "unauth-ticker") {
    const symbol = process.env.TEST_SYMBOL ?? "INFY";
    await page.goto(`${BASE}/ticker/${symbol}`);
    await page.waitForTimeout(2500);
  } else if (step === "bad-token") {
    const symbol = process.env.TEST_SYMBOL ?? "INFY";
    await page.addInitScript(() => {
      sessionStorage.setItem("diverge.session.access", "not-a-valid-jwt");
      sessionStorage.setItem("diverge.session.refresh", "not-a-valid-refresh");
      sessionStorage.setItem("diverge.session.expiry", String(Date.now() + 3600_000));
    });
    await page.goto(`${BASE}/ticker/${symbol}`);
    await page.waitForTimeout(2500);
  } else if (step === "scan-unavailable") {
    await loginViaUi();
    const symbols = ["INFY", "AAPL", "WIPRO", "RELIANCE", "TCS", "HDFCBANK", "TSLA", "NVDA"];
    for (const symbol of symbols) {
      await page.goto(`${BASE}/ticker/${symbol}`);
      await page.waitForTimeout(1500);
    }
  }

  const html = await page.content();
  const url = page.url();
  await browser.close();
  const out = { step, pageUrl: url, email, captures, htmlSnippet: html.slice(0, 2000) };
  writeFileSync("scripts/last-ui-capture.json", JSON.stringify(out, null, 2));
  const summary = captures.map((c) => ({
    status: c.status,
    method: c.method,
    url: c.url,
    hasAuth: Boolean(c.headers.authorization),
    keys: c.body && typeof c.body === "object" ? Object.keys(c.body) : null,
  }));
  console.log(JSON.stringify({ step, pageUrl: url, email, captureCount: captures.length, summary }, null, 2));
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
