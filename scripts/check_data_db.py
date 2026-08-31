import sqlite3
conn = sqlite3.connect('data/diverge_raw.db')
tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
print('Tables in data/diverge_raw.db:', tables)
for t in ['ticker_window_metrics', 'reasoning_trace', 'narrative_phylogeny', 'index_values', 'coordination_scores', 'duplicate_pairs']:
    if t in tables:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {cnt}')
    else:
        print(f'  {t}: TABLE MISSING')
conn.close()
