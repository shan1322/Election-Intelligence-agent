import os
import sys
sys.path.insert(0, '/home/user/app')

import json
import sqlite3
import requests
import pandas as pd
from typing import TypedDict
from langgraph.graph import StateGraph, END

from agents.sql_agent import call_llm as sql_llm
from agents.wikipedia_agent import ask_wikipedia
from agents.news_agent import ask_news
from agents.rag_agent import ask_rag
from agents.visualization_agent import ask_visualization
from agents.supervisor_prompt import SUPERVISOR_PROMPT

HF_TOKEN   = os.getenv("HF_TOKEN", "")
HF_API_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL      = "meta-llama/Llama-3.1-8B-Instruct"
DB_PATH    = "raw_data/elections.db"

# ─── STATE ────────────────────────────────────────────────────────────────────

class AgentState(TypedDict):
    query          : str
    agents_to_call : list
    sql_result     : dict
    wiki_result    : dict
    news_result    : dict
    rag_result     : dict
    viz_result     : dict
    final_answer   : str

# ─── SUPERVISOR ───────────────────────────────────────────────────────────────

def supervisor_node(state: AgentState) -> AgentState:
    print(f"\n[Supervisor] Query: {state['query']}")
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SUPERVISOR_PROMPT},
            {"role": "user", "content": state["query"]}
        ],
        "max_tokens": 50,
        "temperature": 0.0
    }
    raw = requests.post(HF_API_URL, headers=headers, json=payload, timeout=30)
    raw = raw.json()["choices"][0]["message"]["content"].strip()
    try:
        agents = json.loads(raw[raw.find("["):raw.rfind("]")+1])
    except:
        agents = ["sql_agent"]
    print(f"[Supervisor] Will call: {agents}")
    return {**state, "agents_to_call": agents}

# ─── SQL NODE ─────────────────────────────────────────────────────────────────

def extract_first_sql(raw_sql: str) -> str:
    statements = [s.strip() for s in raw_sql.split(";") if s.strip()]
    return statements[0] + ";" if statements else raw_sql

def sql_node(state: AgentState) -> AgentState:
    if "sql_agent" not in state["agents_to_call"]:
        print("[SQL Node] Skipped")
        return state
    print("[SQL Node] Running...")
    try:
        sql = extract_first_sql(sql_llm(state["query"]))
        print(f"[SQL Node] SQL: {sql}")
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(sql, conn)
        conn.close()
        return {**state, "sql_result": {
            "sql": sql,
            "rows": df.head(10).to_dict(orient="records"),
            "df": df,
            "count": len(df)
        }}
    except Exception as e:
        print(f"[SQL Node] Error: {e}")
        return {**state, "sql_result": {"error": str(e)}}

# ─── VISUALIZATION NODE ───────────────────────────────────────────────────────
# Runs after sql_node because it needs sql_result["df"] to be in state.
# Checks if SQL ran successfully and result has enough data to visualize.

def viz_node(state: AgentState) -> AgentState:
    sql_result = state.get("sql_result", {})
    if not sql_result or sql_result.get("error") or "df" not in sql_result:
        print("[Viz Node] Skipped — no SQL result")
        return {**state, "viz_result": {"should_visualize": False}}
    print("[Viz Node] Running...")
    result = ask_visualization(state["query"], sql_result["df"])
    return {**state, "viz_result": result}

# ─── WIKIPEDIA NODE ───────────────────────────────────────────────────────────

def wikipedia_node(state: AgentState) -> AgentState:
    if "wikipedia_agent" not in state["agents_to_call"]:
        print("[Wikipedia Node] Skipped")
        return state
    print("[Wikipedia Node] Running...")
    result = ask_wikipedia(state["query"])
    return {**state, "wiki_result": result}

# ─── NEWS NODE ────────────────────────────────────────────────────────────────

def news_node(state: AgentState) -> AgentState:
    if "news_agent" not in state["agents_to_call"]:
        print("[News Node] Skipped")
        return state
    print("[News Node] Running...")
    result = ask_news(state["query"])
    return {**state, "news_result": result}

# ─── RAG NODE ─────────────────────────────────────────────────────────────────

def rag_node(state: AgentState) -> AgentState:
    if "rag_agent" not in state["agents_to_call"]:
        print("[RAG Node] Skipped")
        return state
    print("[RAG Node] Running...")
    result = ask_rag(state["query"])
    return {**state, "rag_result": result}

