import sqlite3
conn = sqlite3.connect('data/diverge_raw.db')

# Check latest ticker_window_metrics for AAPL
print('=== ticker_window_metrics AAPL (latest 3) ===')
rows = conn.execute('SELECT window_start_utc, composite_score, aggregation_confidence FROM ticker_window_metrics WHERE ticker=? ORDER BY (composite_score IS NOT NULL) DESC, window_start_utc DESC LIMIT 3', ('AAPL',)).fetchall()
for r in rows:
    print(' ', r)

# Also check latest without NULL filter
print('\n=== ticker_window_metrics AAPL (no filter, latest 3) ===')
rows = conn.execute('SELECT window_start_utc, composite_score, aggregation_confidence FROM ticker_window_metrics WHERE ticker=? ORDER BY window_start_utc DESC LIMIT 3', ('AAPL',)).fetchall()
for r in rows:
    print(' ', r)

# Check reasoning trace for latest window
latest_window = rows[0][0] if rows else None
if latest_window:
    rt_cnt = conn.execute('SELECT COUNT(*) FROM reasoning_trace WHERE ticker=? AND window_start_utc=?', ('AAPL', latest_window)).fetchone()[0]
    print(f'\nreasoning_trace count for latest window ({latest_window}): {rt_cnt}')

conn.close()
