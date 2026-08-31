import re

with open('dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Find the loadExplainability function block
start = content.find('async function loadExplainability()')
if start == -1:
    print('ERROR: function not found')
    exit(1)

# Find the end - next function definition or closing </script>
end_patterns = ['async function runScraper', '// \u2500\u2500 Scraper Actions']
end = len(content)
for pat in end_patterns:
    idx = content.find(pat, start)
    if idx != -1 and idx < end:
        end = idx

print(f'Block from {start} to {end}')
print('Current block:', repr(content[start:start+300]))

new_block = '''async function loadExplainability() {
  const ticker = document.getElementById('explain-ticker').value || 'AAPL';

  // Narrative Phylogeny Tree
  let phyloData = { nodes: [] };
  try {
    phyloData = await fetch(`/api/narrative-phylogeny?ticker=${ticker}`).then(r => r.json());
  } catch (e) { /* ignore */ }

  const phyloBody = document.getElementById('phylo-body');
  if (!phyloData.nodes?.length) {
    phyloBody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="empty-msg">No narrative lineage found for ${ticker}. Run Phase 6 to generate phylogeny.</div></div></td></tr>`;
  } else {
    phyloBody.innerHTML = phyloData.nodes.map(n => {
      const delta = n.composite_delta;
      const deltaColor = (delta !== null && delta !== undefined && delta >= 0) ? 'var(--green)' : 'var(--red)';
      const deltaStr = (delta !== null && delta !== undefined) ? (delta > 0 ? '+' : '') + delta : '\\u2014';
      return `
      <tr>
        <td class="mono" style="font-size:10px">${ts(n.window_start_utc)}</td>
        <td><span class="badge badge-bullish">${esc(n.mutation_type)}</span></td>
        <td class="mono" style="color:${deltaColor}">${deltaStr}</td>
        <td class="mono" style="font-size:11px">${esc(JSON.stringify(n.mutation_detail))}</td>
      </tr>`;
    }).join('');
  }

  // Reasoning Trace Audit (use LATEST window for richest traces)
  const traceBody = document.getElementById('trace-body');
  traceBody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="spinner"></div><br>Loading audit traces...</div></td></tr>`;

  // Use latest (last) phylogeny node — it has the most recent traces
  const nodes = phyloData.nodes || [];
  const latestNode = nodes.length > 0 ? nodes[nodes.length - 1] : null;
  const wstart = latestNode?.window_start_utc || '';

  let traceData = { categories: {}, total_traces: 0 };
  try {
    traceData = await fetch(`/api/reasoning-trace?ticker=${ticker}&window_start=${encodeURIComponent(wstart)}`).then(r => r.json());
  } catch (e) { /* ignore */ }

  const allItems = [];
  if (traceData.categories) {
    Object.keys(traceData.categories).forEach(cat => {
      (traceData.categories[cat] || []).forEach(item => {
        allItems.push({ category: cat, ...item });
      });
    });
  }

  if (!allItems.length) {
    traceBody.innerHTML = `<tr><td colspan="4"><div class="empty-state"><div class="empty-msg">
      No audit traces for <strong>${ticker}</strong>${wstart ? ` at window ${ts(wstart)}` : ''}.
      Total in DB: ${traceData.total_traces || 0}. Run Phase 6 to populate audit trail.
    </div></div></td></tr>`;
  } else {
    traceBody.innerHTML = allItems.slice(0, 100).map(t => `
      <tr>
        <td><span class="badge badge-neutral">${esc(t.category || '\\u2014')}</span></td>
        <td class="mono">${(t.weight !== null && t.weight !== undefined) ? Number(t.weight).toFixed(3) : '\\u2014'}</td>
        <td><span class="badge badge-bullish">${esc(t.platform || 'unknown')}</span></td>
        <td style="font-size:11px">${esc(t.text_preview || '\\u2014')}</td>
      </tr>
    `).join('');
  }
}

'''

content = content[:start] + new_block + content[end:]

with open('dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)

print('Done! New block length:', len(new_block))
