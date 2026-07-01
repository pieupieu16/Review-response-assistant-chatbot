"""Redis Queue helpers for offloading heavy RAG work."""

import os

from redis import Redis
from rq import Queue

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")
QUEUE_NAME = os.getenv("RQ_QUEUE_NAME", "rag")


def get_queue() -> Queue:
    return Queue(QUEUE_NAME, connection=Redis.from_url(REDIS_URL))
