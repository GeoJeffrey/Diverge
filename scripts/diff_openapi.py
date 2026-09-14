import urllib.request
import json
import difflib
import sys

try:
    with urllib.request.urlopen("http://localhost:8000/openapi.json") as resp:
        live_openapi = json.loads(resp.read().decode("utf-8"))
except Exception as e:
    print(f"Error fetching live openapi: {e}")
    sys.exit(1)

with open("docs/openapi.json", "r", encoding="utf-8") as f:
    frozen_openapi = json.load(f)

live_pretty = json.dumps(live_openapi, indent=2, sort_keys=True).splitlines()
frozen_pretty = json.dumps(frozen_openapi, indent=2, sort_keys=True).splitlines()

diff = list(difflib.unified_diff(frozen_pretty, live_pretty, fromfile="frozen_openapi", tofile="live_openapi", lineterm=""))

if not diff:
    print("SCHEMA_DIFF: EXACT MATCH (0 diff lines)")
else:
    print(f"SCHEMA_DIFF: FOUND {len(diff)} DIFFERENCE LINES:")
    for line in diff[:30]:
        print(line)
