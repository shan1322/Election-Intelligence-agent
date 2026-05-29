import sys
sys.path.insert(0, '/workspaces/codespaces-blank/election-intelligence')

import gradio as gr
from agents.sql_agent import ask

def query(user_input):
    if not user_input.strip():
        return "Please enter a question.", ""
    
    result = ask(user_input)
    sql = result.get("sql", "")
    
    if "error" in result:
        return f"Error: {result['error']}\n\nSQL attempted:\n{sql}", sql
    
    rows = result.get("results", [])
    if not rows:
        return "No results found.", sql
    
    # Format results as markdown table
    headers = list(rows[0].keys())
    table = "| " + " | ".join(headers) + " |\n"
    table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
    for row in rows[:20]:
        table += "| " + " | ".join([str(row.get(h, "")) for h in headers]) + " |\n"
    
    if len(rows) > 20:
        table += f"\n*Showing 20 of {len(rows)} results*"
    
    return table, sql

with gr.Blocks(title="India Election Intelligence") as app:
    gr.Markdown("# 🗳️ India Election Intelligence Agent")
    gr.Markdown("Ask anything about Indian elections from 1962 to 2019.")
    
    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                placeholder="e.g. Who won Varanasi in 2019? or How many seats did BJP win in 2014?",
                label="Your Question",
                lines=2
            )
            btn = gr.Button("Ask", variant="primary")
        
    with gr.Row():
        out = gr.Markdown(label="Results")
    
    with gr.Accordion("Generated SQL", open=False):
        sql_out = gr.Code(language="sql", label="SQL Query")
    
    gr.Examples(
        examples=[
            ["Who won Varanasi in 2019?"],
            ["How many seats did BJP win in 2019 Lok Sabha?"],
            ["Show Rahul Gandhi election history"],
            ["Which party won most seats in UP 2022 Vidhan Sabha?"],
            ["How many women won in 2019 Lok Sabha?"],
            ["Which constituency had highest winning margin in 2014?"],
            ["Who has won the most Lok Sabha elections ever?"],
            ["Closest contests in Maharashtra 2019 Vidhan Sabha"],
        ],
        inputs=inp
    )
    
    btn.click(fn=query, inputs=inp, outputs=[out, sql_out])
    inp.submit(fn=query, inputs=inp, outputs=[out, sql_out])

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
