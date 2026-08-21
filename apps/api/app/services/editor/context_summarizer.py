from typing import Any, Dict, List, Optional
from app.models.entities import ReportSection


class ContextSummarizer:
    """Maintains consistent chapter context summaries to ensure coherence across 50+ page reports."""

    @staticmethod
    def build_chain_summary(previous_sections: List[ReportSection]) -> str:
        if not previous_sections:
            return "Đây là phần mở đầu của báo cáo."

        summaries: List[str] = []
        for sec in previous_sections[-4:]:  # keep last 4 sections for immediate context
            if sec.plain_text:
                preview = sec.plain_text[:200].replace("\n", " ")
                summaries.append(f"- {sec.title}: {preview}...")

        return "\n".join(summaries)


context_summarizer = ContextSummarizer()
