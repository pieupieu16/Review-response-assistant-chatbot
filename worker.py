
"""
Start the RQ worker for background RAG processing.

Usage (from project root, with Redis running):
    python worker.py
"""

import os
import sys

from dotenv import load_dotenv
from redis import Redis
from rq import Worker

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(PROJECT_ROOT, "src")
sys.path.insert(0, SRC_DIR)

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

from rag_registry import warm_up_rag_system

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "rag")


if __name__ == "__main__":
    warm_up_rag_system()
    redis_conn = Redis.from_url(REDIS_URL)
    worker = Worker([QUEUE_NAME], connection=redis_conn)
    print(f"RQ worker listening on queue '{QUEUE_NAME}' ({REDIS_URL})")
    worker.work()
