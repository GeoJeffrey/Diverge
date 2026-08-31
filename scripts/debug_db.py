import sqlite3

db = 'diverge_raw.db'
conn = sqlite3.connect(db)
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print('Tables:', [t[0] for t in tables])

for t in ['ticker_window_metrics', 'reasoning_trace', 'narrative_phylogeny', 'index_values', 'coordination_scores']:
    try:
        cnt = conn.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
        print(f'  {t}: {cnt} rows')
        if cnt > 0:
            cur = conn.execute(f'SELECT * FROM {t} LIMIT 1')
            cols = [d[0] for d in cur.description]
            row = cur.fetchone()
            print(f'    cols: {cols}')
            print(f'    sample: {dict(zip(cols, row))}')
    except Exception as e:
        print(f'  {t}: ERROR - {e}')
conn.close()
