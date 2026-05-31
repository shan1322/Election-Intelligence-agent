import os
import json
import requests
import pandas as pd
import numpy as np
from agents.viz_prompt import VIZ_PROMPT

HF_TOKEN = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL = "meta-llama/Llama-3.1-8B-Instruct"

def call_llm(user_query: str, columns: list, sample_rows: list, row_count: int) -> dict:
    user_msg = f"""User query: {user_query}
Columns: {columns}
Row count: {row_count}
Sample rows (first 3): {json.dumps(sample_rows[:3], default=str)}

Decide visualization and write plotly code."""

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": VIZ_PROMPT},
            {"role": "user", "content": user_msg}
        ],
        "max_tokens": 1000,
        "temperature": 0.1
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()
    try:
        start = raw.find("{")
        end = raw.rfind("}") + 1
        return json.loads(raw[start:end])
    except Exception as e:
        print(f"[Viz] Parse error: {e}")
        return {"should_visualize": False, "reason": "parse error"}

def sanitize_df(df: pd.DataFrame) -> pd.DataFrame:
    """Convert all numpy types to plain Python types so Plotly uses JSON not binary."""
    df = df.copy()
    for col in df.columns:
        if pd.api.types.is_integer_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].isna(), df[col].apply(lambda x: int(x)))
        elif pd.api.types.is_float_dtype(df[col]):
            df[col] = df[col].astype(object).where(df[col].isna(), df[col].apply(lambda x: float(x)))
        else:
            df[col] = df[col].astype(str)
    return df

def execute_viz_code(code: str, df: pd.DataFrame) -> str | None:
    df = sanitize_df(df)
    local_vars = {"df": df, "chart_json": None}
    try:
        exec(code, {"pd": pd, "np": np, "__import__": __import__}, local_vars)
        return local_vars.get("chart_json")
    except Exception as e:
        print(f"[Viz] Code execution error: {e}")
        return None

def ask_visualization(user_query: str, df: pd.DataFrame) -> dict:
    print(f"\n[Viz] Query: {user_query}")
    print(f"[Viz] DataFrame shape: {df.shape}")

    if df.empty:
        return {"should_visualize": False, "reason": "empty dataframe"}

    columns = list(df.columns)
    sample_rows = df.head(3).to_dict(orient="records")
    row_count = len(df)

    decision = call_llm(user_query, columns, sample_rows, row_count)
    print(f"[Viz] Decision: {decision.get('should_visualize')} — {decision.get('reason')}")

    if not decision.get("should_visualize"):
        return {"should_visualize": False, "reason": decision.get("reason")}

    code = decision.get("code", "")
    if not code:
        return {"should_visualize": False, "reason": "no code generated"}

    chart_json = execute_viz_code(code, df)

    if chart_json:
        print("[Viz] Chart created successfully")
        # Verify no binary encoding
        if "bdata" in chart_json:
            print("[Viz] WARNING: binary data detected, chart may not render in browser")
        return {
            "should_visualize": True,
            "chart_type": decision.get("chart_type"),
            "chart_json": chart_json,
            "reason": decision.get("reason")
        }

    return {"should_visualize": False, "reason": "code execution failed"}
