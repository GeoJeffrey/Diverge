import urllib.request
import json

payload = json.dumps({'email': 'smoke_tester@diverge.ai', 'password': 'Password123!'}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=payload, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

req = urllib.request.Request('http://localhost:8000/ticker/AAPL', headers={'Authorization': f'Bearer {token}'})
data = json.loads(urllib.request.urlopen(req).read().decode())

print("Ticker:", data['symbol'], f"({data['name']})")
print("Composite score:", data['composite_score'])
print("Aggregation confidence:", data['aggregation_confidence'])
print("Dominant index:", data['dominant_index'])
print("Risk flags:", data['risk_flags'])
print("Coordination score:", data['coordination']['coordination_score'], f"(available={data['coordination']['available']})")
print("Phylogeny context items count:", len(data['phylogeny_context']))
for k, v in data['indices'].items():
    print(f"  {k} ({v['label']}): available={v['available']}, score={v['score']}, coverage_note={v['coverage_note']}")


