# 🚀 NexusAI

**The Intelligent Business Assistant You've Been Waiting For**

NexusAI is a sophisticated **multi-agent AI platform** that transforms how you manage business data. Combining invoice processing, document intelligence, and sentiment analysis into one unified system powered by cutting-edge AI and vector databases.

> **"From chaos to clarity"** — Extract insights from invoices, search through contracts, and understand customer feedback, all through a single intelligent interface.

---

## ✨ What Makes NexusAI Amazing

### 🤖 **Multi-Agent Intelligence System**
Instead of a single rigid AI, NexusAI uses **4 specialized agents** that work together:

- **Planner Agent** — Understands your question and routes to the right expert
- **Invoice Agent** — Extracts and summarizes your expenses with precision
- **Document Agent** — Uses AI to search and answer questions about your PDFs
- **Sentiment Agent** — Analyzes customer feedback automatically

Each agent can be activated independently or work together for complex queries.

### 📸 **AI-Powered Invoice Extraction**
- **Groq Vision AI** extracts vendor, amount, date, and line items from receipts automatically
- Works with images, not manual data entry
- Handles multiple currencies and formats
- Confidence scoring for quality assurance
- **Delete invoices anytime** and queries adapt instantly

### 📚 **Intelligent Document Q&A (RAG)**
Upload PDFs and ask natural language questions:
- Semantic search through thousands of pages
- **Qdrant vector database** for lightning-fast retrieval
- **sentence-transformers** for intelligent embeddings (384-dim vectors)
- Context-aware answers with citations and page numbers
- Never hallucinate — only answers from your documents

### 💭 **Sentiment Intelligence**
- **Fine-tuned DistilBERT** with LoRA adapters
- Classifies feedback as positive/negative/neutral instantly
- Batch processing for efficiency
- Automatic alert thresholds
- Aggregate summaries across multiple texts

### 🎨 **Beautiful React Frontend**
- **Chat interface** for natural conversations with your AI assistant
- **Invoice dashboard** with upload, tracking, and management
- **Document explorer** for searching your uploaded PDFs
- **Metrics dashboard** with real-time analytics
- Dark theme, responsive design, instant updates

### ⚡ **Production-Ready Architecture**
- FastAPI for blazing-fast async APIs
- PostgreSQL for reliable data storage
- Redis for caching and sessions
- Qdrant for vector similarity search
- Docker containerization
- LangSmith observability built-in

---

## 🚀 Quick Start

