import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import pandas as pd
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn
from graph.workflow import ask

app = FastAPI()

class Query(BaseModel):
    question: str

@app.post("/ask")
async def ask_question(query: Query):
    try:
        result = ask(query.question)
        answer = result.get("answer", "")
        sql = result.get("sql", "")
        viz = result.get("viz", {})
        rows = result.get("rows", [])

        trace = []
        if sql:
            trace.append("✅ SQL Agent — queried election database")
        if "Wikipedia" in answer:
            trace.append("✅ Wikipedia Agent — fetched background")
        if "news" in answer.lower():
            trace.append("✅ News Agent — fetched recent news")
        if "Budget" in answer or "President" in answer:
            trace.append("✅ RAG Agent — searched speeches")
        if viz.get("should_visualize"):
            trace.append(f"✅ Visualization Agent — {viz.get('chart_type', '')} chart")

        table = ""
        if rows:
            df = pd.DataFrame(rows)
            table = df.to_html(index=False, classes="data-table", border=0)

        chart_json = viz.get("chart_json", "") if viz.get("should_visualize") else ""

        return JSONResponse({
            "answer": answer,
            "sql": sql,
            "trace": "\n".join(trace),
            "table": table,
            "chart_json": chart_json
        })
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

@app.get("/", response_class=HTMLResponse)
async def index():
    return HTMLResponse(open("ui/index.html").read())

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
