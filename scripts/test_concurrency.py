import urllib.request
import json
import concurrent.futures
import time

BASE_URL = "http://localhost:8000"

def get_token():
    # Register test user
    payload = json.dumps({
        "email": "concurrency_test@diverge.ai",
        "password": "Password123!",
        "full_name": "Concurrency Tester"
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{BASE_URL}/auth/signup", data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data["access_token"]
    except Exception as e:
        # If already registered, login
        login_payload = json.dumps({
            "email": "concurrency_test@diverge.ai",
            "password": "Password123!"
        }).encode('utf-8')
        req = urllib.request.Request(f"{BASE_URL}/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            return data["access_token"]

def hit_endpoint(token, i):
    req = urllib.request.Request(f"{BASE_URL}/ticker/AAPL", headers={"Authorization": f"Bearer {token}"})
    start = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode())
            dur = round((time.time() - start) * 1000, 2)
            return (i, resp.status, dur, data.get("ticker"), None)
    except Exception as e:
        dur = round((time.time() - start) * 1000, 2)
        return (i, 500, dur, None, str(e))

if __name__ == "__main__":
    token = get_token()
    print("Obtained JWT token for concurrency test.")
    
    # 20 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(hit_endpoint, token, i) for i in range(20)]
        results = [f.result() for f in futures]
    
    success = [r for r in results if r[1] == 200]
    failures = [r for r in results if r[1] != 200]
    
    print(f"Total Requests: {len(results)}, Successful: {len(success)}, Failed: {len(failures)}")
    for r in results[:10]:
        print(f"  Req #{r[0]}: Status={r[1]}, Latency={r[2]}ms, Ticker={r[3]}")
    if failures:
        print("Failures encountered:", failures)
    else:
        print("CONCURRENCY_SANITY_CHECK: PASS (Zero locking errors, zero failures)")
