import requests
import os
import time

SAVE_DIR = "/workspaces/codespaces-blank/election-intelligence/raw_data/rag_data/budget_speeches"
os.makedirs(SAVE_DIR, exist_ok=True)

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36", "Accept": "application/pdf,*/*", "Accept-Language": "en-US,en;q=0.9", "Referer": "https://www.indiabudget.gov.in/bspeech.php"}

# All budget speech URLs from indiabudget.gov.in
BUDGET_URLS = [
    ("1947-48", "https://www.indiabudget.gov.in/doc/bspeech/bs194748.pdf"),
    ("1948-49", "https://www.indiabudget.gov.in/doc/bspeech/bs194849.pdf"),
    ("1949-50", "https://www.indiabudget.gov.in/doc/bspeech/bs194950.pdf"),
    ("1950-51", "https://www.indiabudget.gov.in/doc/bspeech/bs195051.pdf"),
    ("1951-52", "https://www.indiabudget.gov.in/doc/bspeech/bs195152.pdf"),
    ("1952-53", "https://www.indiabudget.gov.in/doc/bspeech/bs195253.pdf"),
    ("1952-53-I", "https://www.indiabudget.gov.in/doc/bspeech/bs195253(I).pdf"),
    ("1953-54", "https://www.indiabudget.gov.in/doc/bspeech/bs195354.pdf"),
    ("1954-55", "https://www.indiabudget.gov.in/doc/bspeech/bs195455.pdf"),
    ("1955-56", "https://www.indiabudget.gov.in/doc/bspeech/bs195556.pdf"),
    ("1956-57", "https://www.indiabudget.gov.in/doc/bspeech/bs195657.pdf"),
    ("1956-57-Nov", "https://www.indiabudget.gov.in/doc/bspeech/bs195657(November).pdf"),
    ("1957-58", "https://www.indiabudget.gov.in/doc/bspeech/bs195758.pdf"),
    ("1957-58-I", "https://www.indiabudget.gov.in/doc/bspeech/bs195758(I).pdf"),
    ("1958-59", "https://www.indiabudget.gov.in/doc/bspeech/bs195859.pdf"),
    ("1959-60", "https://www.indiabudget.gov.in/doc/bspeech/bs195960.pdf"),
    ("1960-61", "https://www.indiabudget.gov.in/doc/bspeech/bs196061.pdf"),
    ("1961-62", "https://www.indiabudget.gov.in/doc/bspeech/bs196162.pdf"),
    ("1962-63", "https://www.indiabudget.gov.in/doc/bspeech/bs196263.pdf"),
    ("1962-63-I", "https://www.indiabudget.gov.in/doc/bspeech/bs196263(I).pdf"),
    ("1963-64", "https://www.indiabudget.gov.in/doc/bspeech/bs196364.pdf"),
    ("1964-65", "https://www.indiabudget.gov.in/doc/bspeech/bs196465.pdf"),
    ("1965-66", "https://www.indiabudget.gov.in/doc/bspeech/bs196566.pdf"),
    ("1965-66-Aug", "https://www.indiabudget.gov.in/doc/bspeech/bs196566(August).pdf"),
    ("1966-67", "https://www.indiabudget.gov.in/doc/bspeech/bs196667.pdf"),
    ("1967-68", "https://www.indiabudget.gov.in/doc/bspeech/bs196768.pdf"),
    ("1967-68-I", "https://www.indiabudget.gov.in/doc/bspeech/bs196768(I).pdf"),
    ("1968-69", "https://www.indiabudget.gov.in/doc/bspeech/bs196869.pdf"),
    ("1969-70", "https://www.indiabudget.gov.in/doc/bspeech/bs196970.pdf"),
    ("1970-71", "https://www.indiabudget.gov.in/doc/bspeech/bs197071.pdf"),
    ("1971-72", "https://www.indiabudget.gov.in/doc/bspeech/bs197172.pdf"),
    ("1971-72-Dec", "https://www.indiabudget.gov.in/doc/bspeech/bs197172december.pdf"),
    ("1971-72-I", "https://www.indiabudget.gov.in/doc/bspeech/bs197172(I).pdf"),
    ("1972-73", "https://www.indiabudget.gov.in/doc/bspeech/bs197273.pdf"),
    ("1973-74", "https://www.indiabudget.gov.in/doc/bspeech/bs197374.pdf"),
    ("1974-75", "https://www.indiabudget.gov.in/doc/bspeech/bs197475.pdf"),
    ("1974-75-Jul", "https://www.indiabudget.gov.in/doc/bspeech/bs197475(july).pdf"),
    ("1975-76", "https://www.indiabudget.gov.in/doc/bspeech/bs197576.pdf"),
    ("1976-77", "https://www.indiabudget.gov.in/doc/bspeech/bs197677.pdf"),
    ("1977-78", "https://www.indiabudget.gov.in/doc/bspeech/bs197778.pdf"),
    ("1977-78-I", "https://www.indiabudget.gov.in/doc/bspeech/bs197778(I).pdf"),
    ("1978-79", "https://www.indiabudget.gov.in/doc/bspeech/bs197879.pdf"),
    ("1979-80", "https://www.indiabudget.gov.in/doc/bspeech/bs197980.pdf"),
    ("1980-81", "https://www.indiabudget.gov.in/doc/bspeech/bs198081.pdf"),
    ("1980-81-I", "https://www.indiabudget.gov.in/doc/bspeech/bs198081(I).pdf"),
    ("1981-82", "https://www.indiabudget.gov.in/doc/bspeech/bs198182.pdf"),
    ("1982-83", "https://www.indiabudget.gov.in/doc/bspeech/bs198283.pdf"),
    ("1983-84", "https://www.indiabudget.gov.in/doc/bspeech/bs198384.pdf"),
    ("1984-85", "https://www.indiabudget.gov.in/doc/bspeech/bs198485.pdf"),
    ("1985-86", "https://www.indiabudget.gov.in/doc/bspeech/bs198586.pdf"),
    ("1986-87", "https://www.indiabudget.gov.in/doc/bspeech/bs198687.pdf"),
    ("1987-88", "https://www.indiabudget.gov.in/doc/bspeech/bs198788.pdf"),
    ("1988-89", "https://www.indiabudget.gov.in/doc/bspeech/bs198889.pdf"),
    ("1989-90", "https://www.indiabudget.gov.in/doc/bspeech/bs198990.pdf"),
    ("1990-91", "https://www.indiabudget.gov.in/doc/bspeech/bs199091.pdf"),
    ("1991-92", "https://www.indiabudget.gov.in/doc/bspeech/bs199192.pdf"),
    ("1991-92-I", "https://www.indiabudget.gov.in/doc/bspeech/bs199192(I).pdf"),
    ("1992-93", "https://www.indiabudget.gov.in/doc/bspeech/bs199293.pdf"),
    ("1993-94", "https://www.indiabudget.gov.in/doc/bspeech/bs199394.pdf"),
    ("1994-95", "https://www.indiabudget.gov.in/doc/bspeech/bs199495.pdf"),
    ("1995-96", "https://www.indiabudget.gov.in/doc/bspeech/bs199596.pdf"),
    ("1996-97", "https://www.indiabudget.gov.in/doc/bspeech/bs199697.pdf"),
    ("1996-97-I", "https://www.indiabudget.gov.in/doc/bspeech/bs199697(I).pdf"),
    ("1997-98", "https://www.indiabudget.gov.in/doc/bspeech/bs199798.pdf"),
    ("1998-99", "https://www.indiabudget.gov.in/doc/bspeech/bs199899.pdf"),
    ("1998-99-I", "https://www.indiabudget.gov.in/doc/bspeech/bs199899(I).pdf"),
    ("1999-00", "https://www.indiabudget.gov.in/doc/bspeech/bs19992000.pdf"),
    ("2000-01", "https://www.indiabudget.gov.in/doc/bspeech/bs200001.pdf"),
    ("2001-02", "https://www.indiabudget.gov.in/doc/bspeech/bs200102.pdf"),
    ("2002-03", "https://www.indiabudget.gov.in/doc/bspeech/bs200203.pdf"),
    ("2003-04", "https://www.indiabudget.gov.in/doc/bspeech/bs200304.pdf"),
    ("2004-05", "https://www.indiabudget.gov.in/doc/bspeech/bs200405.pdf"),
    ("2004-05-I", "https://www.indiabudget.gov.in/doc/bspeech/bs200405(I).pdf"),
    ("2005-06", "https://www.indiabudget.gov.in/doc/bspeech/bs200506.pdf"),
    ("2006-07", "https://www.indiabudget.gov.in/doc/bspeech/bs200607.pdf"),
    ("2007-08", "https://www.indiabudget.gov.in/doc/bspeech/bs200708.pdf"),
    ("2011-12", "https://www.indiabudget.gov.in/doc/bspeech/bs201112.pdf"),
    ("2012-13", "https://www.indiabudget.gov.in/doc/bspeech/bs201213.pdf"),
    ("2013-14", "https://www.indiabudget.gov.in/doc/bspeech/bs201314.pdf"),
    ("2014-15", "https://www.indiabudget.gov.in/doc/bspeech/bs201415.pdf"),
    ("2015-16", "https://www.indiabudget.gov.in/doc/bspeech/bs201516.pdf"),
    ("2016-17", "https://www.indiabudget.gov.in/doc/bspeech/bs201617.pdf"),
    ("2017-18", "https://www.indiabudget.gov.in/doc/bspeech/bs201718.pdf"),
    ("2018-19", "https://www.indiabudget.gov.in/doc/bspeech/bs201819.pdf"),
    ("2019-20", "https://www.indiabudget.gov.in/doc/bspeech/bs201920.pdf"),
    ("2019-20-I", "https://www.indiabudget.gov.in/doc/bspeech/bs201920(I).pdf"),
    ("2020-21", "https://www.indiabudget.gov.in/doc/bspeech/bs202021.pdf"),
    ("2021-22", "https://www.indiabudget.gov.in/doc/bspeech/bs202122.pdf"),
    ("2022-23", "https://www.indiabudget.gov.in/doc/bspeech/bs202223.pdf"),
    ("2023-24", "https://www.indiabudget.gov.in/doc/bspeech/bs2023_24.pdf"),
    ("2024-25", "https://www.indiabudget.gov.in/doc/bspeech/bs2024_25.pdf"),
    ("2024-25-I", "https://www.indiabudget.gov.in/doc/bspeech/bs2024_25(I).pdf"),
    ("2025-26", "https://www.indiabudget.gov.in/doc/bspeech/bs2025_26.pdf"),
]

def download(year, url):
    filename = f"budget_speech_{year}.pdf"
    filepath = os.path.join(SAVE_DIR, filename)

    if os.path.exists(filepath):
        print(f"[Skip] {filename} already exists")
        return True

    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
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
for year, url in BUDGET_URLS:
    if download(year, url):
        ok += 1
    else:
        fail += 1
    time.sleep(0.5)

print(f"\nDone. Success: {ok} | Failed: {fail}")
print(f"Files saved to: {SAVE_DIR}")
