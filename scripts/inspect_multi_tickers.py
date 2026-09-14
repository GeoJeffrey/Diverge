import urllib.request
import json

payload = json.dumps({'email': 'smoke_tester@diverge.ai', 'password': 'Password123!'}).encode()
req = urllib.request.Request('http://localhost:8000/auth/login', data=payload, headers={'Content-Type': 'application/json'})
token = json.loads(urllib.request.urlopen(req).read().decode())['access_token']

for sym in ['RELIANCE', 'WIPRO', 'LT']:
    req = urllib.request.Request(f'http://localhost:8000/ticker/{sym}', headers={'Authorization': f'Bearer {token}'})
    data = json.loads(urllib.request.urlopen(req).read().decode())
    print(f"\n=== {sym} ===")
    print("Dominant Index:", data['dominant_index'])
    print("Composite Score:", data['composite_score'])
    for k, v in data['indices'].items():
        print(f"  {k}: available={v['available']}, score={v['score']}, coverage_note={v['coverage_note']}")
