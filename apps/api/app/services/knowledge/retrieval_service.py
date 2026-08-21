import math
import re
from typing import Any, Dict, List, Optional
from app.services.knowledge.chunker import document_chunker


class ContextRetrievalService:
    """
    RAG Retrieval Engine with BM25/Cosine relevance scoring and Reranking.
    Prevents prompt flooding by retrieving only top 3-5 relevant evidence chunks.
    """

    @classmethod
    def _tokenize(cls, text: str) -> List[str]:
        return re.findall(r"\w+", text.lower())

    @classmethod
    def calculate_bm25_score(cls, query_tokens: List[str], chunk_tokens: List[str], avg_len: float) -> float:
        if not chunk_tokens:
            return 0.0

        k1 = 1.5
        b = 0.75
        score = 0.0
        doc_len = len(chunk_tokens)

        for q in query_tokens:
            count = chunk_tokens.count(q)
            if count > 0:
                tf = (count * (k1 + 1)) / (count + k1 * (1 - b + b * (doc_len / (avg_len or 1.0))))
                score += tf

        return score

    @classmethod
    def search_relevant_chunks(
        cls,
        query: str,
        documents: List[Dict[str, Any]],  # [{id, original_name, content_text}]
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        query_tokens = cls._tokenize(query)
        if not query_tokens:
            return []

        all_chunks: List[Dict[str, Any]] = []
        for doc in documents:
            text = doc.get("content_text") or ""
            doc_id = doc.get("id")
            doc_name = doc.get("original_name") or "Document"
            chunks = document_chunker.chunk_text(text)

            for c in chunks:
                c["doc_id"] = doc_id
                c["doc_name"] = doc_name
                c["tokens"] = cls._tokenize(c["text"])
                all_chunks.append(c)

        if not all_chunks:
            return []

        avg_len = sum(len(c["tokens"]) for c in all_chunks) / len(all_chunks)

        # Score all chunks
        for c in all_chunks:
            c["score"] = cls.calculate_bm25_score(query_tokens, c["tokens"], avg_len)

        # Sort descending by score
        ranked = sorted(all_chunks, key=lambda x: x["score"], reverse=True)

        results = []
        for r in ranked[:top_k]:
            if r["score"] > 0:
                results.append({
                    "doc_id": r["doc_id"],
                    "doc_name": r["doc_name"],
                    "chunk_index": r["chunk_index"],
                    "text": r["text"],
                    "relevance_score": round(r["score"], 3),
                })

        return results


retrieval_service = ContextRetrievalService()
