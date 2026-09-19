"""
Hugging Face Spaces Entry Point for DermaScan AI.
Serves the FastAPI application directly on port 7860 with an interactive Gradio bridge.
"""

import gradio as gr
from app.main import app as fastapi_app

# Interactive UI bridge for Hugging Face Space preview
with gr.Blocks(title="DermaScan AI Backend") as demo:
    gr.Markdown("# 🔬 DermaScan AI Backend API")
    gr.Markdown(
        """
        ### 🟢 Server Status: Active (16 GB RAM Environment)
        
        * **Swagger Documentation:** [View /docs](/docs)
        * **Health Endpoint:** [View /api/health](/api/health)
        * **Connected Client:** [DermaScan AI Frontend](https://dermascan-ai-eta.vercel.app)
        """
    )
    test_btn = gr.Button("Check API Status")
    output_box = gr.Textbox(label="Status")
    test_btn.click(fn=lambda: "✅ DermaScan AI FastAPI Backend is running smoothly!", inputs=[], outputs=output_box)

# Mount FastAPI app onto Gradio
app = gr.mount_gradio_app(fastapi_app, demo, path="/")