import urllib.request, urllib.parse, json

base = 'http://localhost:8000'
w = '2026-06-02T11:43:14.427080+00:00'
url = base + '/api/advanced?ticker=AAPL&window=' + urllib.parse.quote(w)
res = json.loads(urllib.request.urlopen(url).read())

print('AAPL Composite Score:', res.get('composite_score'))
print('AAPL Dominant Index:', res.get('dominant_index'))
print('AAPL Indices breakdown:', res.get('indices'))

traces = res.get('trace', {}).get('categories', {})
print('AAPL Reasoning Traces categories:', list(traces.keys()))
for cat, posts in traces.items():
    print(f'  - {cat}: {len(posts)} posts driving this metric')
    if posts:
        print(f'    Sample post: [{posts[0]["platform"]}] weight={posts[0]["weight"]} text="{posts[0]["text_preview"][:60]}..."')
