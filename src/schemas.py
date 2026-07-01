from pydantic import BaseModel
from typing import Optional, Any

class Hit(BaseModel):
    _internal_id: int
    score: float
    source: Optional[str]
    chunk_id: Optional[int]
    text_preview: Optional[str]
