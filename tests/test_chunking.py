from src.utils.document_chunker import CHUNK_OVERLAP, CHUNK_SIZE, semantic_chunk_document


def test_semantic_chunking_preserves_policy_sections():
    text = (
        "Quy định đổi trả\n\n"
        "Những trường hợp được đổi trả:\n"
        "Hàng bị lỗi kỹ thuật và lỗi do nhà sản xuất.\n\n"
        "Điều kiện và quy định đổi trả chung:\n"
        "Khách hàng có thể đổi trả trong vòng 7 ngày kể từ ngày nhận hàng. "
        "Sản phẩm phải còn nguyên tem, nhãn mác và chưa qua sử dụng."
    )
    chunks = semantic_chunk_document(text)

    assert len(chunks) >= 2
    assert all(len(chunk["text"]) <= CHUNK_SIZE + 50 for chunk in chunks)
    assert any("Điều kiện và quy định đổi trả chung" in chunk["text"] for chunk in chunks)
    assert CHUNK_OVERLAP < CHUNK_SIZE


def test_infer_query_filter_for_return_policy():
    from src.utils.document_chunker import infer_query_filter

    assert infer_query_filter("Sản phẩm bị lỗi có được đổi trả không?") == {
        "policy_type": "return_policy"
    }
