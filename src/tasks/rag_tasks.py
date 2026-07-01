"""Background tasks executed by RQ workers."""

from rag_registry import get_rag_system, get_worker_event_loop


def process_review_task(customer_name: str, review_text: str) -> dict | None:
    """Run the full RAG pipeline using preloaded models (singleton)."""
    rag_system = get_rag_system()
    loop = get_worker_event_loop()
    return loop.run_until_complete(
        rag_system.process_and_store_review(review_text, customer_name)
    )
