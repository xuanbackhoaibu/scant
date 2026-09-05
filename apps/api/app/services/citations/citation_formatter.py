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

    @staticmethod
    def format_bibtex(index: int, source: Dict[str, Any]) -> str:
        title = source.get("title", "Untitled Document")
        authors = source.get("authors") or "Anonymous"
        publisher = source.get("publisher") or source.get("journal") or "Publication"
        year = source.get("published_date") or source.get("year") or "2026"
        url = source.get("url") or ""
        doi = source.get("doi") or ""

        first_auth = authors.split(",")[0].split()[-1].lower() if authors else "ref"
        key = f"{first_auth}{year}_{index}"

        lines = [
            f"@article{{{key},",
            f"  title = {{{title}}},",
            f"  author = {{{authors}}},",
            f"  journal = {{{publisher}}},",
            f"  year = {{{year}}},",
        ]
        if doi:
            lines.append(f"  doi = {{{doi}}},")
        if url:
            lines.append(f"  url = {{{url}}},")
        lines.append("}")
        return "\n".join(lines)

    @staticmethod
    def format_ris(index: int, source: Dict[str, Any]) -> str:
        title = source.get("title", "Untitled Document")
        authors = source.get("authors") or "Anonymous"
        publisher = source.get("publisher") or source.get("journal") or "Publication"
        year = source.get("published_date") or source.get("year") or "2026"
        url = source.get("url") or ""
        doi = source.get("doi") or ""

        lines = [
            "TY  - JOUR",
            f"TI  - {title}",
            f"AU  - {authors}",
            f"T2  - {publisher}",
            f"PY  - {year}",
        ]
        if doi:
            lines.append(f"DO  - {doi}")
        if url:
            lines.append(f"UR  - {url}")
        lines.append("ER  - ")
        return "\n".join(lines)

    def format_sources(self, sources: List[Any], style: str = "IEEE") -> str:
        """Formats a list of source models or dicts in the requested academic style."""
        style_upper = style.upper()
        formatted_entries = []

        for idx, src in enumerate(sources):
            if hasattr(src, "model_dump"):
                d = src.model_dump()
            elif isinstance(src, dict):
                d = src
            else:
                d = vars(src)

            authors_val = d.get("authors")
            if isinstance(authors_val, list):
                authors_str = ", ".join(authors_val)
            else:
                authors_str = authors_val or "Anonymous"

            src_dict = {
                "title": d.get("title", ""),
                "authors": authors_str,
                "publisher": d.get("publisher") or d.get("journal") or "",
                "published_date": str(d.get("year") or d.get("published_date") or "2026"),
                "url": d.get("url", ""),
                "doi": d.get("doi", ""),
            }

            if style_upper == "BIBTEX":
                formatted_entries.append(self.format_bibtex(idx + 1, src_dict))
            elif style_upper == "RIS":
                formatted_entries.append(self.format_ris(idx + 1, src_dict))
            else:
                formatted_entries.append(self.format_bibliography_entry(idx + 1, src_dict, style=style_upper))

        sep = "\n\n" if style_upper in ("BIBTEX", "RIS") else "\n"
        return sep.join(formatted_entries)


citation_formatter = CitationFormatter()
