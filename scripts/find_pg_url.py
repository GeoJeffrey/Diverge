import urllib.request
import re

req = urllib.request.Request('https://www.enterprisedb.com/download-postgresql-binaries', headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req) as resp:
        content = resp.read().decode('utf-8', errors='ignore')
        matches = [m for m in re.findall(r'https?://[^\s\"\'<>]+\.zip', content)]
        for m in sorted(list(set(matches))):
            if '16' in m or '15' in m or 'windows' in m:
                print(m)
except Exception as e:
    print("Error:", e)
