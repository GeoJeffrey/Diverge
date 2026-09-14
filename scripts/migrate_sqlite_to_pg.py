import sqlite3
import psycopg2

SQLITE_PATH = "data/diverge_raw.db"
PG_URL = "postgresql://postgres@localhost:5432/diverge"

tables = [
    "raw_posts",
    "post_timing",
    "ticker_time_bins",
    "text_features",
    "periodicity_stats",
    "index_values",
    "consumer_sentiment",
    "coordination_scores",
    "ticker_window_metrics",
    "duplicate_pairs",
    "reasoning_trace",
    "narrative_phylogeny"
]

s_conn = sqlite3.connect(SQLITE_PATH)
s_cur = s_conn.cursor()

p_conn = psycopg2.connect(PG_URL)
p_cur = p_conn.cursor()

for table in tables:
    try:
        s_cur.execute(f"PRAGMA table_info({table});")
        cols = [c[1] for c in s_cur.fetchall()]
        if not cols:
            continue
        
        col_names = ", ".join(cols)
        placeholders = ", ".join(["%s"] * len(cols))
        
        s_cur.execute(f"SELECT {col_names} FROM {table};")
        rows = s_cur.fetchall()
        
        if rows:
            insert_stmt = f"INSERT INTO {table} ({col_names}) VALUES ({placeholders}) ON CONFLICT DO NOTHING;"
            p_cur.executemany(insert_stmt, rows)
            p_conn.commit()
            print(f"Migrated {len(rows)} rows into PostgreSQL table '{table}'")
        else:
            print(f"Table '{table}' has 0 rows.")
    except Exception as e:
        p_conn.rollback()
        print(f"Error migrating {table}: {e}")

s_conn.close()
p_conn.close()
print("DATA MIGRATION TO POSTGRES COMPLETE.")
