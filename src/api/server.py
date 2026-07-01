import asyncio
import os
import sys
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from rq.job import Job

current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.dirname(current_dir)
project_root = os.path.dirname(src_dir)
sys.path.append(src_dir)

load_dotenv(os.path.join(project_root, ".env"))

from database import ReviewDB
from rag_pipeline import CustomerCareRAG
from tasks.queue import get_queue
from tasks.rag_tasks import process_review_task

USE_RQ = os.getenv("USE_RQ", "false").lower() in {"1", "true", "yes"}

api_key = os.getenv("GOOGLE_API_KEY")
if not api_key:
    raise RuntimeError(
        "GOOGLE_API_KEY chưa được thiết lập. "
        "Hãy tạo file .env từ .env.example và điền API key."
    )

db = ReviewDB()
rag_system = CustomerCareRAG(api_key=api_key)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.init_db()
    yield


app = FastAPI(
    title="TADICO Review Care API",
    description="Hệ thống API xử lý đánh giá khách hàng tích hợp AI (RAG Pipeline)",
    version="1.0.0",
    lifespan=lifespan,
)


class ReviewInput(BaseModel):
    customer_name: str
    review_text: str


class ApprovalInput(BaseModel):
    final_reply: str


@app.post("/api/process_review", summary="Xử lý một đánh giá mới (Process a new review)")
async def process_new_review(payload: ReviewInput):
    """
    Nhận đánh giá mới -> Phân loại cảm xúc -> RAG sinh câu trả lời -> Lưu Database (Trạng thái: Pending).
    Khi USE_RQ=true, tác vụ nặng được đẩy vào Redis Queue thay vì chạy trên request thread.
    """
    if USE_RQ:
        try:
            queue = get_queue()
            job = await asyncio.to_thread(
                queue.enqueue,
                process_review_task,
                payload.customer_name,
                payload.review_text,
                job_timeout=300,
            )
            return {
                "status": "queued",
                "message": "Đánh giá đã được đưa vào hàng đợi xử lý",
                "job_id": job.id,
            }
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"Không thể kết nối Redis Queue: {e}",
            )

    result = await rag_system.process_and_store_review(
        review_text=payload.review_text,
        customer_name=payload.customer_name,
    )

    if result:
        return {
            "status": "success",
            "message": "Đã xử lý và lưu nháp thành công (Successfully processed and drafted)",
            "data": result,
        }
    raise HTTPException(status_code=500, detail="Lỗi máy chủ: Không thể xử lý RAG")


@app.get("/api/job/{job_id}", summary="Kiểm tra trạng thái job RQ")
async def get_job_status(job_id: str):
    """Poll kết quả khi xử lý review qua Redis Queue."""
    try:
        queue = get_queue()
        job = await asyncio.to_thread(Job.fetch, job_id, connection=queue.connection)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Không tìm thấy job: {job_id}")

    if job.is_finished:
        if job.is_failed:
            return {"status": "failed", "job_id": job_id, "error": job.exc_info}
        return {"status": "success", "job_id": job_id, "data": job.result}

    if job.is_started:
        return {"status": "processing", "job_id": job_id}

    return {"status": "queued", "job_id": job_id}


@app.get("/api/pending_reviews", summary="Lấy danh sách cần duyệt (Fetch pending reviews)")
async def get_pending():
    """Truy vấn các đánh giá đang ở trạng thái 'Pending' kèm câu trả lời nháp từ AI."""
    try:
        rows = await db.get_pending_reviews()
        pending_list = [
            {
                "review_id": row["review_id"],
                "customer_name": row["customer_name"],
                "review_text": row["review_text"],
                "sentiment": row["sentiment"],
                "ai_reply_draft": row["ai_reply"],
            }
            for row in rows
        ]
        return {"status": "success", "total_pending": len(pending_list), "data": pending_list}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi truy xuất dữ liệu (Database Error): {e}")


@app.put("/api/approve_review/{review_id}", summary="Phê duyệt câu trả lời (Approve AI Reply)")
async def approve_review(review_id: int, payload: ApprovalInput):
    """Cập nhật câu trả lời đã chỉnh sửa và đổi trạng thái thành 'Approved'."""
    try:
        await db.update_status(
            review_id=review_id,
            new_status='Approved',
            final_reply=payload.final_reply,
        )
        return {
            "status": "success",
            "message": f"Đã duyệt thành công (Approved) Review #{review_id}",
            "final_reply": payload.final_reply,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
