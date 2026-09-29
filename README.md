# MailSentinel AI

AI-powered email intelligence platform: connects to Gmail, finds important emails, extracts
summaries / actions / deadlines with Groq, and notifies you on WhatsApp (official Cloud API).

> Status: **Phase 1** (project foundation). Auth, Gmail, Groq, WhatsApp, Celery, RAG come in later phases.

## Stack
React + Vite + Tailwind | FastAPI | MongoDB (Motor) | (later) Redis/Celery, Groq, ChromaDB

## Local setup

### Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env
uvicorn app.main:app --reload --port 8000
```
Open http://localhost:8000/health and http://localhost:8000/docs

### Frontend
```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```
Open http://localhost:5173

### Tests
```bash
cd backend && pytest -v
python -m scripts.test_mongo
```

### Docker
```bash
cp backend/.env.example backend/.env
docker compose up --build
```

## Security
Never commit `.env`. All secrets stay on the backend. See `.gitignore`.
