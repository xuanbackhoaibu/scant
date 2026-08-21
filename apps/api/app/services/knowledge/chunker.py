import re
from typing import Any, Dict, List


class DocumentChunker:
    """Splits large documents into overlapping chunks for precise context retrieval."""

    @staticmethod
    def chunk_text(text: str, chunk_size: int = 400, overlap: int = 50) -> List[Dict[str, Any]]:
        if not text or not text.strip():
            return []

        paragraphs = text.split("\n\n")
        chunks: List[Dict[str, Any]] = []
        current_words: List[str] = []
        chunk_idx = 0

        for p in paragraphs:
            words = p.strip().split()
            if not words:
                continue

            if len(current_words) + len(words) > chunk_size and current_words:
                chunk_str = " ".join(current_words)
                chunks.append({
                    "chunk_index": chunk_idx,
                    "text": chunk_str,
                    "word_count": len(current_words)
                })
                chunk_idx += 1
                # Keep overlap
                current_words = current_words[-overlap:] if len(current_words) > overlap else []

            current_words.extend(words)

        if current_words:
            chunk_str = " ".join(current_words)
            chunks.append({
                "chunk_index": chunk_idx,
                "text": chunk_str,
                "word_count": len(current_words)
            })

        return chunks


document_chunker = DocumentChunker()
