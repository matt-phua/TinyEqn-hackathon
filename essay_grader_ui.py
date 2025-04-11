import gradio as gr
import requests
import io
from PIL import Image

# ---- ECS Backend Endpoint ----
API_URL = "http://8.222.167.185:8000/evaluate"

# ---- Function to Call FastAPI Server ----
def evaluate_with_backend(image: Image.Image):
    buffered = io.BytesIO()
    image.save(buffered, format="JPEG")
    buffered.seek(0)

    try:
        response = requests.post(API_URL, files={"file": buffered})
        if response.status_code == 200:
            result = response.json()
            print(result.get("feedback"))
            # Format the band scores and feedback
            feedback = "**Feedback:**\n\n" + result.get("feedback", "No feedback provided.")

            # Convert annotated image bytes if included
            if "annotated_image" in result:
                annotated_image_data = requests.get(result["annotated_image"]).content
                annotated_image = Image.open(io.BytesIO(annotated_image_data))
            else:
                annotated_image = image  # fallback to original

            return feedback, annotated_image
        else:
            return f"❌ Server error: {response.status_code}", image
    except Exception as e:
        return f"❌ Request failed: {e}", image

# ---- Gradio Interface ----
with gr.Blocks(title="RAME Essay Marker UI") as demo:
    gr.Markdown("""
    # 🧠 RAME Essay Grading Assistant
    Upload a photo of a handwritten essay.  
    Get band scores, personalized feedback, and visual marking on your uploaded paper.
    """)

    with gr.Row():
        image_input = gr.Image(
            label="📷 Upload or Take Essay Photo",
            type="pil"
        )

    submit_btn = gr.Button("🧪 Evaluate Essay")

    gr.Markdown("### 💬 AI Feedback & Scores")
    feedback_box = gr.Markdown("_(Your feedback will appear here...)_")

    gr.Markdown("### 🖼️ Marked Essay (Annotated Image)")
    annotated_image = gr.Image(label="Annotated Essay")

    submit_btn.click(fn=evaluate_with_backend, inputs=image_input, outputs=[feedback_box, annotated_image])

demo.launch()
