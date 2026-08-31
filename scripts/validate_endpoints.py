import urllib.request, json, sys, io, time
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

time.sleep(1)  # let server start

def get(url):
    try:
        with urllib.request.urlopen(url, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {'_error': str(e)}

print('=== /api/stats ===')
s = get('http://localhost:8000/api/stats')
print('total_raw_posts:', s.get('total_raw_posts'))
print('phase5.ticker_window_metrics:', s.get('phase5', {}).get('ticker_window_metrics'))
print('phase6.reasoning_trace:', s.get('phase6', {}).get('reasoning_trace'))
print('phase6.narrative_phylogeny:', s.get('phase6', {}).get('narrative_phylogeny'))
print('phase3.index_values:', s.get('phase3', {}).get('index_values'))

print()
print('=== /api/advanced?ticker=AAPL&window= ===')
a = get('http://localhost:8000/api/advanced?ticker=AAPL&window=')
print('composite_score:', a.get('composite_score'))
print('dominant_index:', a.get('dominant_index'))
print('window_start_utc:', a.get('window_start_utc'))
print('aggregation_confidence:', a.get('aggregation_confidence'))
print('coordination:', a.get('coordination'))
print('trace.total_traces:', (a.get('trace') or {}).get('total_traces'))
print('trace.category_count:', len((a.get('trace') or {}).get('categories', {})))
print('phylogeny_context count:', len(a.get('phylogeny_context') or []))

print()
print('=== /api/reasoning-trace?ticker=AAPL ===')
t = get('http://localhost:8000/api/reasoning-trace?ticker=AAPL')
print('total_traces:', t.get('total_traces'))
print('window_start_utc:', t.get('window_start_utc'))
print('categories:', list(t.get('categories', {}).keys())[:5])

print()
print('=== /api/tickers (simple mode) ===')
ti = get('http://localhost:8000/api/tickers')
print('total tickers:', ti.get('total'))
if ti.get('tickers'):
    first = ti['tickers'][0]
    print('first ticker sample:', {k: v for k, v in first.items()})
