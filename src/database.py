import os
from datetime import datetime

import aiosqlite

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_NAME = os.path.join(PROJECT_ROOT, "tadico_review_care.db")


class ReviewDB:
    def __init__(self, db_name=None):
        self.db_name = db_name or DEFAULT_DB_NAME

    async def init_db(self):
        """Khởi tạo schema một lần lúc server/worker startup (gọi từ lifespan)."""
        async with aiosqlite.connect(self.db_name) as conn:
            await conn.execute("PRAGMA journal_mode=WAL")
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS reviews (
                    review_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    customer_name TEXT,
                    review_text TEXT,
                    sentiment TEXT,
                    confidence_score REAL,
                    ai_reply TEXT,
                    status TEXT DEFAULT 'Pending',
                    timestamp TEXT
                )
            """)
            await conn.commit()

    async def insert_review(
        self,
        review_text,
        sentiment,
        confidence_score,
        customer_name="Khách hàng ẩn danh",
        ai_reply="",
    ):
        """Chèn một review mới vào database và trả về review_id"""
        async with aiosqlite.connect(self.db_name) as conn:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = await conn.execute(
                """
                INSERT INTO reviews (
                    customer_name, review_text, sentiment,
                    confidence_score, ai_reply, status, timestamp
                )
                VALUES (?, ?, ?, ?, ?, 'Pending', ?)
                """,
                (customer_name, review_text, sentiment, confidence_score, ai_reply, timestamp),
            )
            await conn.commit()
            return cursor.lastrowid

    async def update_ai_reply(self, review_id, ai_reply):
        """Cập nhật câu trả lời nháp của AI"""
        async with aiosqlite.connect(self.db_name) as conn:
            await conn.execute(
                "UPDATE reviews SET ai_reply = ? WHERE review_id = ?",
                (ai_reply, review_id),
            )
            await conn.commit()

    async def update_status(self, review_id, new_status, final_reply=None):
        """Cập nhật trạng thái duyệt và câu trả lời cuối cùng nếu có sửa đổi"""
        async with aiosqlite.connect(self.db_name) as conn:
            if final_reply:
                await conn.execute(
                    "UPDATE reviews SET status = ?, ai_reply = ? WHERE review_id = ?",
                    (new_status, final_reply, review_id),
                )
            else:
                await conn.execute(
                    "UPDATE reviews SET status = ? WHERE review_id = ?",
                    (new_status, review_id),
                )
            await conn.commit()

    async def get_pending_reviews(self):
        """Lấy danh sách review đang chờ duyệt"""
        async with aiosqlite.connect(self.db_name) as conn:
            conn.row_factory = aiosqlite.Row
            cursor = await conn.execute("""
                SELECT review_id, customer_name, review_text, sentiment, ai_reply
                FROM reviews
                WHERE status = 'Pending'
            """)
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
