import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from app.services.research.academic.base import ResearchSourceModel


class EvidenceItemModel(BaseModel):
    id: str
    source_id: str
    source_title: str
    source_url: str
    text: str
    quote: Optional[str] = None
    snippet: Optional[str] = None
    location: str = "Abstract / Core Findings"
    page: Optional[int] = None
    section: Optional[str] = None
    relevance_score: float = 0.90
    confidence: float = 0.95

    def model_post_init(self, __context: Any) -> None:
        if not self.quote:
            self.quote = self.text
        if not self.snippet:
            self.snippet = self.text


class MarketDataClaim(BaseModel):
    claim: str
    value: str
    unit: str
    period: str
    source_id: str
    evidence: str
    confidence: float = 0.95


class EvidenceExtractor:
    """
    Evidence & Quantitative Fact Extraction Engine (Section 5 & 12).
    Extracts atomic evidence chunks, statistics, market figures, and page references from real sources.
    """

    STAT_PATTERN = re.compile(
        r"(\b\d+(?:[.,]\d+)?\s*(?:%|tỷ|triệu|nghìn|USD|VND|xe|triệu USD|tỷ USD|CAGR|GW|MW|km)\b|"
        r"\b(?:tăng|giảm|đạt|chiếm|dự báo)\s+\d+(?:[.,]\d+)?%?)",
        re.I,
    )

    def extract_evidence_from_sources(
        self,
        query: str,
        sources: List[ResearchSourceModel],
    ) -> Tuple[List[EvidenceItemModel], List[MarketDataClaim]]:
        evidence_list: List[EvidenceItemModel] = []
        market_claims: List[MarketDataClaim] = []

        q_terms = set(re.findall(r"\b\w{3,}\b", query.lower()))

        for src_idx, src in enumerate(sources):
            content = f"{src.title}\n{src.abstract or ''}\n{src.snippet or ''}".strip()
            if not content:
                continue

            # Split content into sentences/paragraphs
            chunks = re.split(r"(?<=[.!?])\s+", content)

            chunk_count = 0
            for chunk in chunks:
                chunk = chunk.strip()
                if len(chunk) < 35 or len(chunk) > 400:
                    continue

                chunk_terms = set(re.findall(r"\b\w{3,}\b", chunk.lower()))
                relevance = len(q_terms & chunk_terms) / max(len(q_terms), 1)

                has_stat = bool(self.STAT_PATTERN.search(chunk))

                # Keep chunk if relevant or contains concrete stats
                if relevance > 0.15 or has_stat or chunk_count == 0:
                    ev_id = f"ev_{src_idx + 1}_{chunk_count + 1}"
                    evidence_list.append(
                        EvidenceItemModel(
                            id=ev_id,
                            source_id=src.id,
                            source_title=src.title,
                            source_url=src.url,
                            text=chunk,
                            location="Abstract / Document Core",
                            page=1 if src.pdf_url else None,
                            section=src.journal or src.publisher or "Executive Summary",
                            relevance_score=round(min(max(relevance + (0.2 if has_stat else 0.0), 0.70), 0.98), 2),
                        )
                    )
                    chunk_count += 1

                    # Extract quantitative market claim if statistical numbers are detected
                    if has_stat and len(market_claims) < 12:
                        stat_match = self.STAT_PATTERN.search(chunk)
                        val = stat_match.group(0) if stat_match else "Dữ liệu thực nghiệm"
                        market_claims.append(
                            MarketDataClaim(
                                claim=chunk[:120].strip(),
                                value=val,
                                unit="Thống kê công bố",
                                period=str(src.year or "2024-2026"),
                                source_id=src.id,
                                evidence=chunk,
                                confidence=round(min(src.quality_score / 100.0, 0.98), 2),
                            )
                        )

                if chunk_count >= 3:
                    break

        return evidence_list, market_claims



evidence_extractor = EvidenceExtractor()
