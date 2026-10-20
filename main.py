import os
import time
from collections import defaultdict, deque
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

load_dotenv()
BASE_DIR = Path(__file__).resolve().parent
API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
REQUESTS_PER_HOUR = int(os.getenv("REQUESTS_PER_HOUR", "12"))

app = FastAPI(title="MedMinder")
request_times = defaultdict(deque)

SYSTEM_INSTRUCTION = """
You are MedMinder, a careful educational tutor for a first-year MBBS student.
This is for learning, not diagnosis or treatment of real patients.
Start simply, then use correct medical terminology. Use concise headings and bullets.
For topics, explain definition, mechanism, key facts, and exam/viva relevance.
For MCQs, put answers and explanations after the questions unless asked otherwise.
Never invent sources, citations, page numbers, or certainty. Say when unsure.
Encourage checking important details against faculty guidance and recommended textbooks.
Do not ask for or encourage identifiable patient data. For real symptoms or treatment,
explain that this is not a clinician and recommend appropriate professional care.
"""

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=5000)
    subject: str = Field(default="General", max_length=80)
    history: list[dict[str, str]] = Field(default_factory=list, max_length=8)

class ChatResponse(BaseModel):
    answer: str
    model: str

def enforce_rate_limit(request: Request):
    # Starter-only limit. For a real public service use trusted proxy configuration
    # and a shared rate-limit store/service.
    host = request.client.host if request.client else "unknown"
    now = time.time()
    queue = request_times[host]
    while queue and now - queue[0] > 3600:
        queue.popleft()
    if len(queue) >= REQUESTS_PER_HOUR:
        raise HTTPException(status_code=429, detail="Study-chat limit reached for now. Try again later.")
    queue.append(now)

@app.get("/api/health")
def health():
    return {"ok": True, "model_configured": bool(API_KEY), "model": MODEL_NAME}

@app.post("/api/chat", response_model=ChatResponse)
def chat(payload: ChatRequest, request: Request):
    enforce_rate_limit(request)
    if not API_KEY:
        raise HTTPException(status_code=503, detail="AI is not configured. Add GEMINI_API_KEY to the server environment.")
    message = payload.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Please enter a question.")

    history_lines = []
    for item in payload.history[-8:]:
        role, content = item.get("role", ""), item.get("content", "")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            history_lines.append(("Student" if role == "user" else "MedMinder") + ": " + content.strip()[:1500])
    prompt = (
        f"Subject selected by student: {payload.subject}\n\n"
        f"Recent conversation:\n{chr(10).join(history_lines)}\n\n"
        f"Student's current question:\n{message}\n\n"
        "Answer as an educational tutor. Do not claim to have checked external sources "
        "unless source material was provided."
    )
    try:
        client = genai.Client(api_key=API_KEY)
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.25,
                max_output_tokens=2500,
            ),
        )
        answer = (response.text or "").strip()
        if not answer:
            raise HTTPException(status_code=502, detail="The AI returned an empty answer. Try again.")
        return ChatResponse(answer=answer, model=MODEL_NAME)
    except HTTPException:
        raise
    
    except Exception as e:
        print(f"MedMinder AI error: {type(e).__name__}: {e}")
        raise HTTPException(
            status_code=502,
            detail="AI request failed. Check the VS Code terminal."
        )

@app.get("/")
def index():
    return FileResponse(BASE_DIR / "index.html")
