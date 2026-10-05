"""Vercel Python serverless entry point.

Vercel treats this file as a single serverless function and routes every
``/api/*`` request to it (see ``vercel.json``). It simply exposes the FastAPI
ASGI ``app`` defined in the application package at the repository root, so the
same app runs identically in local development (via ``uvicorn app.main:app``)
and in Vercel's serverless runtime.
"""

import sys
from pathlib import Path

# Ensure the repository root is importable regardless of the serverless CWD.
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.main import app  # noqa: E402  (import after sys.path fix)

# Vercel's @vercel/python runtime detects the module-level ``app`` ASGI object.
__all__ = ["app"]
