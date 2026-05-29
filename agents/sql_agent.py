import sqlite3
import requests
import os
from agents.sql_prompt import SYSTEM_PROMPT

DB_PATH = "/workspaces/codespaces-blank/election-intelligence/raw_data/elections.db"
HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "meta-llama/Llama-3.1-8B-Instruct"

def call_llm(user_query: str) -> str:
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_query}
        ],
        "max_tokens": 200,
        "temperature": 0.1
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"].strip()

def run_sql(sql: str) -> list:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def ask(user_query: str) -> dict:
    print(f"\nQuery: {user_query}")
    print("Generating SQL...")
    sql = call_llm(user_query)
    print(f"SQL: {sql}")
    try:
        results = run_sql(sql)
        print(f"Results: {len(results)} rows")
        for r in results[:5]:
            print(r)
        return {"sql": sql, "results": results}
    except Exception as e:
        print(f"SQL Error: {e}")
        return {"sql": sql, "error": str(e)}

if __name__ == "__main__":
    queries = [
        "Who won Varanasi in 2019?",
        "How many seats did BJP win in 2019 Lok Sabha?",
        "Show Rahul Gandhi election history",
        "Which party won most seats in UP 2022 Vidhan Sabha?",
        "How many women won in 2019 Lok Sabha?"
    ]
    for q in queries:
        ask(q)
        print("-" * 50)
