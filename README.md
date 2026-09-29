# 🛡️ MailSentinel AI

> **Next-Generation Multi-User AI Email Intelligence & Actionable WhatsApp Notification SaaS Platform.**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3+-61DAFB.svg?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4+-646CFF.svg?logo=vite&logoColor=white)](https://vitejs.dev)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind_CSS-3.4+-38B2AC.svg?logo=tailwind-css&logoColor=white)](https://tailwindcss.com)
[![MongoDB](https://img.shields.io/badge/MongoDB-7.0+-47A248.svg?logo=mongodb&logoColor=white)](https://www.mongodb.com)
[![Groq](https://img.shields.io/badge/Groq-Llama_3.3_70B-F55036.svg?logo=groq&logoColor=white)](https://groq.com)
[![ChromaDB](https://img.shields.io/badge/ChromaDB-Vector_RAG-orange.svg)](https://www.trychroma.com)
[![Celery](https://img.shields.io/badge/Celery-5.4+-37814A.svg?logo=celery&logoColor=white)](https://docs.celeryq.dev)
[![WhatsApp Cloud API](https://img.shields.io/badge/WhatsApp-Cloud_API-25D366.svg?logo=whatsapp&logoColor=white)](https://developers.facebook.com/docs/whatsapp/cloud-api)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)](https://www.docker.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## 📌 1. Product Overview

**MailSentinel AI** is a production-ready, multi-tenant SaaS application that continuously ingests unread emails via **Google OAuth 2.0 / Gmail API**, filters noise through a multi-stage cost-optimized pipeline, classifies importance with **Groq LLM (`llama-3.3-70b-versatile`)**, extracts critical **deadlines & required action items**, delivers instant structured alerts to the user's **WhatsApp**, and allows two-way conversational queries via **ChromaDB Vector RAG**.

---

## 🏗️ 2. High-Level Architecture

```text
                                 ┌─────────────────────────┐
                                 │   Gmail OAuth 2.0 API   │
                                 └────────────┬────────────┘
                                              │ (Ingest unread messages)
                                              ▼
┌──────────────────┐            ┌──────────────────────────┐
│   React / Vite   │ ◄────────► │     FastAPI Backend      │ ◄────────► [ MongoDB Atlas ]
│   Tailwind UI    │  JWT Auth  │   (Clean Architecture)   │              - users, emails
└──────────────────┘            └─────────────┬────────────┘              - threads, notifications
                                              │                           - preferences
                      ┌───────────────────────┼───────────────────────┐
                      ▼                       ▼                       ▼
            ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
            │   Groq GenAI     │    │ Celery + Redis   │    │  Meta WhatsApp   │
            │   Pipeline       │    │  Background      │    │  Cloud API       │
            │ (Classification, │    │  Orchestration   │    │ (Alerts + Two-Way│
            │  Scoring, Extr.) │    │  & Schedulers    │    │  Bot Webhooks)   │
            └──────────────────┘    └──────────────────┘    └──────────────────┘
                      │                                               ▲
                      ▼                                               │
            ┌──────────────────┐                                      │
            │ ChromaDB Vector  │ ─────────────────────────────────────┘
            │ User-Isolated RAG│  (Query historical inbox context via WhatsApp / UI)
            └──────────────────┘
```

---

## ✨ 3. Core Features Across Phases

| Phase | Feature | Highlights |
|---|---|---|
| **Phase 1-2** | **Multi-Tenant Foundation & Auth** | JWT auth, Bcrypt hashing, Argon2/crypto token encryption, strict user isolation. |
| **Phase 3-4** | **Gmail OAuth & Ingestion** | Official Google OAuth 2.0, token refresh lifecycle, email normalization, deduplication. |
| **Phase 5** | **Groq GenAI Intelligence** | Hybrid rule + LLM classifier, structured JSON schemas, deadline parser, action extractor. |
| **Phase 6** | **WhatsApp Cloud Dispatcher** | Official WhatsApp Cloud API provider, idempotency hashes, customizable notification limits. |
| **Phase 7** | **Background Automation** | Celery task queues, Redis broker, Celery Beat recurring 5-minute automated sync. |
| **Phase 8** | **Executive SaaS Dashboard** | Key metrics (Deadlines, Urgent emails, Stats), timeline views, categorized filtering. |
| **Phase 9** | **ChromaDB Vector RAG** | Multi-user vector partitioning (`user_id` filtering), semantic email search, Ask AI interface. |
| **Phase 10** | **Conversational WhatsApp Bot** | Meta Webhook challenges, inbound parsing, intent router, conversational RAG & UI simulator. |
| **Phase 11** | **Production & Security Hardening**| Multi-stage Docker & Compose, Nginx SPA proxy, correlation IDs, sensitive log redactor. |

---

## 📁 4. Project Directory Structure

```text
mailsentinel-ai/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI application factory & middleware
│   │   ├── core/
│   │   │   ├── config.py               # Pydantic Settings & environment variables
│   │   │   ├── database.py             # Motor MongoDB connection manager
│   │   │   ├── security.py             # JWT token and password hashing utilities
│   │   │   ├── encryption.py           # Fernet encryption for OAuth tokens at rest
│   │   │   └── logging_config.py       # Production structured & redacted logging
│   │   ├── models/                     # Data schemas & domain models
│   │   ├── api/                        # Modular FastAPI route controllers
│   │   │   ├── auth.py                 # Registration & Login endpoints
│   │   │   ├── gmail.py                # Google OAuth handshake & disconnect
│   │   │   ├── emails.py               # Email listing & ingestion triggers
│   │   │   ├── ai.py                   # Groq classification & extraction endpoints
│   │   │   ├── rag.py                  # Semantic search & inbox RAG Q&A
│   │   │   ├── notifications.py        # WhatsApp notification logs & dispatch
│   │   │   ├── settings.py             # User preferences & threshold configuration
│   │   │   ├── webhook.py              # Meta WhatsApp webhook challenge & listener
│   │   │   └── health.py               # Healthcheck & ping
│   │   ├── services/                   # Business logic layer
│   │   │   ├── user_service.py         # User management
│   │   │   ├── gmail_service.py        # Gmail API client
│   │   │   ├── email_normalizer.py     # HTML cleaner, signature stripper, parser
│   │   │   ├── importance_scorer.py    # Hybrid heuristic + AI importance engine
│   │   │   ├── rag_service.py          # ChromaDB collection & embedding manager
│   │   │   ├── whatsapp_service.py     # WhatsApp Cloud API client
│   │   │   └── whatsapp_agent.py       # Conversational intent router & bot handler
│   │   └── workers/
│   │       ├── celery_app.py           # Celery application & beat schedule setup
│   │       └── tasks.py                # Celery async tasks for sync & notification
│   ├── tests/                          # 40 comprehensive unit & integration tests
│   ├── Dockerfile                      # Production backend container definition
│   ├── requirements.txt                # Python dependencies
│   └── .env.example                    # Sample environment template
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── Landing.jsx             # Public SaaS landing page
│   │   │   ├── Login.jsx               # Authentication login
│   │   │   ├── Register.jsx            # Authentication register
│   │   │   ├── Dashboard.jsx           # Analytics, Deadlines & Top emails
│   │   │   ├── Emails.jsx              # Searchable categorized inbox
│   │   │   ├── AskAI.jsx               # Vector RAG conversational search
│   │   │   ├── Notifications.jsx       # WhatsApp notification log & dispatch
│   │   │   ├── ConnectEmail.jsx        # Google OAuth connection wizard
│   │   │   └── Settings.jsx            # Thresholds, phone number & WhatsApp bot simulator
│   │   ├── components/                 # Reusable UI components & Layouts
│   │   └── services/api.js             # Axios client with JWT interceptor
│   ├── nginx.conf                      # Production SPA routing & security headers
│   ├── Dockerfile                      # Multi-stage Node build -> Nginx runtime
│   └── package.json                    # Frontend dependencies
│
├── docker-compose.yml                  # Complete stack orchestration (Mongo, Redis, API, Celery, Nginx)
├── LICENSE                             # MIT License
└── README.md
```

---

## ⚙️ 5. Environment Variables Setup

Create a `.env` file in `backend/.env` using the provided [`.env.example`](backend/.env.example):

```env
APP_NAME=MailSentinel AI
ENVIRONMENT=development

# Database
MONGODB_URI=mongodb://localhost:27017
MONGODB_DB_NAME=mailsentinel

# URLs
FRONTEND_URL=http://localhost:5173
BACKEND_URL=http://localhost:8000

# Auth
JWT_SECRET=your_super_secret_jwt_key_here_change_in_production
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=10080

# Google Cloud OAuth 2.0 (For Gmail Ingestion)
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://localhost:5173/auth/google/callback

# Groq Cloud API (For GenAI Intelligence)
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile

# Meta WhatsApp Cloud API (For Mobile Notifications & Conversational Bot)
WHATSAPP_ACCESS_TOKEN=your_meta_whatsapp_access_token
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id
WHATSAPP_BUSINESS_ACCOUNT_ID=your_business_account_id
WHATSAPP_VERIFY_TOKEN=mailsentinel_secure_webhook_verify_token_2026

# Redis & Celery
REDIS_URL=redis://localhost:6379/0
```

---

## 🚀 6. Quickstart & Local Development

### Option A: Running with Docker Compose (Recommended for Production)

```bash
# Clone the repository
git clone https://github.com/NULLPOINTERCODER/MailSentinel_AI.git
cd MailSentinel_AI

# Create backend/.env from .env.example
cp backend/.env.example backend/.env

# Build and start all services (MongoDB, Redis, Backend, Celery Worker, Celery Beat, Frontend)
docker compose up --build -d

# Check running services
docker compose ps
```

* **Frontend Dashboard**: `http://localhost:5173`
* **FastAPI Swagger Docs**: `http://localhost:8000/docs`
* **Backend Healthcheck**: `http://localhost:8000/health`

---

### Option B: Running Locally (Manual Step-by-Step)

#### 1. Backend Setup
```bash
cd backend
python -m venv venv

# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

#### 2. Background Celery Worker & Beat (Optional for local test)
```bash
# Terminal 2 - Celery Worker
cd backend
celery -A app.workers.celery_app.celery_app worker --loglevel=info -c 2

# Terminal 3 - Celery Beat Scheduler
cd backend
celery -A app.workers.celery_app.celery_app beat --loglevel=info
```

#### 3. Frontend Setup
```bash
# Terminal 4 - Frontend
cd frontend
npm install
npm run dev
```

---

## 🧪 7. Automated Test Suite

MailSentinel AI includes a complete test suite with **40 automated unit and integration tests** covering:
- Authentication & JWT validation
- Multi-user tenant isolation
- Google OAuth token exchange & Gmail normalizer
- Heuristic + Groq AI classifier & structured schema enforcement
- ChromaDB Vector RAG retrieval with user metadata partitioning
- WhatsApp Cloud API delivery & deduplication hashes
- Meta Webhook challenges & Conversational Agent intent router
- Production security headers & sensitive log redactor

```bash
cd backend
python -m pytest
```

```text
======================= 40 passed, 2 warnings in 11.06s =======================
```

---

## 🔒 8. Security & Multi-Tenant Guarantees

1. **Strict User-Level Partitioning**: Every database query, vector search in ChromaDB, and WhatsApp webhook lookup is bound to the authenticated `user_id`.
2. **Zero Plaintext Secrets**: Passwords use bcrypt salt hashing; OAuth tokens are encrypted at rest with Fernet cryptography.
3. **Log Masking**: Real-time logging filter automatically scrubs `Bearer` tokens, API keys, passwords, and authorization headers from console logs.
4. **Security Hardening**: All HTTP responses include `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection`, and `Referrer-Policy`.
5. **Request Correlation**: Every inbound request receives an `X-Request-ID` and latency header for observability.

---

## 📄 9. License

This project is licensed under the [MIT License](LICENSE).