# ─── SYNTHESIS NODE ───────────────────────────────────────────────────────────

def synthesis_node(state: AgentState) -> AgentState:
    print("[Synthesis] Combining results...")
    context = f"User question: {state['query']}\n\n"
    sources = []

    if state.get("sql_result") and not state["sql_result"].get("error"):
        context += f"ELECTION DATA:\n{json.dumps(state['sql_result']['rows'], default=str)}\n\n"
        sources.append("Election Database (Lok Dhaba)")

    if state.get("wiki_result"):
        wiki = state["wiki_result"]
        wiki_text = wiki.get("context") or wiki.get("summary", "")
        if wiki_text:
            context += f"BACKGROUND (Wikipedia - {wiki.get('title','')}):\n{wiki_text[:800]}\n\n"
        if wiki.get("url"):
            sources.append(f"Wikipedia: {wiki['url']}")

    if state.get("news_result") and state["news_result"].get("context"):
        context += f"RECENT NEWS:\n{state['news_result']['context'][:500]}\n\n"
        for s in state["news_result"].get("sources", [])[:3]:
            sources.append(f"{s['title']} — {s['url']}")

    if state.get("rag_result") and state["rag_result"].get("answer"):
        context += f"POLICY/SPEECH CONTEXT:\n{state['rag_result']['answer'][:500]}\n\n"
        sources += state["rag_result"].get("sources", [])

    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are an Indian election expert. Rules: 1) Use ONLY data provided in context — never invent or assume facts. 2) If election data is provided, summarize it accurately with exact numbers. 3) If no relevant data is in context, say exactly: I do not have enough data to answer this. 4) Never hallucinate names, numbers or events. 5) Be concise and specific. 6) Cite sources at end."},
            {"role": "user", "content": context}
        ],
        "max_tokens": 1200,
        "temperature": 0.2
    }
    response = requests.post(HF_API_URL, headers=headers, json=payload, timeout=60)
    answer = response.json()["choices"][0]["message"]["content"].strip()
    answer += f"\n\nSources: {', '.join(sources)}"
    return {**state, "final_answer": answer}

# ─── BUILD GRAPH ──────────────────────────────────────────────────────────────
# Order: supervisor → sql → viz → wikipedia → news → rag → synthesis → END
# viz runs right after sql because it needs sql_result["df"]
# all other agents are independent — order between them doesnt matter

def build_graph():
    graph = StateGraph(AgentState)

    graph.add_node("supervisor",     supervisor_node)
    graph.add_node("sql_node",       sql_node)
    graph.add_node("viz_node",       viz_node)
    graph.add_node("wikipedia_node", wikipedia_node)
    graph.add_node("news_node",      news_node)
    graph.add_node("rag_node",       rag_node)
    graph.add_node("synthesis",      synthesis_node)

    graph.set_entry_point("supervisor")
    graph.add_edge("supervisor",     "sql_node")
    graph.add_edge("sql_node",       "viz_node")
    graph.add_edge("viz_node",       "wikipedia_node")
    graph.add_edge("wikipedia_node", "news_node")
    graph.add_edge("news_node",      "rag_node")
    graph.add_edge("rag_node",       "synthesis")
    graph.add_edge("synthesis",      END)

    return graph.compile()

GRAPH = build_graph()

def ask(query: str) -> dict:
    result = GRAPH.invoke({
        "query"          : query,
        "agents_to_call" : [],
        "sql_result"     : {},
        "wiki_result"    : {},
        "news_result"    : {},
        "rag_result"     : {},
        "viz_result"     : {},
        "final_answer"   : ""
    })
    return {
        "answer" : result["final_answer"],
        "sql"    : result.get("sql_result", {}).get("sql", ""),
        "viz"    : result.get("viz_result", {}),
        "rows"   : result.get("sql_result", {}).get("rows", [])
    }

if __name__ == "__main__":
    queries = [
        "Who won Varanasi in 2019?",
        "What did the 2019 budget say about farmers?",
        "Tell me about Narendra Modi latest news",
        "Who won Varanasi in 2019 and what is its history?",
    ]
    for q in queries:
        print(f"\n{'='*60}")
        result = ask(q)
        print(f"\nANSWER:\n{result['answer']}")
