import urllib.request

candidates = [
    "https://sbp.enterprisedb.com/getfile.jsp?fileid=1259021",
    "https://get.enterprisedb.com/postgresql/postgresql-16.2-1-windows-x64-binaries.zip",
    "https://get.enterprisedb.com/postgresql/postgresql-16.1-1-windows-x64-binaries.zip",
    "https://get.enterprisedb.com/postgresql/postgresql-15.6-1-windows-x64-binaries.zip"
]

for url in candidates:
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req) as resp:
            print(url, "->", resp.status, resp.headers.get('Content-Length'))
    except Exception as e:
        print(url, "->", e)
