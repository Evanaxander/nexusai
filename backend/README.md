# NexusAI Backend

A **multi-agent business intelligence platform** that combines invoice processing, document retrieval, and sentiment analysis into one unified API. Built with FastAPI, Groq AI, PostgreSQL, and Qdrant.

---

## 🎯 Features

### 1. **Multi-Agent System**
- **Planner Agent**: Routes incoming queries to appropriate handlers
- **Invoice Agent**: Retrieves weekly expense summaries from PostgreSQL
- **Document Agent**: Searches contracts and documents using RAG (Retrieval-Augmented Generation)
- **Sentiment Agent**: Classifies customer feedback as positive/negative/neutral

### 2. **Invoice Processing**
- OCR extraction using Groq Vision AI
- Automatic vendor, amount, and date detection
- Image storage and invoice verification workflows
- Weekly expense aggregation and vendor analytics

### 3. **Document Q&A (RAG)**
- Upload PDFs and ask questions about their content
- Semantic search using Qdrant vector database
- Embeddings via `sentence-transformers` (all-MiniLM-L6-v2)
- Citation support: chunks return page numbers and context

### 4. **Sentiment Analysis**
- Fine-tuned DistilBERT with LoRA adapters
- Batch processing of customer feedback
- Confidence scores and alert thresholds (>40% negative = alert)
- Aggregate summaries for multiple texts

### 5. **REST API**
- Full OpenAPI/Swagger documentation at `/docs`
- Async endpoints for large file uploads and batch processing
- CORS enabled for local development

---

## 🏗️ Architecture

### Directory Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI app + lifespan
│   ├── core/
│   │   └── config.py                    # Settings from .env
│   ├── db/
│   │   ├── base.py                      # SQLAlchemy ORM base
│   │   └── session.py                   # Database connection pool
│   ├── models/
│   │   ├── invoice.py                   # Invoice table definition
│   │   └── document.py                  # Document metadata table
│   ├── schemas/
│   │   ├── invoice.py                   # Pydantic request/response models
│   │   └── document.py                  # Document schemas
│   ├── services/
│   │   ├── agent_service.py             # Multi-agent orchestration
│   │   ├── ocr_service.py               # Groq Vision OCR
│   │   ├── rag_service.py               # RAG pipeline (embedding + retrieval)
│   │   └── sentiment_service.py         # Sentiment classification
│   ├── utils/
│   │   └── file_handler.py              # Image save/load helpers
│   └── api/
│       └── v1/
│           ├── router.py                # Route aggregator
│           └── endpoints/
│               ├── health.py            # Health check
│               ├── invoices.py          # Invoice CRUD + OCR
│               ├── documents.py         # Document upload + RAG query
│               ├── agent.py             # Multi-agent chat endpoint
│               └── sentiment.py         # Sentiment classification
├── tests/
│   └── test_invoices.py                 # Integration tests
├── requirements.txt                     # Python dependencies
├── Dockerfile                           # Container image definition
├── .env.example                         # Environment template
└── README.md                            # This file
```

### Data Flow

```
User Query
    ↓
/api/v1/agent/chat (POST)
    ↓
Planner Agent (local routing)
    ├─→ needs_invoice? → Invoice Agent → DB query
    ├─→ needs_document? → Document Agent → Qdrant search
    └─→ needs_sentiment? → Sentiment Agent → Model inference
    ↓
Synthesizer (merge results)
    ↓
AgentResponse (final answer + metadata)
```

---

## 🚀 Getting Started

### Prerequisites

- **Python** 3.10+ (tested on 3.10, 3.11)
- **Docker** & **Docker Compose** (for services)
- **Groq API Key** (for invoice OCR)
- **GPU optional** but recommended for sentiment model (~6GB VRAM)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repo-url>
   cd nexusai/backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Copy and configure `.env`**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```

5. **Start infrastructure services**
   ```bash
   docker-compose up -d
   ```
   This starts:
   - PostgreSQL (port 5433)
   - Redis (port 6379)
   - Qdrant (port 6333)

6. **Run the backend**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

