/*
 * app.js
 * Client-side logic for Diverge UI.
 * simple.html sets data-page="simple" on <body>.
 * advanced.html sets data-page="advanced" on <body>.
 * init() dispatches to the correct loader on DOMContentLoaded.
 */

/* ── Simple Mode ───────────────────────────────────────── */
async function loadSimpleMode() {
  const res = await fetch('/api/tickers').then(r => r.json());
  const grid = document.getElementById('cards-grid');
  if (!res.tickers || !res.tickers.length) {
    grid.innerHTML = '<div style="grid-column:1/-1;color:var(--text2)">No populated tickers found.</div>';
    return;
  }
  grid.innerHTML = res.tickers.map(t => {
    const scoreStr = t.score !== null ? t.score.toFixed(1) : '—';
    const scoreColor = t.score === null ? 'var(--text2)' : t.score >= 65 ? 'var(--green)' : t.score >= 35 ? 'var(--gray)' : 'var(--amber)';
    const pillClass = `pill-${t.verdict_label}`;
    return `
      <div class="card" onclick="window.location.href='/ui/advanced.html?ticker=${t.ticker}&window=${encodeURIComponent(t.window_start_utc)}'">
        <div class="card-top">
          <div>
            <div class="ticker">${t.ticker}</div>
            <div class="trust">⏱ ${t.window_start_utc.slice(0,16).replace('T',' ')}</div>
          </div>
          <div class="score" style="color:${scoreColor}">${scoreStr}</div>
        </div>
        <div style="margin-bottom:12px">
          <span class="pill ${pillClass}">${t.verdict_label}</span>
        </div>
        <div class="why">${t.why_sentence}</div>
        <div class="trust">🔒 ${t.trust_label}</div>
      </div>
    `;
  }).join('');
}

/* ── Advanced Mode ─────────────────────────────────────── */
async function loadAdvancedMode() {
  const params = new URLSearchParams(window.location.search);
  const ticker = params.get('ticker') || 'AAPL';
  const wstart = params.get('window') || '';

  document.getElementById('title-ticker').textContent = `${ticker} — Advanced Diagnostics`;
  document.getElementById('title-sub').textContent = `Loading detailed diagnostics for ${ticker}…`;

  let res;
  try {
    res = await fetch(`/api/advanced?ticker=${encodeURIComponent(ticker)}&window=${encodeURIComponent(wstart)}`).then(r => r.json());
  } catch (e) {
    document.getElementById('title-sub').textContent = `Network error: ${e.message}`;
    return;
  }

  if (res.error) {
    document.getElementById('title-sub').textContent = `Error: ${res.error}`;
    return;
  }

  // Populate indices — guard all values for null/undefined
  const fmt = (v, decimals = 3) => (v !== null && v !== undefined) ? Number(v).toFixed(decimals) : 'NULL';
  document.getElementById('val-rn').textContent    = fmt(res.indices?.rn);
  document.getElementById('val-cirg').textContent  = fmt(res.indices?.cirg);
  document.getElementById('val-cli').textContent   = fmt(res.indices?.cli);
  document.getElementById('val-cassi').textContent = fmt(res.indices?.cassi);
  document.getElementById('val-vdi').textContent   = fmt(res.indices?.vdi);

  // Coordination & Trust — guard against null coordination_score
  const coordScore = res.coordination?.coordination_score;
  document.getElementById('val-coord').textContent =
    (coordScore !== null && coordScore !== undefined) ? Number(coordScore).toFixed(1) : 'NULL';
  document.getElementById('val-trust').textContent =
    `Trust Flag: ${res.coordination?.confidence_flag || 'N/A'}`;

  const flagsContainer = document.getElementById('risk-flags-container');
  if (res.risk_flags && res.risk_flags.length) {
    flagsContainer.innerHTML = res.risk_flags.map(f => `<span class="chip chip-reversal">${f}</span>`).join('');
  } else {
    flagsContainer.innerHTML = '<span style="font-size:12px;color:var(--text2)">No active risk flags</span>';
  }

  // Update subtitle with composite score summary
  const composite = res.composite_score;
  document.getElementById('title-sub').textContent =
    `Window: ${res.window_start_utc ? res.window_start_utc.slice(0,16).replace('T',' ') : 'N/A'} · ` +
    `Score: ${(composite !== null && composite !== undefined) ? Number(composite).toFixed(1) : 'N/A'} · ` +
    `Dominant: ${res.dominant_index || 'N/A'} · Confidence: ${res.aggregation_confidence || 'N/A'}`;

  // Phylogeny Strip
  const phyloStrip = document.getElementById('phylo-strip');
  if (!res.phylogeny_context || !res.phylogeny_context.length) {
    phyloStrip.innerHTML = '<span style="color:var(--text2);font-size:13px">No narrative phylogeny history recorded yet.</span>';
  } else {
    phyloStrip.innerHTML = res.phylogeny_context.map(p => {
      const chipClass = p.mutation_type === 'composite_reversal' ? 'chip-reversal'
                      : p.mutation_type === 'dominant_index_shift' ? 'chip-shift' : '';
      const delta = p.composite_delta;
      return `
        <div style="background:var(--bg);border:1px solid var(--border);border-radius:8px;padding:10px 14px;display:flex;flex-direction:column;gap:4px">
          <div style="font-size:10px;color:var(--text2);font-family:'JetBrains Mono'">${p.window_start_utc.slice(0,16).replace('T',' ')}</div>
          <div><span class="chip ${chipClass}">${p.mutation_type}</span></div>
          <div style="font-size:11px;color:var(--text2)">Δ: ${delta !== null && delta !== undefined ? (delta > 0 ? '+' : '') + delta : '—'}</div>
        </div>
      `;
    }).join('<div style="color:var(--text2);font-size:18px;padding:0 4px">→</div>');
  }

  // Reasoning Traces — collect all categories into flat list
  const tbody = document.getElementById('traces-body');
  const traceData = res.trace || {};
  const categories = traceData.categories || {};
  const allTraces = [];
  Object.keys(categories).forEach(cat => {
    (categories[cat] || []).forEach(t => allTraces.push({ category: cat, ...t }));
  });

  if (!allTraces.length) {
    tbody.innerHTML = `<tr><td colspan="4" style="color:var(--text2);padding:24px;text-align:center">
      ${(traceData.total_traces || 0) === 0
        ? 'No reasoning traces for this window. Run Phase 6 to generate audit traces.'
        : 'No categorised traces found.'}
    </td></tr>`;
    return;
  }

  tbody.innerHTML = allTraces.slice(0, 100).map(t => `
    <tr>
      <td><span class="chip">${t.category || '—'}</span></td>
      <td class="mono">${(t.weight !== null && t.weight !== undefined) ? Number(t.weight).toFixed(3) : '—'}</td>
      <td><span class="chip" style="background:rgba(16,185,129,0.15);color:var(--green);border-color:var(--green)">${t.platform || 'unknown'}</span></td>
      <td style="font-size:12px;line-height:1.4">${t.text_preview || '—'}</td>
    </tr>
  `).join('');
}

/* ── Dispatcher ────────────────────────────────────────── */
function init() {
  const page = document.body.dataset.page;
  if (page === 'simple')   loadSimpleMode();
  if (page === 'advanced') loadAdvancedMode();
}

document.addEventListener('DOMContentLoaded', init);
