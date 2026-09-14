import psycopg2

try:
    conn = psycopg2.connect("postgresql://postgres@localhost:5432/postgres")
    conn.autocommit = True
    cur = conn.cursor()
    cur.execute("SELECT version();")
    print("Postgres Version:", cur.fetchone()[0])
    
    cur.execute("SELECT datname FROM pg_database WHERE datname='diverge';")
    row = cur.fetchone()
    if not row:
        cur.execute("CREATE DATABASE diverge;")
        print("Database 'diverge' created!")
    else:
        print("Database 'diverge' exists!")
    conn.close()

    # Verify connect to diverge database
    conn_div = psycopg2.connect("postgresql://postgres@localhost:5432/diverge")
    cur_div = conn_div.cursor()
    cur_div.execute("SELECT current_database();")
    print("Connected to target DB:", cur_div.fetchone()[0])
    conn_div.close()
    print("CONNECTIVITY_CHECK: PASS")
except Exception as e:
    print("CONNECTIVITY_CHECK: FAIL -", e)
