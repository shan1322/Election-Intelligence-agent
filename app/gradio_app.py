import sys
sys.path.insert(0, '/workspaces/codespaces-blank/election-intelligence')

import json
import sqlite3
import pandas as pd
import gradio as gr
from agents.sql_agent import ask, call_llm, run_sql
from agents.visualization_agent import ask_visualization

DB = "/workspaces/codespaces-blank/election-intelligence/raw_data/elections.db"

def query(user_input):
    if not user_input.strip():
        return "Please enter a question.", "", None

    # Step 1: Get SQL from LLM
    sql = call_llm(user_input)
    print(f"SQL: {sql}")

    # Step 2: Run SQL
    try:
        conn = sqlite3.connect(DB)
        df = pd.read_sql_query(sql, conn)
        conn.close()
    except Exception as e:
        return f"SQL Error: {e}", sql, None

    if df.empty:
        return "No results found.", sql, None

    # Step 3: Format table
    table = df.head(20).to_markdown(index=False)
    if len(df) > 20:
        table += f"\n\n*Showing 20 of {len(df)} rows*"

    # Step 4: Try visualization
    viz_result = ask_visualization(user_input, df)
    chart = None
    if viz_result.get("should_visualize") and viz_result.get("chart_json"):
        import plotly.io as pio
        chart = pio.from_json(viz_result["chart_json"])

    return table, sql, chart

with gr.Blocks(title="India Election Intelligence") as app:
    gr.Markdown("# 🗳️ India Election Intelligence Agent")
    gr.Markdown("Ask anything about Indian elections from 1962 to 2019.")

    with gr.Row():
        inp = gr.Textbox(
            placeholder="e.g. Show voting turnout history of Varanasi",
            label="Your Question",
            lines=2
        )
        btn = gr.Button("Ask", variant="primary")

    with gr.Row():
        out = gr.Markdown(label="Results")

    with gr.Row():
        chart_out = gr.Plot(label="Visualization")

    with gr.Accordion("Generated SQL", open=False):
        sql_out = gr.Code(language="sql", label="SQL Query")

    gr.Examples(
        examples=[
            ["Show voting turnout history of Varanasi"],
            ["How many seats did each party win in 2019 Lok Sabha?"],
            ["BJP vs INC vote share trend in UP Lok Sabha"],
            ["Who won Varanasi in 2019?"],
            ["Show Rahul Gandhi election history"],
            ["Closest contests in Maharashtra 2019 Vidhan Sabha"],
            ["How many women won in 2019 Lok Sabha?"],
            ["Which party won most seats state wise in 2014?"],
        ],
        inputs=inp
    )

    btn.click(fn=query, inputs=inp, outputs=[out, sql_out, chart_out])
    inp.submit(fn=query, inputs=inp, outputs=[out, sql_out, chart_out])

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7890, share=False)
