import sqlite3

for path in ['diverge.db', 'diverge_raw.db', 'data/diverge_raw.db']:
    try:
        conn = sqlite3.connect(path)
        cur = conn.cursor()
        cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [r[0] for r in cur.fetchall()]
        print(path, 'Tables:', len(tables))
        for t in ['raw_posts', 'ticker_window_metrics', 'index_values', 'reasoning_trace']:
            if t in tables:
                cur.execute(f"SELECT count(*) FROM {t};")
                print(f"   {t}: {cur.fetchone()[0]}")
    except Exception as e:
        print(path, 'Error:', e)
