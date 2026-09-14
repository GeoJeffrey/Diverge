import urllib.request
import json
import sys

BASE_URL = "http://localhost:8000"

def run_tests():
    # 1. Health
    with urllib.request.urlopen(f"{BASE_URL}/health") as resp:
        assert resp.status == 200
        health = json.loads(resp.read().decode())
        print("PASS: /health ->", health)
        assert health["database"] == "connected"

    # 2. Public /tickers
    with urllib.request.urlopen(f"{BASE_URL}/tickers") as resp:
        assert resp.status == 200
        tickers = json.loads(resp.read().decode())
        print(f"PASS: /tickers -> {tickers['total']} tickers")
        assert tickers["total"] > 0

    # 3. Public /ticker/{symbol}/simple
    with urllib.request.urlopen(f"{BASE_URL}/ticker/AAPL/simple") as resp:
        assert resp.status == 200
        simple = json.loads(resp.read().decode())
        print("PASS: /ticker/AAPL/simple ->", simple["symbol"], simple["verdict_label"])
        assert "symbol" in simple
        assert "verdict_label" in simple

    # 4. Auth Signup / Login
    auth_payload = json.dumps({
        "email": "smoke_tester@diverge.ai",
        "password": "Password123!",
        "full_name": "Smoke Tester"
    }).encode('utf-8')
    try:
        req = urllib.request.Request(f"{BASE_URL}/auth/signup", data=auth_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode())
    except Exception:
        login_payload = json.dumps({
            "email": "smoke_tester@diverge.ai",
            "password": "Password123!"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            token_data = json.loads(resp.read().decode())

    token = token_data["access_token"]
    print("PASS: /auth/signup & /auth/login -> JWT obtained")

    # 5. /auth/me
    req = urllib.request.Request(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        me = json.loads(resp.read().decode())
        print("PASS: /auth/me ->", me["email"])

    # 6. Protected /ticker/{symbol} (Advanced)
    req = urllib.request.Request(f"{BASE_URL}/ticker/AAPL", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        adv = json.loads(resp.read().decode())
        print(f"PASS: /ticker/AAPL (Protected) -> symbol={adv['symbol']}, composite_score={adv['composite_score']}")
        assert adv["symbol"] == "AAPL"
        assert "indices" in adv

    # 7. /ticker/{symbol}/reasoning
    req = urllib.request.Request(f"{BASE_URL}/ticker/AAPL/reasoning", headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        reasoning = json.loads(resp.read().decode())
        print(f"PASS: /ticker/AAPL/reasoning -> total_traces={reasoning['total_traces']}")

    # 8. Negative test: Unauthenticated access to /ticker/AAPL
    try:
        urllib.request.urlopen(f"{BASE_URL}/ticker/AAPL")
        print("FAIL: Expected 401 for unauthenticated /ticker/AAPL")
        sys.exit(1)
    except urllib.error.HTTPError as e:
        assert e.code == 401
        print("PASS: Unauthenticated /ticker/AAPL correctly returned 401 Unauthorized")

    print("\nALL API SMOKE TESTS PASSED AGAINST POSTGRESQL!")

if __name__ == "__main__":
    run_tests()
