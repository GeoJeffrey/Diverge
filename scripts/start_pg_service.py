import os
import subprocess
import sys
import time

PG_DIR = r"C:\Users\geoje\.gemini\antigravity-ide\scratch\pgsql"
DATA_DIR = r"C:\Users\geoje\.gemini\antigravity-ide\scratch\pgdata"
INITDB = os.path.join(PG_DIR, "bin", "initdb.exe")
PG_CTL = os.path.join(PG_DIR, "bin", "pg_ctl.exe")
CREATEDB = os.path.join(PG_DIR, "bin", "createdb.exe")

if not os.path.exists(DATA_DIR):
    print(f"Initializing database cluster in {DATA_DIR}...")
    # Initialize with user 'postgres', no auth password needed locally, auth trust
    cmd = [INITDB, "-D", DATA_DIR, "-U", "postgres", "-A", "trust", "-E", "UTF8"]
    res = subprocess.run(cmd, capture_output=True, text=True)
    print("initdb stdout:", res.stdout)
    print("initdb stderr:", res.stderr)
    if res.returncode != 0:
        sys.exit(res.returncode)
else:
    print(f"Data dir {DATA_DIR} already exists.")

print("Starting PostgreSQL server...")
log_file = os.path.join(DATA_DIR, "logfile.log")
cmd_start = [PG_CTL, "-D", DATA_DIR, "-l", log_file, "-o", "-p 5432", "start"]
res = subprocess.run(cmd_start, capture_output=True, text=True)
print("pg_ctl stdout:", res.stdout)
print("pg_ctl stderr:", res.stderr)

time.sleep(2)

print("Creating database diverge if not exists...")
cmd_createdb = [CREATEDB, "-U", "postgres", "-p", "5432", "diverge"]
res = subprocess.run(cmd_createdb, capture_output=True, text=True)
print("createdb stdout:", res.stdout)
print("createdb stderr:", res.stderr)
