import pandas as pd
import sqlite3

base = "raw_data"

print("Loading CSVs...")
lok = pd.read_csv(f"{base}/lok_sabha_all_elections.csv", low_memory=False)
vid = pd.read_csv(f"{base}/vidhan_sabha_all_elections.csv", low_memory=False)

print(f"Lok Sabha: {lok.shape}")
print(f"Vidhan Sabha: {vid.shape}")

conn = sqlite3.connect(f"{base}/elections.db")
lok.to_sql("lok_sabha", conn, if_exists="replace", index=False)
vid.to_sql("vidhan_sabha", conn, if_exists="replace", index=False)
conn.close()

print("Done. Saved to elections.db")
