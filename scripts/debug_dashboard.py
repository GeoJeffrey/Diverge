import sys, io, re
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='ascii', errors='replace')

with open('dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find all JS function names
funcs = re.findall(r'(?:async\s+)?function\s+(\w+)\s*\(', html)
print('JS functions:', funcs)

# Find switchTab function body
m = re.search(r'function switchTab\([^)]*\)\s*\{[^}]+\}', html, re.DOTALL)
if m:
    print('\n=== switchTab ===')
    print(html[m.start():m.start()+800])

# Find composite/phase5 tab loading
for fname in ['loadComposite', 'loadPhase5', 'loadPhase6', 'renderAdvanced', 'loadAdvanced', 'fetchAdvanced']:
    m = re.search(rf'(?:async\s+)?function\s+{fname}\b', html)
    if m:
        print(f'\n=== {fname} found at {m.start()} ===')
        print(html[m.start():m.start()+500])

# Also look for composite tab switch call
idx = html.find("tab-composite")
if idx > -1:
    print(f'\n=== tab-composite area ({idx}) ===')
    print(html[idx-200:idx+500])
