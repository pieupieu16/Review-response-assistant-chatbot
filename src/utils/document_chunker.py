"""Structure-aware semantic chunking and document metadata."""

import os
import re
from typing import TypedDict

from langchain_text_splitters import RecursiveCharacterTextSplitter

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "800"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "150"))

SECTION_HEADER_PATTERNS = [
    r"^Quy\s",
    r"^Điều kiện",
    r"^Bước\s+\d+",
    r"^CHỈ\s",
    r"^Lưu ý",
    r"^Hình thức",
    r"^Không\s",
    r"^Những\s",
    r"^Mục tiêu",
    r"^Hoàn tiền",
    r"^TADICO\s",
]


class ChunkRecord(TypedDict):
    text: str
    section: str


class DocumentMetadata(TypedDict):
    source: str
    policy_type: str
    category: str
    product_scope: str


def _is_section_header(line: str) -> bool:
    line = line.strip()
    if not line or len(line) > 120:
        return False
    return any(re.match(pattern, line, re.IGNORECASE) for pattern in SECTION_HEADER_PATTERNS)


def _fallback_splitter() -> RecursiveCharacterTextSplitter:
    return RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n\n", "\n", "• ", "* ", ". ", " "],
    )


def _split_oversized_section(text: str, section: str) -> list[ChunkRecord]:
    if len(text) <= CHUNK_SIZE:
        return [{"text": text, "section": section}]

    chunks = []
    for piece in _fallback_splitter().split_text(text):
        chunks.append({"text": piece, "section": section})
    return chunks


def semantic_chunk_document(text: str) -> list[ChunkRecord]:
    """Chunk by paragraph/section boundaries; split only when a section is too large."""
    text = text.strip()
    if not text:
        return []

    blocks = [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]
    if not blocks:
        return []

    chunks: list[ChunkRecord] = []
    current_section = blocks[0].split("\n", 1)[0].strip()[:120]
    current_text = ""

    for block in blocks:
        first_line = block.split("\n", 1)[0].strip()

        if _is_section_header(first_line) and current_text:
            chunks.extend(_split_oversized_section(current_text.strip(), current_section))
            current_section = first_line[:120]
            current_text = block
            continue

        if _is_section_header(first_line):
            current_section = first_line[:120]

        candidate = f"{current_text}\n\n{block}".strip() if current_text else block
        if len(candidate) <= CHUNK_SIZE:
            current_text = candidate
        else:
            if current_text:
                chunks.extend(_split_oversized_section(current_text.strip(), current_section))
            current_section = first_line[:120] if _is_section_header(first_line) else current_section
            current_text = block

    if current_text:
        chunks.extend(_split_oversized_section(current_text.strip(), current_section))

    return chunks


def infer_document_metadata(file_path: str) -> DocumentMetadata:
    """Infer policy metadata from filename for ChromaDB pre-filtering."""
    file_name = os.path.basename(file_path)
    name_lower = file_name.lower()

    if "đổi trả" in name_lower:
        return {
            "source": file_name,
            "policy_type": "return_policy",
            "category": "chính_sách_đổi_trả",
            "product_scope": "general",
        }
    if "khiếu nại" in name_lower or "phàn n" in name_lower:
        return {
            "source": file_name,
            "policy_type": "complaint_handling",
            "category": "xử_lý_khiếu_nại",
            "product_scope": "general",
        }
    if "câu hỏi" in name_lower or "faq" in name_lower:
        return {
            "source": file_name,
            "policy_type": "faq",
            "category": "hỏi_đáp",
            "product_scope": "general",
        }

    return {
        "source": file_name,
        "policy_type": "general",
        "category": "chung",
        "product_scope": "general",
    }


def infer_query_filter(query: str) -> dict | None:
    """Lightweight metadata pre-filter based on query intent."""
    normalized = query.lower()

    if any(keyword in normalized for keyword in ["đổi trả", "hoàn tiền", "trả hàng", "bảo hành", "lỗi kỹ thuật"]):
        return {"policy_type": "return_policy"}
    if any(keyword in normalized for keyword in ["khiếu nại", "phàn nàn", "bức xúc", "xử lý"]):
        return {"policy_type": "complaint_handling"}
    if any(keyword in normalized for keyword in ["hỏi", "faq", "là gì", "thường gặp"]):
        return {"policy_type": "faq"}

    return None
