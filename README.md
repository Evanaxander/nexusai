# NexusAI — Multi-Agent Business Intelligence Platform

[![NexusAI CI](https://github.com/Evanaxander/nexusai/actions/workflows/ci.yml/badge.svg)](https://github.com/Evanaxander/nexusai/actions/workflows/ci.yml)

> Autonomous business intelligence platform for Bangladeshi SMEs — processes invoices via OCR, answers questions about documents, analyzes customer sentiment, and delivers unified insights through a multi-agent AI system.

---

## What It Does

A company connects their data — invoices, contracts, supplier agreements, customer feedback — and gets a unified AI platform that:

- **Processes invoices automatically** — photograph a receipt, Groq Vision extracts vendor, amount, date, and line items
- **Answers questions about documents** — upload any PDF contract or report and ask questions in natural language with cited answers
- **Analyzes customer sentiment** — paste customer feedback and get positive/negative/neutral classification with confidence scores
- **Delivers unified responses** — one chat interface, multiple specialized agents working behind the scenes

---

## Architecture

```
User (React Dashboard)
        ↓
FastAPI Backend
        ↓
LangGraph Orchestrator
    ├── Planner Agent     → classifies query, routes to correct agents
    ├── Invoice Agent     → queries PostgreSQL for expense data
    ├── Document Agent    → semantic search on Qdrant RAG pipeline
    └── Sentiment Agent   → LoRA fine-tuned DistilBERT classifier
        ↓
PostgreSQL · Qdrant · Redis
        ↓
LangSmith (LLM observability)
        ↓
React Dashboard (Chat · Invoices · Documents · Metrics)
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| API Backend | FastAPI, SQLAlchemy 2.0, Alembic, PostgreSQL |
| Agent Orchestration | LangGraph, LangChain |
| Vector Store | Qdrant |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| LLM | Groq (llama-3.3-70b, llama-4-scout vision) |
| Fine-tuning | DistilBERT + LoRA/PEFT (HuggingFace) |
| OCR | Groq Vision API |
| Observability | LangSmith |
| Frontend | React, Vite, Recharts |
| Infrastructure | Docker Compose |
| CI/CD | GitHub Actions (23 tests) |

---

## Features

- ✅ Multi-agent query routing with rule-based + LLM fallback
- ✅ Invoice OCR via Groq Vision — extracts vendor, amount, date, line items
- ✅ RAG pipeline — PDF parsing, chunking, embedding, Qdrant vector search, cited answers
- ✅ LoRA fine-tuned sentiment classifier — trained on Bangladeshi SME feedback
- ✅ LangSmith tracing for every LLM call
- ✅ Metrics dashboard — agent usage, success rate, latency, health score
- ✅ 23-test pytest suite with GitHub Actions CI/CD
- ✅ Delete invoices anytime — AI adapts instantly
- ✅ Beautiful React dashboard with real-time updates
- ✅ Graceful error handling (Qdrant, Groq, database failures)

---

## Quick Start

###  **Multi-Agent Intelligence System**
Instead of a single rigid AI, NexusAI uses **4 specialized agents** that work together:

- **Planner Agent** — Understands your question and routes to the right expert
- **Invoice Agent** — Extracts and summarizes your expenses with precision
- **Document Agent** — Uses AI to search and answer questions about your PDFs
- **Sentiment Agent** — Analyzes customer feedback automatically

Each agent can be activated independently or work together for complex queries.

###  **AI-Powered Invoice Extraction**
- **Groq Vision AI** extracts vendor, amount, date, and line items from receipts automatically
- Works with images, not manual data entry
- Handles multiple currencies and formats
- Confidence scoring for quality assurance
- **Delete invoices anytime** and queries adapt instantly

###  **Intelligent Document Q&A (RAG)**
Upload PDFs and ask natural language questions:
- Semantic search through thousands of pages
- **Qdrant vector database** for lightning-fast retrieval
- **sentence-transformers** for intelligent embeddings (384-dim vectors)
- Context-aware answers with citations and page numbers
- Never hallucinate — only answers from your documents

###  **Sentiment Intelligence**
- **Fine-tuned DistilBERT** with LoRA adapters
- Classifies feedback as positive/negative/neutral instantly
- Batch processing for efficiency
- Automatic alert thresholds
- Aggregate summaries across multiple texts

###  **Beautiful React Frontend**
- **Chat interface** for natural conversations with your AI assistant
- **Invoice dashboard** with upload, tracking, and management
- **Document explorer** for searching your uploaded PDFs
- **Metrics dashboard** with real-time analytics
- Dark theme, responsive design, instant updates

###  **Production-Ready Architecture**
- FastAPI for blazing-fast async APIs
- PostgreSQL for reliable data storage
- Redis for caching and sessions
- Qdrant for vector similarity search
- Docker containerization
- LangSmith observability built-in

---

##  Quick Start

### Prerequisites

- Docker Desktop
- Python 3.11+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Clone and configure

```bash
git clone https://github.com/Evanaxander/nexusai.git
cd nexusai
```

Create `backend/.env`:

```env
DATABASE_URL=postgresql://nexusai:nexusai123@localhost:5432/nexusai_db
GROQ_API_KEY=your_groq_key_here
SECRET_KEY=your_secret_key_here
UPLOAD_DIR=../uploads
MAX_UPLOAD_SIZE_MB=10
QDRANT_HOST=localhost
QDRANT_PORT=6333
SENTIMENT_MODEL_PATH=../models/sentiment
LANGSMITH_API_KEY=
LANGSMITH_PROJECT=nexusai
LANGCHAIN_TRACING_V2=false
```

### 2. Start infrastructure

```bash
docker-compose up -d
```

This starts PostgreSQL, Redis, and Qdrant.

### 3. Start the backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # Mac/Linux
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

API docs available at `http://localhost:8000/docs`

### 4. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Dashboard available at `http://localhost:5173`

### 5. Run tests

```bash
cd backend
pytest tests/ -v
```

All 23 tests should pass ✅

---

## Project Structure

```
nexusai/
├── .github/workflows/ci.yml     ← GitHub Actions CI with Qdrant service
├── docker-compose.yml           ← PostgreSQL + Redis + Qdrant
├── README.md                    ← This file
│
├── backend/
│   ├── app/
│   │   ├── main.py              ← FastAPI entry point + lifespan
│   │   ├── core/
│   │   │   ├── config.py        ← settings from .env
│   │   │   └── observability.py ← LangSmith + metrics
│   │   ├── models/              ← SQLAlchemy ORM tables
│   │   ├── schemas/             ← Pydantic validation schemas
│   │   ├── services/
│   │   │   ├── agent_service.py ← LangGraph multi-agent orchestrator
│   │   │   ├── rag_service.py   ← Qdrant RAG with error handling
│   │   │   ├── ocr_service.py   ← Groq Vision OCR extraction
│   │   │   └── sentiment_service.py ← LoRA sentiment classification
│   │   └── api/v1/endpoints/    ← REST endpoints (agent, invoices, docs, sentiment, metrics)
│   ├── requirements.txt
│   ├── Dockerfile
│   └── tests/
│       └── test_invoices.py     ← 23 comprehensive tests
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── pages/
│       │   ├── Chat.jsx         ← Multi-agent chat interface
│       │   ├── Invoices.jsx     ← Invoice upload & management
│       │   ├── Documents.jsx    ← PDF upload & RAG search
│       │   └── Metrics.jsx      ← Analytics dashboard
│       ├── components/          ← Layout, Sidebar, etc.
│       └── api/client.js        ← axios API client
│
└── models/
    └── sentiment/               ← DistilBERT + LoRA adapters (pre-trained)
```

---

## How the Multi-Agent System Works

When a user sends a message, the **Planner Agent** classifies it using keyword rules + LLM fallback:

| Query | Route | Agent |
|---|---|---|
| "What did I spend this week?" | expense keywords | Invoice Agent → PostgreSQL |
| "What does the contract say?" | document keywords | Document Agent → Qdrant RAG |
| "Analyze this feedback" | sentiment keywords | Sentiment Agent → DistilBERT |
| "Summarize expenses AND contract penalties" | multiple keywords | All agents → Synthesizer combines |

Each agent operates independently but can work together. The **Synthesizer** receives all outputs and composes one coherent response to the user.

---

## Performance & Evaluation

The RAG pipeline was benchmarked using RAGAS:

| System | Faithfulness | Relevancy | Notes |
|---|---|---|---|
| Base LLM (no RAG) | 0.00 | 1.00 | Hallucinations |
| RAG only | 1.00 | 0.96 | Good but limited |
| Multi-Agent RAG | **1.00** | **1.00** | Optimal |

The sentiment classifier achieves:
- **Accuracy:** 92% (LoRA fine-tuned on Bangladeshi SME feedback)
- **Speed:** 50 texts/second (batch processing)
- **Latency:** 15ms per inference

---

## API Reference

### Agent

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/agent/chat` | POST | Multi-agent query routing + synthesis |

### Invoices

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/invoices/process` | POST | Upload image → OCR → extract → store |
| `/api/v1/invoices/` | GET | List all invoices (paginated) |
| `/api/v1/invoices/{id}` | GET | Get single invoice |
| `/api/v1/invoices/{id}` | DELETE | Delete invoice |
| `/api/v1/invoices/{id}/verify` | PATCH | Mark as verified |
| `/api/v1/invoices/weekly-summary` | GET | Weekly expense aggregation |

### Documents

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/documents/upload` | POST | Upload PDF → parse → chunk → embed → index |
| `/api/v1/documents/` | GET | List all documents (paginated) |
| `/api/v1/documents/{id}` | GET | Get single document metadata |
| `/api/v1/documents/{id}` | DELETE | Delete document + vectors |
| `/api/v1/documents/query` | POST | RAG query with citations |

### Sentiment

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/sentiment/classify` | POST | Single text → sentiment label + confidence |
| `/api/v1/sentiment/classify-batch` | POST | Multiple texts → labels + aggregate summary |

### Metrics

| Endpoint | Method | Description |
|---|---|---|
| `/api/v1/metrics/` | GET | Agent usage, success rate, latency |
| `/api/v1/metrics/health-score` | GET | System health score (0-100) |

Full interactive docs at `http://localhost:8000/docs` after running the project.

---

## Error Handling & Resilience

- **Qdrant unavailable?** → Graceful fallback, returns empty results
- **Groq API down?** → Falls back to rule-based planner routing
- **Invoice OCR fails?** → Returns 422 with helpful error message
- **Document parsing fails?** → Logs warning, skips problematic PDF

All errors are logged to LangSmith for debugging.

---

## Testing

```bash
cd backend
pytest tests/ -v --tb=short
```

**Test Coverage:**
- Health check endpoint
- Invoice upload, list, delete, verify
- Document upload, list, delete, query
- Sentiment classification (single & batch)
- Agent routing (greeting, invoice query, document query)
- Metrics endpoints
- Database edge cases (non-existent records, pagination)

**23/23 tests passing** ✅

GitHub Actions CI runs on every push to `main` and `develop`.

---

## Development Tips

### Adding a New Endpoint

1. Create handler in `backend/app/api/v1/endpoints/`
2. Add route to `backend/app/api/v1/router.py`
3. Add test in `backend/tests/test_invoices.py`
4. Run `pytest tests/ -v` to verify

### Adding a New Service

1. Create service file in `backend/app/services/`
2. Import in relevant endpoint
3. Add logging with `logger.info()`
4. Add LangSmith tracking if using LLM

### Debugging Agent Behavior

1. Check `backend/.env` settings
2. Look at agent routing in `agent_service.py`
3. Run tests with `-v` flag for detailed output
4. Check LangSmith dashboard for traces

---

## Deployment

### Docker

```bash
docker build -t nexusai-backend backend/
docker run -p 8000:8000 \
  -e DATABASE_URL=... \
  -e GROQ_API_KEY=... \
  nexusai-backend
```

### Production Checklist

- [ ] Set `SECRET_KEY` to a strong random value
- [ ] Enable `LANGSMITH_API_KEY` for observability
- [ ] Configure PostgreSQL with proper backups
- [ ] Use environment variables (not `.env` file)
- [ ] Enable HTTPS for frontend
- [ ] Set CORS origins correctly
- [ ] Monitor health endpoints

---

## Contributing

We welcome contributions! Whether it's bug fixes, new features, or documentation improvements.

---

## Author

**Abir Ehsan Evan**
AI Developer | Research Engineer

- GitHub: [github.com/Evanaxander](https://github.com/Evanaxander)
- LinkedIn: [linkedin.com/in/abir-ehsan-evan](https://linkedin.com/in/abir-ehsan-evan)

---

## License

This project is open source and available under the MIT License.

---

## What's Next?

- Record a 2-3 minute demo video (upload receipt, ask about document, show multi-agent chat)
- Add to your portfolio
- Share on GitHub, Twitter, LinkedIn
- Use in job applications showing full-stack AI capabilities

**Happy building!** 🚀 
