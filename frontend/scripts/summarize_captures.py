import json
from pathlib import Path

files = [
    "scripts/cap-login.json",
    "scripts/cap-ticker.json",
    "scripts/cap-simple.json",
    "scripts/cap-reasoning.json",
]
root = Path(r"d:\Projects\Project Diverge frontend")
for rel in files:
    p = root / rel
    print("====", rel, "====")
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except Exception as e:
        print("parse error", e, "raw", p.read_text(encoding="utf-8")[:500])
        continue
    print("pageUrl", data.get("pageUrl"))
    print("captureCount", data.get("captureCount"))
    for c in data.get("captures", []):
        print(f"  {c['status']} {c['method']} {c['url']}")
        body = c.get("body")
        if isinstance(body, dict):
            keys = list(body.keys())
            print("    keys", keys)
            if "indices" in body:
                idx = body["indices"]
                print("    indices keys", list(idx.keys()) if isinstance(idx, dict) else type(idx))
                if isinstance(idx, dict):
                    for k, v in idx.items():
                        print("     ", k, v)
            if "coordination" in body:
                print("    coordination", body["coordination"])
            if "categories" in body:
                cats = body["categories"]
                print("    categories keys", list(cats.keys()) if isinstance(cats, dict) else cats)
                print("    total_traces", body.get("total_traces"), "symbol", body.get("symbol"))
            if "email" in body:
                print("    email", body.get("email"), "full_name", body.get("full_name"), "role", body.get("role"))
            if "access_token" in body:
                print("    token_type", body.get("token_type"), "expires_in", body.get("expires_in"), "has_refresh", "refresh_token" in body)
            if "error_code" in body or "message" in body:
                print("    error", body)
        else:
            print("    body type", type(body), str(body)[:200])
