import glob
import hashlib
import os

import chromadb
from dotenv import load_dotenv
from pypdf import PdfReader

from retrieval.embeddings import MultilingualE5EmbeddingFunction
from retrieval.reranker import PassageReranker
from utils.document_chunker import (
    infer_document_metadata,
    infer_query_filter,
    semantic_chunk_document,
)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

DEFAULT_COLLECTION = os.getenv("CHROMA_COLLECTION_NAME", "cskh_policies_v2")
RETRIEVE_K = int(os.getenv("RETRIEVE_K", "10"))
FINAL_TOP_K = int(os.getenv("FINAL_TOP_K", "3"))


def _resolve_path(env_var: str, default_relative: str) -> str:
    path = os.getenv(env_var, default_relative)
    if not os.path.isabs(path):
        path = os.path.join(PROJECT_ROOT, path)
    return os.path.normpath(path)


def _chunk_id(chunk_text: str) -> str:
    """ID ổn định theo nội dung — tránh lệch index khi file thay đổi."""
    return hashlib.sha256(chunk_text.encode("utf-8")).hexdigest()


class CustomerCareVectorDB:
    def __init__(self, db_path=None, collection_name=None):
        if db_path is None:
            db_path = _resolve_path("CHROMA_DB_PATH", os.path.join("data", "chroma_db"))

        self.chroma_client = chromadb.PersistentClient(path=db_path)
        self.embedding_fn = MultilingualE5EmbeddingFunction()
        self.reranker = PassageReranker()
        self.collection_name = collection_name or DEFAULT_COLLECTION

        self.collection = self.chroma_client.get_or_create_collection(
            name=self.collection_name,
            embedding_function=self.embedding_fn,
        )

    def read_text_file(self, file_path):
        with open(file_path, "r", encoding="utf-8") as file:
            return file.read()

    def read_pdf_file(self, file_path):
        text = ""
        reader = PdfReader(file_path)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text

    def delete_chunks_by_source(self, file_name: str) -> int:
        """Xóa toàn bộ chunk cũ của một file trước khi ingest lại."""
        existing = self.collection.get(where={"source": file_name}, include=[])
        ids = existing.get("ids") or []
        if ids:
            self.collection.delete(ids=ids)
        return len(ids)

    def ingest_document(self, file_path):
        if not os.path.exists(file_path):
            print(f"Lỗi: Không tìm thấy file tại {file_path}")
            return

        file_ext = os.path.splitext(file_path)[1].lower()
        if file_ext == ".txt":
            text = self.read_text_file(file_path)
        elif file_ext == ".pdf":
            text = self.read_pdf_file(file_path)
        else:
            print(f"Bỏ qua định dạng không hỗ trợ: {file_ext}")
            return

        if not text.strip():
            print(f"Cảnh báo: File rỗng hoặc không có văn bản: {file_path}")
            return

        doc_metadata = infer_document_metadata(file_path)
        chunk_records = semantic_chunk_document(text)
        if not chunk_records:
            return

        file_name = doc_metadata["source"]
        removed = self.delete_chunks_by_source(file_name)
        if removed:
            print(f"↻ Đã xóa {removed} chunk cũ của file: {file_name}")

        documents = [record["text"] for record in chunk_records]
        ids = [_chunk_id(chunk) for chunk in documents]
        metadatas = [
            {
                **doc_metadata,
                "section": record["section"],
            }
            for record in chunk_records
        ]

        self.collection.add(
            documents=documents,
            metadatas=metadatas,
            ids=ids,
        )
        print(f"➔ Đã nạp thành công {len(documents)} đoạn từ file: {file_name}")

    def ingest_folder(self, folder_path):
        if not os.path.exists(folder_path):
            print(f"Lỗi: Thư mục không tồn tại: {folder_path}")
            return

        all_files = glob.glob(os.path.join(folder_path, "*"))
        print(f"Tìm thấy {len(all_files)} mục trong {folder_path}. Bắt đầu nạp dữ liệu...")
        for file_path in all_files:
            if os.path.isfile(file_path):
                self.ingest_document(file_path)
        print("Quá trình nạp toàn bộ thư mục hoàn tất!")

    def _query_collection(self, query_embedding, n_results, metadata_filter=None):
        query_kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": n_results,
        }
        if metadata_filter:
            query_kwargs["where"] = metadata_filter
        return self.collection.query(**query_kwargs)

    def retrieve_context(self, query, top_k=None):
        """Retrieve top passages with metadata pre-filtering and cross-encoder reranking."""
        final_k = top_k or FINAL_TOP_K
        query_embedding = self.embedding_fn.embed_query(query)
        metadata_filter = infer_query_filter(query)

        results = self._query_collection(query_embedding, RETRIEVE_K, metadata_filter)
        documents = results["documents"][0] if results.get("documents") else []

        if not documents and metadata_filter:
            results = self._query_collection(query_embedding, RETRIEVE_K, None)
            documents = results["documents"][0] if results.get("documents") else []

        return self.reranker.rerank(query, documents, top_k=final_k)


if __name__ == "__main__":
    vdb = CustomerCareVectorDB()
    raw_data_folder = _resolve_path("DATA_RAW_PATH", os.path.join("data", "raw"))
    vdb.ingest_folder(raw_data_folder)

    sample_query = "Quy trình xử lý khiếu nại đổi trả sản phẩm bị lỗi"
    context = vdb.retrieve_context(sample_query)
    print("\n[Kết quả tìm kiếm thử nghiệm sau rerank]")
    for index, doc in enumerate(context, start=1):
        print(f"Đoạn {index}: {doc[:200]}...")