7. **Access API**
   - Swagger UI: [http://localhost:8000/docs](http://localhost:8000/docs)
   - ReDoc: [http://localhost:8000/redoc](http://localhost:8000/redoc)
   - OpenAPI JSON: [http://localhost:8000/openapi.json](http://localhost:8000/openapi.json)

---

## ⚙️ Configuration

### Environment Variables (`.env`)

```env
# Database
DATABASE_URL=postgresql://nexusai:nexusai123@127.0.0.1:5433/nexusai_db

# Groq (for OCR and agent)
GROQ_API_KEY=gsk_your_api_key_here

# App
SECRET_KEY=your-secret-key-here
UPLOAD_DIR=../uploads
MAX_UPLOAD_SIZE_MB=10

# Qdrant (vector database)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# Sentiment model path (local file or huggingface model ID)
SENTIMENT_MODEL_PATH=./models/sentiment-model
```

### Key Services

| Service | Role | Port | Health Check |
|---------|------|------|--------------|
| FastAPI | API server | 8000 | `GET /api/v1/health` |
| PostgreSQL | Invoices + Documents | 5433 | Tables auto-created on startup |
| Qdrant | Vector embeddings | 6333 | Automatic collection setup |
| Redis | Cache (optional) | 6379 | Not required for core features |

---

## 📡 API Endpoints

### Health
```
GET /api/v1/health
→ { "status": "healthy", "timestamp": "2026-05-03T15:00:00Z" }
```

### Invoices

**Upload & Process**
```
POST /api/v1/invoices/process
Body: { "file": <image>, "uploaded_by": "user" }
→ { "id": 1, "vendor": "Acme Inc", "amount": 1250.50, ... }
```

**List Invoices**
```
GET /api/v1/invoices/?limit=20&offset=0
→ [{ "id": 1, "vendor": "...", ... }]
```

**Weekly Summary**
```
GET /api/v1/invoices/weekly-summary
→ {
    "period_start": "2026-04-26",
    "period_end": "2026-05-03",
    "total_expenses": 5432.75,
    "invoice_count": 12,
    "top_vendors": ["Acme Inc", "Global Supply"],
    "daily_breakdown": { "2026-05-03": 450.00, ... }
  }
```

**Verify Invoice**
```
PATCH /api/v1/invoices/{id}/verify
Body: { "amount": 1300.00, "vendor": "Acme Corp", "is_verified": true }
→ Updated invoice
```

### Documents

**Upload & Index**
```
POST /api/v1/documents/upload
Body: { "file": <pdf>, "uploaded_by": "user" }
→ {
    "id": 1,
    "filename": "abc123.pdf",
    "total_pages": 5,
    "total_chunks": 25,
    "is_indexed": true
  }
```

**Query Documents**
```
POST /api/v1/documents/query
Body: {
  "question": "What are the payment terms?",
  "top_k": 5,
  "document_ids": [1, 2],
  "stream": false
}
→ {
    "question": "...",
    "answer": "Payment terms: Net 30...",
    "sources": [
      { "text": "...", "page_number": 2, "chunk_index": 5, "document_name": "contract.pdf" }
    ],
    "total_chunks_searched": 5
  }
```

**Streaming Responses** (`stream=true`)
```
Returns Server-Sent Events (SSE):
data: Payment
data: terms
data: are
...
data: [DONE]
```

### Sentiment Analysis

**Single Text**
```
POST /api/v1/sentiment/classify
Body: { "text": "Delivery was late and product quality was terrible" }
→ {
    "label": "negative",
    "confidence": 0.94,
    "text_preview": "Delivery was late and product quality..."
  }
```

**Batch Analysis**
```
POST /api/v1/sentiment/classify-batch
Body: {
  "texts": ["Great product!", "Terrible service", "It's okay"],
  "summarize": true
}
→ {
    "results": [
      { "label": "positive", "confidence": 0.98, ... },
      { "label": "negative", "confidence": 0.91, ... },
      { "label": "neutral", "confidence": 0.87, ... }
    ],
    "summary": {
      "total": 3,
      "positive": 1,
      "negative": 1,
      "neutral": 1,
      "dominant": "neutral",
      "average_confidence": 0.92,
      "alert": false,
      "negative_ratio": 0.333
    }
  }
```

### Multi-Agent Chat

**Main Agent Endpoint**
```
POST /api/v1/agent/chat
Body: { "message": "What did I spend this week?" }
→ {
    "user_message": "What did I spend this week?",
    "final_answer": "Weekly expense summary...",
    "invoice_summary": "Total spent: 5432.75 BDT...",
    "document_answer": "",
    "document_sources": [],
    "sentiment_results": [],
    "sentiment_summary": {},
    "agents_used": {
      "invoice": true,
      "document": false,
      "sentiment": false
    }
  }
```

---

## 🔧 Development

### Running Tests

```bash
# All tests (requires Postgres running)
pytest tests/ -v

# Specific test
pytest tests/test_invoices.py::test_agent_invoice_query -v

# With coverage
pytest tests/ --cov=app --cov-report=html
```

### Running Linting & Type Checking

```bash
# Lint with pylint
pylint app/

# Type check with mypy
mypy app/

# Format with black
black app/
```

### Development Server

```bash
# Auto-reload on file changes
uvicorn app.main:app --reload --port 8000

# With logging
uvicorn app.main:app --reload --port 8000 --log-level debug
```

---

## 🐳 Docker Deployment

### Build Container

```bash
docker build -t nexusai-backend:latest .
```

### Run Container

```bash
docker run -d \
  --name nexusai-api \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://nexusai:nexusai123@postgres:5432/nexusai_db \
  -e GROQ_API_KEY=$GROQ_API_KEY \
  -v uploads:/app/uploads \
  nexusai-backend:latest
```

### Docker Compose (Full Stack)

From project root:
```bash
docker-compose up -d
```

---

## 📊 Database Schema

### Invoices Table
```sql
CREATE TABLE invoices (
  id SERIAL PRIMARY KEY,
  vendor VARCHAR(200) NOT NULL,
  amount FLOAT NOT NULL,
  currency VARCHAR(10) DEFAULT 'BDT',
  invoice_date VARCHAR(50),
  items TEXT,                    -- JSON list
  raw_text TEXT,                 -- Full OCR output
  image_path VARCHAR(500),
  uploaded_by VARCHAR(100),
  is_verified BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

### Documents Table
```sql
CREATE TABLE documents (
  id SERIAL PRIMARY KEY,
  filename VARCHAR(255) UNIQUE NOT NULL,
  original_name VARCHAR(255),
  file_path VARCHAR(500),
  total_pages INTEGER,
  total_chunks INTEGER,
  is_indexed BOOLEAN DEFAULT FALSE,
  uploaded_by VARCHAR(100),
  created_at TIMESTAMP DEFAULT NOW()
);
```

### Qdrant Collection
```json
{
  "collection_name": "nexusai_documents",
  "vector_size": 384,
  "distance": "cosine",
  "payload": {
    "document_id": 1,
    "document_name": "contract.pdf",
    "page_number": 2,
    "chunk_index": 5,
    "text": "chunk content..."
  }
}
```

---

## 🔐 Security

- **CORS**: Configured for `localhost:3000` and `localhost:5173`
- **Secret Key**: Set `SECRET_KEY` in `.env` for session signing
- **File Upload**: Max 10MB (configurable), only PDF/images allowed
- **Database**: Uses parameterized queries to prevent SQL injection
- **API Keys**: All sensitive keys stored in environment variables

---

## 🐛 Troubleshooting

### Connection Refused (PostgreSQL)
```
Error: connection to server at "127.0.0.1", port 5433 failed
Solution: Start Docker containers: docker-compose up -d
```

### Sentiment Model Not Found
```
Error: FileNotFoundError: Sentiment model not found
Solution: Download model and set SENTIMENT_MODEL_PATH in .env
```

### Qdrant Connection Error
```
Error: Failed to connect to Qdrant at localhost:6333
Solution: Ensure Qdrant container is running: docker-compose logs qdrant
```

### Import Error: cannot import name 'run_agent'
```
Error: ImportError from app.services.agent_service
Solution: Rebuild venv: pip install -r requirements.txt
```

### Groq API Rate Limited
```
Error: 429 Too Many Requests
Solution: Add delays between requests or upgrade Groq plan
```

---

## 📚 Dependencies

| Package | Purpose |
|---------|---------|
| `fastapi` | Web framework |
| `uvicorn` | ASGI server |
| `sqlalchemy` | ORM |
| `psycopg2` | PostgreSQL driver |
| `groq` | LLM/Vision API |
| `qdrant-client` | Vector DB client |
| `sentence-transformers` | Embeddings |
| `transformers` | Hugging Face models |
| `peft` | LoRA adapter loading |
| `pypdf` | PDF text extraction |
| `pillow` | Image handling |
| `pydantic` | Data validation |
| `pytest` | Testing |

Full list: see `requirements.txt`

---

## 📖 Example Workflows

### Workflow 1: Expense Reporting
```
1. User: "What did I spend this week?"
2. Agent routes to Invoice Agent
3. Planner → Invoice Agent → DB query → summarize
4. Response: Weekly breakdown by vendor
```

### Workflow 2: Contract Compliance
```
1. User: "Upload contract.pdf then tell me payment terms"
2. Upload → /api/v1/documents/upload → indexed in Qdrant
3. Query: "What are the payment terms?"
4. Agent → Document Agent → RAG retrieval → answer with citations
```

### Workflow 3: Feedback Analysis
```
1. User uploads 50 customer reviews
2. POST /api/v1/sentiment/classify-batch
3. Returns sentiment breakdown + alert if >40% negative
4. Use summary in next agent chat: "Analyze feedback trends"
```

---

## 🚀 Performance Notes

- **Invoice OCR**: ~2-3 seconds per image (Groq API)
- **Document Indexing**: ~1-2 seconds per PDF page (embedding)
- **Sentiment Classification**: ~50ms per text (batch mode faster)
- **RAG Query**: ~500ms (embedding + Qdrant search + LLM generation)
- **Caching**: Sentiment model cached in memory after first load

---

## 📝 License

[Specify license here]

---

## 👥 Support

- GitHub Issues: [link]
- Documentation: [link]
- Contact: [email]

---

**Last Updated**: May 3, 2026
**Version**: 1.0.0
