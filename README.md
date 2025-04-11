# Tiny Equations - Vision-Integrated Scoring & Text Annotation (VISTA)

This project is a full-stack handwritten essay grading system built for the Alibaba Cloud x KrASIA Hackathon. It allows users to upload a photo of an essay, processes it using OCR and LLM agents, and returns **band scores**, **annotated feedback**, and a **visually marked essay**.

---

## 🚀 Features

- 📸 Upload handwritten essays
- 🔍 Extract raw text using OCR + Vision LLM
- 🤖 Evaluate essays via DashScope Agent API
- ✍️ Annotate image with strengths and areas of improvement
- 🌐 Gradio-based frontend + FastAPI backend
- ☁️ Image uploads & annotations handled with OSS (Alibaba Cloud)

---

## 📁 Project Structure

```
TinyEqn-hackathon/
├── app.py                    
├── essay_grader_ui.py        
├── ocr_vl.py                 
├── PromptSampleLibrary.xlsx 
├── TinyEquations Presentation Slides.pdf
├── .gitignore
└── README.md               
```

---

## ⚙️ Setup

### 1. Clone the Repository

```bash
git clone https://github.com/matt-phua/TinyEqn-hackathon.git
cd TinyEqn-hackathon
```

### 2. Install Dependencies

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

Install requirements:

```bash
pip install -r requirements.txt
```

### Sample `requirements.txt`

```
gradio
fastapi
uvicorn
paddleocr
oss2
openai
dashscope
opencv-python
numpy
```

---

## 🧪 Running Locally

### Start Backend API

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```
**Also You'll need to run this on ECS server**

This will start the backend at `http://localhost:8000/evaluate`.

### Launch Frontend (Gradio)

```bash
python essay_grader_ui.py
```

Visit: `http://127.0.0.1:7860/` in your browser.

---

## ☁️ Deploying on Alibaba Cloud ECS

### 🖥️ ECS Setup Steps

1. **Create ECS instance** (Ubuntu 20.04 or 22.04)
2. **Allow Ports**: Open ports `8000` (API) and `7860` (UI) in the security group
3. **SSH into instance**:

```bash
ssh root@<your-ecs-ip>
```

4. **Install Python & Git**:

```bash
sudo apt update
sudo apt install python3-pip git
```

5. **Clone the Repo**:

```bash
git clone https://github.com/<your-username>/TinyEqn-hackathon.git
cd TinyEqn-hackathon
```

6. **Install Python Libraries**:

```bash
pip3 install -r requirements.txt
```

7. **Run Backend**:

```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

8. **Run Frontend**:

```bash
python3 essay_grader_ui.py
```

Access:
- `http://<your-ecs-ip>:8000/evaluate` → API endpoint
- `http://<your-ecs-ip>:7860/` → Gradio UI

---

## 🧠 How It Works

1. User uploads essay image
2. Image is sent to FastAPI backend
3. OCR + Vision LLM (Qwen-VL) extract the handwritten text
4. Essay is passed to DashScope Agent for feedback and band scores
5. Annotated image with highlights is generated
6. Final feedback and image are returned to the frontend UI

---

## 🔐 Environment Variables (optional)

Replace sensitive values like API keys with environment variables or a `.env` file.

```env
OSS_ACCESS_KEY_ID=xxx
OSS_ACCESS_KEY_SECRET=xxx
DASHSCOPE_API_KEY=xxx
DASHSCOPE_APP_ID=xxx
```

---

## 🖼️ Demo Workflow

1. Upload a handwritten essay
2. Click "🧪 Evaluate Essay"
3. See:
   - AI-generated feedback
   - Annotated image with highlights

---

## 📄 License

The contents in this repo are intended solely for Tiny Equations' participation in the Alibaba Cloud Singapore Hackathon 2025.
```

