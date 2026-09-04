import re
from typing import Any, Dict, List


class TemplateCleaner:
    """Keeps DOCX template structure while removing sample/prompt content from LLM context."""

    BLOCK_PATTERNS = [
        r"\[[^\]\n]*(?:NỘI DUNG|NOI DUNG|CHÈN ẢNH|CHEN ANH|GỢI Ý|GOI Y)[^\]\n]*\]",
        r"(?im)^\s*Gợi ý cho AI viết:.*$",
        r"(?im)^\s*PROMPT TỔNG HỢP.*$",
        r"(?im)^\s*CHECKLIST TRƯỚC KHI NỘP.*$",
        r"(?im)^\s*TODO\b.*$",
        r"(?im)^\s*Lorem ipsum.*$",
        r"(?im)^\s*Ignore previous instructions.*$",
    ]

    PLACEHOLDER_PATTERNS = [
        "…………",
        "......",
        "[NỘI DUNG",
        "[CHÈN ẢNH",
        "[GỢI Ý",
        "Gợi ý cho AI viết",
        "PROMPT TỔNG HỢP",
        "CHECKLIST TRƯỚC KHI NỘP",
    ]

    @classmethod
    def clean_text(cls, text: str) -> str:
        cleaned = text or ""
        for pattern in cls.BLOCK_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    @classmethod
    def is_sample_or_placeholder(cls, text: str) -> bool:
        normalized = (text or "").strip()
        if not normalized:
            return True
        upper = normalized.upper()
        if any(marker.upper() in upper for marker in cls.PLACEHOLDER_PATTERNS):
            return True
        if re.fullmatch(r"[\.\-_–—…\s]{4,}", normalized):
            return True
        return False

    @classmethod
    def clean_paragraphs(cls, paragraphs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        cleaned: List[Dict[str, Any]] = []
        for paragraph in paragraphs or []:
            text = cls.clean_text(str(paragraph.get("text") or ""))
            if cls.is_sample_or_placeholder(text) and not paragraph.get("is_heading"):
                continue
            cleaned.append({**paragraph, "text": text})
        return cleaned

    @classmethod
    def build_structure_context(cls, parsed: Dict[str, Any]) -> Dict[str, Any]:
        headings = [
            {
                "text": cls.clean_text(h.get("text") or ""),
                "level": h.get("level") or 1,
            }
            for h in parsed.get("headings", [])
            if not cls.is_sample_or_placeholder(h.get("text") or "")
        ]
        paragraphs = cls.clean_paragraphs(parsed.get("paragraphs", []))
        return {
            "headings": headings,
            "paragraphs": paragraphs[:80],
            "tables_count": parsed.get("tables_count", 0),
            "sections": parsed.get("sections", []),
            "full_text": "\n".join(p["text"] for p in paragraphs if p.get("text")),
            "sample_content_removed": True,
            "blocked_patterns": cls.PLACEHOLDER_PATTERNS,
        }


template_cleaner = TemplateCleaner()
