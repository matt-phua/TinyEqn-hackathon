from fastapi import FastAPI, UploadFile, File
import shutil
from ocr_vl import extract_text, sent_to_agent, change_to_json, annotate_essay_image,extract_non_json_text

app = FastAPI()

@app.post("/evaluate")
async def evaluate(file: UploadFile = File(...)):
    temp_path = "temp.jpg"
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 1: Extract text using Qwen-VL OCR
    lines = extract_text(temp_path)
    clean_text = lines.encode().decode('unicode_escape')
    flattened = clean_text.replace('\n', ' ').strip()

    # Step 2: Send to LLM agent and parse output
    output = sent_to_agent(flattened)
    without_json=extract_non_json_text(output)
    json_data = change_to_json(output)

    if not json_data:
        return {"error": "? Could not parse grading output."}

    result_1 = {
        "full_text": json_data,
        "flattened": lines
    }

    # Step 3: Annotate image and upload to OSS
    annotated_url = annotate_essay_image(temp_path, result_1)

    # Step 4: Return structured response to frontend
    return {
        "feedback": without_json,
        "annotated_image": annotated_url
    }
