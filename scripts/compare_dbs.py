import sqlite3, os

for dbp in ['diverge_raw.db', 'data/diverge_raw.db']:
    if os.path.exists(dbp):
        conn = sqlite3.connect(dbp)
        tables = [t[0] for t in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
        rt = conn.execute('SELECT COUNT(*) FROM reasoning_trace').fetchone()[0] if 'reasoning_trace' in tables else 'MISSING'
        twm = conn.execute('SELECT COUNT(*) FROM ticker_window_metrics').fetchone()[0] if 'ticker_window_metrics' in tables else 'MISSING'
        raw = conn.execute('SELECT COUNT(*) FROM raw_posts').fetchone()[0] if 'raw_posts' in tables else 'MISSING'
        print(f'{dbp}: raw_posts={raw}, ticker_window_metrics={twm}, reasoning_trace={rt}')
        if 'reasoning_trace' in tables and rt != 'MISSING' and rt > 0:
            w = conn.execute('SELECT DISTINCT window_start_utc FROM reasoning_trace WHERE ticker=? ORDER BY window_start_utc DESC LIMIT 3', ('AAPL',)).fetchall()
            print(f'  AAPL reasoning_trace latest windows: {[r[0] for r in w]}')
        conn.close()
    else:
        print(f'{dbp}: NOT FOUND')