### Prerequisites
- Python 3.9+
- Node.js 16+
- Docker & Docker Compose
- Groq API Key ([Get one free](https://console.groq.com))

### Setup (5 minutes)

```bash
# 1. Clone and navigate
git clone https://github.com/Evanaxander/nexusai.git
cd nexusai

# 2. Start infrastructure (PostgreSQL, Redis, Qdrant)
docker-compose up -d

# 3. Backend setup
cd backend
pip install -r requirements.txt
echo "GROQ_API_KEY=your_key_here" > .env
python -m uvicorn app.main:app --reload

# 4. Frontend setup (new terminal)
cd frontend
npm install
npm run dev
```

**Done!** 
- Frontend: `http://localhost:5173`
- API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

---

## 💡 Usage Examples

### Chat with Your Data
```
You: "How much did I spend this week?"
NexusAI: "Weekly expense summary (May 7 - May 14):
• Total spent: 181.41 USD
• Invoice count: 2
• Top vendor: East Repair Inc."

You: "What payment terms are in my supplier contract?"
NexusAI: "According to the contract (page 3):
Payment terms: Net 30 days from invoice date..."

You: "Analyze the customer feedback I pasted below"
NexusAI: "Sentiment Summary:
• Total texts: 5
• Positive: 60% | Negative: 20% | Neutral: 20%
• Alert: No ⚠️"
```

### Manage Invoices
- Upload receipt images → auto-extracted data
- View weekly summaries instantly
- Delete invoices with one click → summaries update
- Ask questions about specific expenses
- Verify or correct OCR results

### Search Documents
- Upload PDFs (contracts, policies, CVs)
- Ask questions in natural language
- Get answers with exact citations
- Search across multiple documents
- Export relevant sections

---

## 🏗️ Architecture

### Three-Tier System

```
┌─────────────────────────────────────┐
│     Frontend (React + Vite)         │
│  Chat | Invoices | Docs | Metrics   │
└─────────────┬───────────────────────┘
              │ (REST API)
┌─────────────▼───────────────────────┐
│    Backend (FastAPI)                │
│  Multi-Agent Orchestration          │
│  • Planner • Invoice • Document     │
│  • Sentiment • Synthesizer          │
└─────────────┬───────────────────────┘
              │
    ┌─────────┼─────────┐
    │         │         │
┌───▼──┐ ┌───▼──┐ ┌───▼──┐
│ PostgreSQL│ Redis  │ Qdrant
│Invoices   │Caching │Vectors
└──────┘ └──────┘ └──────┘
```

### Key Technologies

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **API** | FastAPI | High-performance async REST endpoints |
| **LLM** | Groq (Llama 3.3 70B) | Query routing & answer generation |
| **Vision** | Groq Vision | OCR from invoice images |
| **Embeddings** | sentence-transformers | 384-dim semantic vectors |
| **Vector DB** | Qdrant | Fast similarity search for RAG |
| **NLP** | DistilBERT + LoRA | Sentiment classification |
| **Database** | PostgreSQL | Transactional data storage |
| **Cache** | Redis | Session & cache layer |
| **Frontend** | React 19 + Vite | Modern, responsive UI |
| **DevOps** | Docker Compose | Local development & deployment |
| **Observability** | LangSmith | Full tracing & debugging |

---

## 📊 Project Structure

```
nexusai/
├── docker-compose.yml              ← Infrastructure
├── init-postgres.sql               ← Database setup
├── README.md
│
├── backend/                        ← FastAPI application
│   ├── requirements.txt
│   ├── Dockerfile
│   └── app/
│       ├── main.py                 ← Entry point
│       ├── core/
│       │   ├── config.py           ← Settings from .env
│       │   └── observability.py    ← LangSmith tracing
│       ├── api/v1/
│       │   ├── router.py           ← Route registration
│       │   └── endpoints/
│       │       ├── agent.py        ← Chat endpoint
│       │       ├── invoices.py     ← Invoice CRUD
│       │       ├── documents.py    ← Document RAG
│       │       ├── sentiment.py    ← Sentiment analysis
│       │       ├── metrics.py      ← Analytics
│       │       └── health.py       ← Health check
│       ├── services/
│       │   ├── agent_service.py    ← Multi-agent orchestration
│       │   ├── ocr_service.py      ← Groq Vision integration
│       │   ├── rag_service.py      ← Document QA + vector search
│       │   └── sentiment_service.py← DistilBERT classification
│       ├── db/
│       │   ├── base.py             ← SQLAlchemy base
│       │   └── session.py          ← Connection management
│       ├── models/                 ← ORM models
│       └── schemas/                ← Pydantic schemas
│
├── frontend/                       ← React application
│   ├── package.json
│   ├── vite.config.js
│   └── src/
│       ├── pages/
│       │   ├── Chat.jsx            ← Multi-agent interface
│       │   ├── Invoices.jsx        ← Invoice management
│       │   ├── Documents.jsx       ← Document upload & search
│       │   └── Metrics.jsx         ← Analytics dashboard
│       ├── components/
│       │   ├── Layout.jsx
│       │   └── Sidebar.jsx
│       └── api/
│           └── client.js           ← API service client
│
└── models/
    └── sentiment/
        ├── adapter_config.json     ← LoRA adapter config
        ├── adapter_model.safetensors
        └── tokenizer.json
```

---

## 🎯 Features

- ✅ **Upload & Extract** — OCR invoices to structured data
- ✅ **Query Invoices** — Ask about expenses any time
- ✅ **Delete & Adapt** — Remove invoices, AI updates instantly
- ✅ **Upload Documents** — PDFs, contracts, journals
- ✅ **Semantic Search** — Find information across documents
- ✅ **Q&A with Citations** — Ask questions, get page numbers
- ✅ **Sentiment Analysis** — Understand customer feedback
- ✅ **Real-Time Metrics** — Track usage and performance
- ✅ **Beautiful UI** — Modern React interface
- ✅ **Full API Docs** — Swagger UI at `/docs`
- ✅ **Observability** — LangSmith tracing for debugging

---

## 🔧 Environment Setup

Create `backend/.env`:

```env
DATABASE_URL=postgresql://nexusai:nexusai123@localhost:5433/nexusai_db
GROQ_API_KEY=gsk_your_key_here
SECRET_KEY=your_secret_key_here
QDRANT_HOST=localhost
QDRANT_PORT=6333
LANGSMITH_API_KEY=optional_for_tracing
```

---

## 📚 API Examples

### Chat with Agent
```bash
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How much did I spend this week?"}'
```

### Upload Invoice
```bash
curl -X POST http://localhost:8000/api/v1/invoices/process \
  -F "file=@receipt.png"
```

### Search Documents
```bash
curl -X POST http://localhost:8000/api/v1/documents/query \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are the payment terms?",
    "document_ids": [1, 2],
    "top_k": 5
  }'
```

---

## 🤝 Contributing

We welcome contributions! Whether it's bug fixes, new features, or documentation improvements.

---

## 📄 License

This project is open source and available under the MIT License.

---

## 🎉 Get Started Now

Transform your business data management today. Start with the quick setup above and experience the power of multi-agent AI.

**Questions?** Check the full API docs at `http://localhost:8000/docs` after running the project.

Happy analyzing! 🚀
