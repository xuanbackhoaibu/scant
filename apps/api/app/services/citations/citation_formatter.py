from typing import Any, Dict, List, Optional


class CitationFormatter:
    """Formats academic in-text citations and reference list bibliographies."""

    @staticmethod
    def format_in_text(citation_number: int, author: Optional[str] = None, year: Optional[str] = None, style: str = "IEEE") -> str:
        style_upper = style.upper()
        if style_upper == "IEEE":
            return f"[{citation_number}]"
        elif style_upper == "APA" or style_upper == "APA7":
            auth_str = (author or "Anonymous").split(",")[0].split()[0]
            year_str = year or "n.d."
            return f"({auth_str}, {year_str})"
        elif style_upper == "HARVARD":
            auth_str = (author or "Anonymous").split(",")[0].split()[0]
            year_str = year or "n.d."
            return f"({auth_str} {year_str})"
        elif style_upper == "VANCOUVER":
            return f"({citation_number})"
        return f"[{citation_number}]"

    @staticmethod
    def format_bibliography_entry(index: int, source: Dict[str, Any], style: str = "IEEE") -> str:
        style_upper = style.upper()
        title = source.get("title", "Untitled Document")
        authors = source.get("authors") or "Anonymous"
        publisher = source.get("publisher") or "Web Publication"
        year = source.get("published_date") or "2024"
        url = source.get("url") or ""

        if style_upper == "IEEE":
            if url:
                return f"[{index}] {authors}, \"{title},\" {publisher}, {year}. [Online]. Available: {url}."
            return f"[{index}] {authors}, \"{title},\" {publisher}, {year}."

        elif style_upper in ["APA", "APA7"]:
            if url:
                return f"{authors} ({year}). {title}. {publisher}. {url}"
            return f"{authors} ({year}). {title}. {publisher}."

        elif style_upper == "HARVARD":
            if url:
                return f"{authors}, {year}. {title}. {publisher}. Available at: <{url}>."
            return f"{authors}, {year}. {title}. {publisher}."

        # Default IEEE
        return f"[{index}] {authors}, \"{title},\" {publisher}, {year}."


citation_formatter = CitationFormatter()
