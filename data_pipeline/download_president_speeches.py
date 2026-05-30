import requests
import os
import time
from urllib.parse import quote

SAVE_DIR = "/workspaces/codespaces-blank/election-intelligence/raw_data/rag_data/president_speeches"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Referer": "https://prsindia.org/policy/president-address"
}

BASE = "https://prsindia.org/files/policy/Policy_President_Speech"

SPEECHES = [
    ("1952", f"{BASE}/1952.pdf"),
    ("1953", f"{BASE}/1953.pdf"),
    ("1954", f"{BASE}/1954.pdf"),
    ("1955", f"{BASE}/1955.pdf"),
    ("1956", f"{BASE}/1956.pdf"),
    ("1957", f"{BASE}/1957.pdf"),
    ("1958", f"{BASE}/1958.pdf"),
    ("1959", f"{BASE}/1959.pdf"),
    ("1960", f"{BASE}/1960.pdf"),
    ("1961", f"{BASE}/1961.pdf"),
    ("1962", f"{BASE}/1962.pdf"),
    ("1963", f"{BASE}/1963.pdf"),
    ("1964", f"{BASE}/1964.pdf"),
    ("1965", f"{BASE}/1965.pdf"),
    ("1966", f"{BASE}/1966.pdf"),
    ("1967", f"{BASE}/1967.pdf"),
    ("1968", f"{BASE}/1968.pdf"),
    ("1969", f"{BASE}/1969_0.pdf"),
    ("1970", f"{BASE}/1970.pdf"),
    ("1971", f"{BASE}/1971.pdf"),
    ("1972", f"{BASE}/1972.pdf"),
    ("1973", f"{BASE}/1973.pdf"),
    ("1974", f"{BASE}/1974.pdf"),
    ("1975", f"{BASE}/1975.pdf"),
    ("1976", f"{BASE}/1976.pdf"),
    ("1977", f"{BASE}/1977.pdf"),
    ("1978", f"{BASE}/1978.pdf"),
    ("1979", f"{BASE}/1979.pdf"),
    ("1980", f"{BASE}/1980.pdf"),
    ("1981", f"{BASE}/1981.pdf"),
    ("1982", f"{BASE}/1982.pdf"),
    ("1983", f"{BASE}/1983.pdf"),
    ("1984", f"{BASE}/1984.pdf"),
    ("1985", f"{BASE}/1985.pdf"),
    ("1986", f"{BASE}/1986.pdf"),
    ("1987", f"{BASE}/1987.pdf"),
    ("1988", f"{BASE}/1988.pdf"),
    ("1989", f"{BASE}/1989.pdf"),
    ("1990", f"{BASE}/1990.pdf"),
    ("1991", f"{BASE}/1991.pdf"),
    ("1992", f"{BASE}/1992.pdf"),
    ("1993", f"{BASE}/1993.pdf"),
    ("1994", f"{BASE}/1994.pdf"),
    ("1995", f"{BASE}/1995.pdf"),
    ("1996", f"{BASE}/1996.pdf"),
    ("1997", f"{BASE}/1997.pdf"),
    ("1998", f"{BASE}/1998.pdf"),
    ("1999", f"{BASE}/1999.pdf"),
    ("2000", f"{BASE}/2000.pdf"),
    ("2001", f"{BASE}/2001.pdf"),
    ("2002", f"{BASE}/2002.pdf"),
    ("2003", f"{BASE}/2003.pdf"),
    ("2004", f"{BASE}/2004.pdf"),
    ("2005", f"{BASE}/2005.pdf"),
    ("2006", f"{BASE}/2006.pdf"),
    ("2007", f"{BASE}/2007.pdf"),
    ("2008", f"{BASE}/2008.pdf"),
    ("2010", f"{BASE}/2010.pdf"),
    ("2011", f"{BASE}/2011.pdf"),
    ("2012", f"{BASE}/2012.pdf"),
    ("2013", f"{BASE}/2013.pdf"),
    ("2014", f"{BASE}/2014_0.pdf"),
    ("2015", f"{BASE}/2015_0.pdf"),
    ("2016", f"{BASE}/2016_0.pdf"),
    ("2018", f"{BASE}/2018.pdf"),
    ("2019-Jan", f"{BASE}/President's Address_January, 2019.pdf"),
    ("2019-Jun", f"{BASE}/President's Address_June, 2019.pdf"),
    ("2020", f"{BASE}/President's Address_2020_0.pdf"),
    ("2021", f"{BASE}/President's Address_2021_0.pdf"),
    ("2022", f"{BASE}/2022/President's_Address_2022.pdf"),
    ("2023", f"{BASE}/2023/President's_Address_2023.pdf"),
    ("2024", f"{BASE}/2024/President's_Address_2024.pdf"),
    ("2026", "https://prsindia.org/files/policy/Policy_President_Address/2026-27/Presidents_Speech_2026.pdf"),
]

def download(year, url):
    filename = f"president_speech_{year}.pdf"
    filepath = os.path.join(SAVE_DIR, filename)
    if os.path.exists(filepath):
        print(f"[Skip] {filename}")
        return True
    try:
        encoded_url = url.replace(" ", "%20").replace("'", "%27")
        r = requests.get(encoded_url, headers=HEADERS, timeout=30)
        if r.status_code == 200 and len(r.content) > 1000:
            with open(filepath, "wb") as f:
                f.write(r.content)
            print(f"[OK] {filename} — {len(r.content)//1024}KB")
            return True
        else:
            print(f"[FAIL] {year} — status {r.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] {year} — {e}")
        return False

ok, fail = 0, 0
for year, url in SPEECHES:
    if download(year, url):
        ok += 1
    else:
        fail += 1
    time.sleep(0.5)

print(f"\nDone. Success: {ok} | Failed: {fail}")
print(f"Files saved to: {SAVE_DIR}")
