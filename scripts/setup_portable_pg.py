import os
import sys
import urllib.request
import zipfile
import shutil

TARGET_DIR = r"C:\Users\geoje\.gemini\antigravity-ide\scratch\pgsql"
ZIP_PATH = r"C:\Users\geoje\.gemini\antigravity-ide\scratch\pgsql.zip"
URL = "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64-binaries.zip"

os.makedirs(r"C:\Users\geoje\.gemini\antigravity-ide\scratch", exist_ok=True)

if not os.path.exists(ZIP_PATH):
    print(f"Downloading PostgreSQL binaries from {URL}...")
    def reporthook(count, block_size, total_size):
        percent = int(count * block_size * 100 / total_size)
        if count % 1000 == 0 or percent == 100:
            sys.stdout.write(f"\rDownloading: {percent}% ({count * block_size // (1024*1024)} MB / {total_size // (1024*1024)} MB)")
            sys.stdout.flush()
    urllib.request.urlretrieve(URL, ZIP_PATH, reporthook)
    print("\nDownload complete.")
else:
    print(f"Zip already exists at {ZIP_PATH}")

if not os.path.exists(os.path.join(TARGET_DIR, "bin", "postgres.exe")):
    print(f"Extracting {ZIP_PATH} to {TARGET_DIR}...")
    with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
        zip_ref.extractall(r"C:\Users\geoje\.gemini\antigravity-ide\scratch")
    print("Extraction complete.")
else:
    print("Postgres binaries already extracted.")
