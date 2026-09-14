import json
from pathlib import Path

p = Path(r"C:\Users\geoje\AppData\Local\Temp\live-openapi.json")
d = json.loads(p.read_text(encoding="utf-8"))
print("global security", d.get("security"))
print("schemes", list(d.get("components", {}).get("securitySchemes", {})))
for path, methods in d["paths"].items():
    for m, op in methods.items():
        if m.startswith("x-"):
            continue
        sec = op.get("security", "(inherit)")
        print(f"{m.upper():6} {path:32} security={sec}")
