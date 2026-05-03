# NexusAI

A FastAPI-based invoice processing system using Groq Vision AI for OCR and PostgreSQL for data persistence.

## Project Structure

```
nexusai/
├── docker-compose.yml          ← runs PostgreSQL + Redis
├── .gitignore
├── README.md
├── uploads/                    ← invoice images stored here
└── backend/
    ├── requirements.txt
    ├── .env
    ├── Dockerfile
    ├── app/
    │   ├── main.py             ← FastAPI app entry point
    │   ├── core/
    │   │   ├── __init__.py
    │   │   └── config.py       ← all settings from .env
    │   ├── db/
    │   │   ├── __init__.py
    │   │   ├── base.py         ← SQLAlchemy base class
    │   │   └── session.py      ← database connection
    │   ├── models/
    │   │   ├── __init__.py
    │   │   └── invoice.py      ← Invoice table definition
    │   ├── schemas/
    │   │   ├── __init__.py
    │   │   └── invoice.py      ← Pydantic input/output shapes
    │   ├── services/
    │   │   ├── __init__.py
    │   │   └── ocr_service.py  ← Groq Vision logic lives here
    │   ├── utils/
    │   │   ├── __init__.py
    │   │   └── file_handler.py ← image save/load helpers
    │   └── api/
    │       ├── __init__.py
    │       └── v1/
    │           ├── __init__.py
    │           ├── router.py   ← connects all endpoints
    │           └── endpoints/
    │               ├── __init__.py
    │               ├── health.py
    │               └── invoices.py
    └── tests/
        ├── __init__.py
        └── test_invoices.py
```

## Getting Started

### Prerequisites
- Python 3.9+
- Docker & Docker Compose
- Groq API Key

### Setup

1. Clone the repository
2. Create `.env` file in `backend/` with required variables
3. Install dependencies: `pip install -r backend/requirements.txt`
4. Start services: `docker-compose up -d`
5. Run the app: `python -m uvicorn app.main:app --reload`

## API Documentation

Once running, visit `http://localhost:8000/docs` for interactive API documentation.
