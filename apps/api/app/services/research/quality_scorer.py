import re
from typing import Any, Dict, List, Set
from app.services.research.academic.base import ResearchSourceModel


class SourceQualityScorer:
    """
    Code-calculated Source Quality Engine (Section 9, 10 & 11).
    Calculates transparent 0-100 quality score using the exact weighted formula:
      qualityScore = authority * 0.25
                   + metadataCompleteness * 0.15
                   + relevance * 0.30
                   + recency * 0.10
                   + citationSignal * 0.10
                   + verification * 0.10
    """

    CURRENT_YEAR = 2026

    def score_sources(self, query: str, sources: List[ResearchSourceModel]) -> List[ResearchSourceModel]:
        query_tokens = self._tokenize(query)

        scored: List[ResearchSourceModel] = []
        for src in sources:
            breakdown = self.calculate_breakdown(query_tokens, src)
            total_score = round(
                (
                    breakdown["authority"] * 0.25
                    + breakdown["metadata_completeness"] * 0.15
                    + breakdown["relevance"] * 0.30
                    + breakdown["recency"] * 0.10
                    + breakdown["citation_signal"] * 0.10
                    + breakdown["verification"] * 0.10
                )
                * 100,
                1,
            )

            updated = src.model_copy(
                update={
                    "quality_score": min(max(total_score, 10.0), 100.0),
                    "quality_breakdown": breakdown,
                }
            )
            scored.append(updated)

        # Sort descending by quality_score
        scored.sort(key=lambda s: s.quality_score, reverse=True)
        return scored

    def calculate_breakdown(self, query_tokens: Set[str], src: ResearchSourceModel) -> Dict[str, float]:
        # 1. Authority (0.0 to 1.0)
        authority = self._calc_authority(src)

        # 2. Metadata Completeness (0.0 to 1.0)
        completeness = self._calc_metadata_completeness(src)

        # 3. Relevance (0.0 to 1.0)
        relevance = self._calc_relevance(query_tokens, src)

        # 4. Recency (0.0 to 1.0)
        recency = self._calc_recency(src)

        # 5. Citation Signal (0.0 to 1.0)
        citation_signal = self._calc_citation_signal(src)

        # 6. Verification (0.0 to 1.0)
        verification = self._calc_verification(src)

        return {
            "authority": round(authority, 3),
            "metadata_completeness": round(completeness, 3),
            "relevance": round(relevance, 3),
            "recency": round(recency, 3),
            "citation_signal": round(citation_signal, 3),
            "verification": round(verification, 3),
        }

    def _calc_authority(self, src: ResearchSourceModel) -> float:
        st = (src.source_type or "").lower()
        prov = (src.provider or "").lower()

        if prov in ("crossref", "arxiv", "pubmed") or st == "academic":
            return 0.95
        if st == "government":
            return 0.95
        if st == "organization":
            return 0.92
        if st == "market":
            return 0.82
        if st == "news":
            return 0.75
        if st == "company":
            return 0.78
        return 0.60

    def _calc_metadata_completeness(self, src: ResearchSourceModel) -> float:
        points = 0.0
        if src.title and len(src.title) > 5:
            points += 0.20
        if src.authors and len(src.authors) > 0:
            points += 0.20
        if src.publisher or src.journal:
            points += 0.20
        if src.year or src.published_at:
            points += 0.15
        if src.doi or src.arxiv_id or src.pmid:
            points += 0.15
        if src.abstract or src.snippet:
            points += 0.10
        return min(points, 1.0)

    def _calc_relevance(self, query_tokens: Set[str], src: ResearchSourceModel) -> float:
        if not query_tokens:
            return 0.70

        title_tokens = self._tokenize(src.title)
        snippet_tokens = self._tokenize(f"{src.abstract or ''} {src.snippet or ''}")

        title_overlap = len(query_tokens & title_tokens) / len(query_tokens)
        snippet_overlap = len(query_tokens & snippet_tokens) / len(query_tokens)

        # Award strong credit for title match or snippet match
        score = max(title_overlap * 0.85 + 0.20, snippet_overlap * 0.70 + 0.25)
        return min(max(score, 0.55), 1.0)

    def _calc_recency(self, src: ResearchSourceModel) -> float:
        if not src.year:
            return 0.75
        diff = self.CURRENT_YEAR - src.year
        if diff <= 1:  # 2025 - 2026
            return 1.0
        elif diff <= 3:  # 2023 - 2024
            return 0.90
        elif diff <= 5:  # 2021 - 2022
            return 0.80
        elif diff <= 10:
            return 0.65
        return 0.50

    def _calc_citation_signal(self, src: ResearchSourceModel) -> float:
        count = src.citation_count
        if count is None:
            # Default moderate-high score if citation count is unindexed (e.g. newly published)
            return 0.75
        if count >= 100:
            return 1.0
        elif count >= 30:
            return 0.95
        elif count >= 10:
            return 0.88
        elif count >= 1:
            return 0.80
        return 0.65

    def _calc_verification(self, src: ResearchSourceModel) -> float:
        score = 0.60
        if src.url_verified:
            score += 0.25
        if src.metadata_verified:
            score += 0.15
        if "✓ Multi-Provider Cross-Checked" in src.verification_badges:
            score += 0.05
        return min(score, 1.0)

    def _tokenize(self, text: str) -> Set[str]:
        if not text:
            return set()
        words = re.findall(r"\b\w{2,}\b", text.lower())
        stopwords = {
            "the", "and", "for", "with", "from", "to", "of", "in", "on", "at", "by", "is", "it",
            "về", "của", "cho", "trong", "các", "những", "năm", "tại", "một", "được", "nghiên", "cứu"
        }
        return {w for w in words if w not in stopwords}


source_quality_scorer = SourceQualityScorer()
