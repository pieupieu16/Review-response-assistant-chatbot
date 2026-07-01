"""Singleton registry — load heavy AI models once per worker process."""

import asyncio
import os
import threading

from dotenv import load_dotenv

from rag_pipeline import CustomerCareRAG

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

_lock = threading.Lock()
_rag_system: CustomerCareRAG | None = None
_worker_loop: asyncio.AbstractEventLoop | None = None


def get_rag_system() -> CustomerCareRAG:
    """Return a process-wide CustomerCareRAG instance (thread-safe lazy init)."""
    global _rag_system
    if _rag_system is not None:
        return _rag_system

    with _lock:
        if _rag_system is None:
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise RuntimeError("GOOGLE_API_KEY is not set")
            print("[RAG Registry] Loading models into memory (one-time per worker)...")
            _rag_system = CustomerCareRAG(api_key=api_key)
            print("[RAG Registry] Models ready.")
        return _rag_system


def warm_up_rag_system() -> CustomerCareRAG:
    """Preload models and DB schema once at worker startup."""
    rag = get_rag_system()
    loop = get_worker_event_loop()
    loop.run_until_complete(rag.db.init_db())
    return rag


def get_worker_event_loop() -> asyncio.AbstractEventLoop:
    """Reuse one event loop per worker process for async DB calls."""
    global _worker_loop
    if _worker_loop is None or _worker_loop.is_closed():
        _worker_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(_worker_loop)
    return _worker_loop
