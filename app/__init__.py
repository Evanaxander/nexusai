"""Package shim so `app.*` imports resolve from the repository root.

The FastAPI application lives under `backend/app`, but some workflows run
`uvicorn app.main:app` from the repo root. This module extends the package
search path so Python can find the backend implementation without changing
those commands.
"""

from pathlib import Path

_backend_app = Path(__file__).resolve().parent.parent / "backend" / "app"

if _backend_app.exists():
    __path__.append(str(_backend_app))
