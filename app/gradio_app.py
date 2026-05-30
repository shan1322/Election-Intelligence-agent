import sys
sys.path.insert(0, '/workspaces/codespaces-blank/election-intelligence')

import json
import gradio as gr
from graph.workflow import ask, GRAPH

def run_query(user_input):
    if not user_input.strip():
        return "Please enter a question.", "", "", None

    result = ask(user_input)

    answer = result.get("answer", "No answer generated.")
    sql = result.get("sql", "")
    viz = result.get("viz", {})

    # Agent trace
    trace = "Agents called this query:\n\n"
    # Re-run supervisor just for display — read from result
    if sql:
        trace += "✅ SQL Agent — queried election database\n"
    if "Wikipedia" in answer:
        trace += "✅ Wikipedia Agent — fetched background\n"
    if "News" in answer or "news" in answer.lower():
        trace += "✅ News Agent — fetched recent news\n"
    if "Budget" in answer or "President" in answer:
        trace += "✅ RAG Agent — searched speeches\n"
    if viz.get("should_visualize"):
        trace += f"✅ Visualization Agent — created {viz.get('chart_type', '')} chart\n"

    # Chart
    chart = None
    if viz.get("should_visualize") and viz.get("chart_json"):
        import plotly.io as pio
        chart = pio.from_json(viz["chart_json"])

    return answer, sql, trace, chart


with gr.Blocks(title="India Election Intelligence", theme=gr.themes.Soft()) as app:

    gr.Markdown("# 🗳️ India Election Intelligence Agent")
    gr.Markdown("Multi-agent system powered by LangGraph — SQL + Wikipedia + News + RAG + Visualization")

    with gr.Row():
        with gr.Column(scale=3):
            inp = gr.Textbox(
                placeholder="e.g. Who won Varanasi in 2019 and what is its history?",
                label="Ask anything about Indian elections",
                lines=2
            )
            btn = gr.Button("Ask", variant="primary", size="lg")

            gr.Examples(
                examples=[
                    ["Who won Varanasi in 2019?"],
                    ["Show voter turnout trend in Varanasi across all elections"],
                    ["Tell me about Narendra Modi"],
                    ["What did the 2019 budget say about farmers?"],
                    ["BJP vs INC seats in 2019 Lok Sabha"],
                    ["Who won Varanasi in 2019 and what is its history?"],
                    ["Latest news about Rahul Gandhi"],
                    ["Defence spending in budget speeches over the years"],
                ],
                inputs=inp
            )

        with gr.Column(scale=2):
            trace_out = gr.Textbox(
                label="🤖 Agents Called",
                lines=8,
                interactive=False
            )
            sql_out = gr.Code(
                language="sql",
                label="Generated SQL",
            )

    with gr.Row():
        answer_out = gr.Markdown(label="Answer")

    with gr.Row():
        chart_out = gr.Plot(label="Visualization")

    btn.click(
        fn=run_query,
        inputs=inp,
        outputs=[answer_out, sql_out, trace_out, chart_out]
    )
    inp.submit(
        fn=run_query,
        inputs=inp,
        outputs=[answer_out, sql_out, trace_out, chart_out]
    )

if __name__ == "__main__":
    app.launch(server_name="0.0.0.0", server_port=7860, share=False)
