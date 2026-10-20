# MedMinder AI starter

A responsive MBBS study website with a Python FastAPI backend that calls Gemini server-side.

## Run locally
Install Python 3.11+.

Windows PowerShell:
```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

macOS/Linux:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Create an API key at https://aistudio.google.com/app/apikey. Put it in `.env` as `GEMINI_API_KEY=...`. Do not commit `.env` or paste the key into `index.html`.
Check current free-tier availability, quotas, model availability, and data-use terms:
https://ai.google.dev/gemini-api/docs/pricing

Run:
```bash
uvicorn main:app --reload
```
Open http://127.0.0.1:8000. Check http://127.0.0.1:8000/api/health.

## Deploy free (example: Render)
1. Create a private GitHub repository and upload the project files except `.env`.
2. In Render, choose New > Web Service and connect that repository.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. Choose Free if available.
6. Add `GEMINI_API_KEY`, `GEMINI_MODEL`, and `REQUESTS_PER_HOUR` in Render Environment settings.
7. Deploy and test the service URL and `/api/health`.

Render free services can sleep after inactivity and have other limitations. Review:
https://render.com/docs/free
https://render.com/docs/web-services

## Before sharing publicly
- This starter uses a simple in-memory rate limit. It resets on restart and is not robust public-service protection.
- There is no login. Anyone who finds the URL can try to use the AI endpoint and consume your provider quota. For a personal gift, add authentication/access control before sharing widely.
- Restrict the key to the Gemini API where available; rotate it if exposed.
- Never send identifiable patient information.
- AI can be wrong. Verify important facts against textbooks and faculty guidance. Not for diagnosis or treatment.
