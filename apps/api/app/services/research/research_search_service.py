import asyncio
import logging
import re
from typing import Any, Dict, List, Optional, Set
from app.services.research.academic.base import ResearchSourceModel
from app.services.research.academic.crossref_provider import CrossrefProvider
from app.services.research.academic.openalex_provider import OpenAlexProvider
from app.services.research.academic.arxiv_provider import ArxivProvider
from app.services.research.academic.semantic_scholar_provider import SemanticScholarProvider
from app.services.research.academic.microsoft_learn_provider import MicrosoftLearnProvider
from app.services.research.web_search import WebSearchProvider

logger = logging.getLogger("research.search_service")


class ResearchSearchService:
    """
    Unified Multi-Provider Research Search Engine.
    Coordinates genuine sources from Academic repositories, Official Vendor Documentation,
    and live web feeds.
    Strictly Anti-Hallucination: Never fabricates papers, URLs, DOIs, authors, or publication years.
    """

    def __init__(self):
        self.crossref = CrossrefProvider()
        self.openalex = OpenAlexProvider()
        self.arxiv = ArxivProvider()
        self.semantic_scholar = SemanticScholarProvider()
        self.microsoft_learn = MicrosoftLearnProvider()
        self.web_search = WebSearchProvider()

    @staticmethod
    def _normalize_title(title: str) -> str:
        clean = re.sub(r"[^\w\s]", "", title.lower())
        return " ".join(clean.split())

    @staticmethod
    def _canonical_url(url: str) -> str:
        clean = url.split("#")[0].split("?")[0].rstrip("/")
        clean = re.sub(r"^https?://(www\.)?", "", clean.lower())
        return clean

    async def search(
        self,
        query: str,
        source_type: Optional[str] = None,
        provider: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        sort: str = "RELEVANCE",
        limit: int = 15,
    ) -> Dict[str, Any]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return {"query": "", "total": 0, "results": [], "providers_queried": []}

        lower_query = cleaned_query.lower()
        tasks = []
        provider_names = []

        # 1. Select appropriate providers based on query intent & filters
        is_tech_or_ms = any(k in lower_query for k in [
            "asp.net", "dotnet", ".net", "c#", "microsoft", "azure", "entity framework",
            "mvc", "blazor", "linq", "jwt", "identity", "dependency injection", "web api"
        ])
        is_academic_intent = any(k in lower_query for k in [
            "paper", "research", "study", "journal", "ieee", "acm", "algorithm",
            "survey", "evaluation", "empirical", "model", "analysis", "phương pháp", "nghiên cứu"
        ])

        # Microsoft Learn Official Docs
        if (not provider or provider == "microsoft_learn") and (is_tech_or_ms or source_type == "OFFICIAL_DOCUMENTATION"):
            tasks.append(self.microsoft_learn.search(cleaned_query, limit=limit))
            provider_names.append("microsoft_learn")

        # OpenAlex (Open Academic Catalog)
        if not provider or provider == "openalex":
            tasks.append(self.openalex.search(cleaned_query, limit=limit))
            provider_names.append("openalex")

        # Crossref (Official DOI Registry)
        if not provider or provider == "crossref":
            tasks.append(self.crossref.search(cleaned_query, limit=limit))
            provider_names.append("crossref")

        # arXiv (Preprints)
        if not provider or provider == "arxiv":
            tasks.append(self.arxiv.search(cleaned_query, limit=limit))
            provider_names.append("arxiv")

        # Web search (Google News VN, Bing Web, Live Portals)
        if (not provider or provider == "web") and (not source_type or source_type in ["WEB_ARTICLE", "GOVERNMENT_SOURCE", "ORGANIZATION_SOURCE"]):
            tasks.append(self.web_search.search(cleaned_query, limit=limit))
            provider_names.append("web_search")

        # 2. Execute concurrently with graceful fault-tolerance
        results_nested = await asyncio.gather(*tasks, return_exceptions=True)

        all_sources: List[ResearchSourceModel] = []
        diagnostics: Dict[str, str] = {}

        for p_name, res in zip(provider_names, results_nested):
            if isinstance(res, Exception):
                logger.warning(f"Provider '{p_name}' failed: {res}")
                diagnostics[p_name] = f"Error: {str(res)[:120]}"
            elif isinstance(res, list):
                all_sources.extend(res)
                diagnostics[p_name] = f"Success ({len(res)} results)"

        # 3. Deduplication (by DOI, Canonical URL, and Normalized Title + Year)
        seen_dois: Set[str] = set()
        seen_urls: Set[str] = set()
        seen_titles: Set[str] = set()
        deduped: List[ResearchSourceModel] = []

        for s in all_sources:
            if s.doi:
                norm_doi = s.doi.lower().strip()
                if norm_doi in seen_dois:
                    continue
                seen_dois.add(norm_doi)

            if s.url:
                c_url = self._canonical_url(s.url)
                if c_url in seen_urls:
                    continue
                seen_urls.add(c_url)

            n_title = self._normalize_title(s.title)
            title_key = f"{n_title}_{s.year or ''}"
            if len(n_title) > 10 and title_key in seen_titles:
                continue
            seen_titles.add(title_key)

            # 4. Filter by year if specified
            if year_from and s.year and s.year < year_from:
                continue
            if year_to and s.year and s.year > year_to:
                continue

            # 5. Filter by source_type if specified
            if source_type and source_type != "ALL":
                if s.source_type != source_type and s.authority_type != source_type.lower():
                    continue

            deduped.append(s)

        # 6. Genuine Sorting (no fake numbers)
        if sort == "NEWEST":
            deduped.sort(key=lambda x: (x.year or 0, x.published_at or ""), reverse=True)
        elif sort == "OLDEST":
            deduped.sort(key=lambda x: (x.year or 9999, x.published_at or "9999"))
        elif sort == "CITATION_COUNT":
            deduped.sort(key=lambda x: (x.citation_count or 0), reverse=True)
        elif sort == "VERIFICATION_SCORE":
            deduped.sort(key=lambda x: (x.quality_score or 0), reverse=True)
        else:  # RELEVANCE default
            # Balance relevance + verification
            deduped.sort(key=lambda x: (x.quality_score or 0) + (min(x.citation_count or 0, 50) * 0.4), reverse=True)

        return {
            "query": cleaned_query,
            "total": len(deduped),
            "results": [s.model_dump() for s in deduped[:limit]],
            "providers_queried": provider_names,
            "diagnostics": diagnostics,
        }

    async def search_all(
        self,
        query: str,
        providers: Optional[List[str]] = None,
        sort_by: str = "RELEVANCE",
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        res = await self.search(query=query, sort=sort_by, limit=limit)
        return res.get("results", [])


research_search_service = ResearchSearchService()
