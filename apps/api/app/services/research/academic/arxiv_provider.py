import re
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from app.services.research.academic.base import AcademicProvider, ResearchSourceModel


class ArxivProvider(AcademicProvider):
    """
    Real Academic Search Provider using arXiv API (Section 3.C).
    Queries arXiv.org open scientific repository for preprints and research papers.
    """
    name = "arxiv"
    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    async def search(self, query: str, limit: int = 10, **kwargs) -> List[ResearchSourceModel]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        # arXiv query format: all:keyword
        formatted_query = f"all:{cleaned_query}"
        params = {
            "search_query": formatted_query,
            "start": 0,
            "max_results": min(max(limit, 1), 25),
            "sortBy": "relevance",
            "sortOrder": "descending",
        }

        results: List[ResearchSourceModel] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                res = await client.get(self.BASE_URL, params=params)
                if res.status_code != 200:
                    return []

                soup = BeautifulSoup(res.text, "xml")
                entries = soup.find_all("entry")

                for entry in entries:
                    source = self._parse_entry(entry)
                    if source:
                        results.append(source)
        except Exception:
            return []

        return results

    def _parse_entry(self, entry: Any) -> Optional[ResearchSourceModel]:
        title_el = entry.find("title")
        if not title_el:
            return None

        title = title_el.get_text().replace("\n", " ").strip()
        if not title or title.lower() == "error":
            return None

        id_url = entry.find("id").get_text().strip() if entry.find("id") else ""
        arxiv_id_match = re.search(r"arxiv\.org/abs/([0-9]+\.[0-9]+(?:v[0-9]+)?)", id_url)
        arxiv_id = arxiv_id_match.group(1) if arxiv_id_match else id_url.split("/")[-1]

        paper_url = f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else id_url
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf" if arxiv_id else None

        # Authors
        authors: List[str] = []
        for author_el in entry.find_all("author"):
            name_el = author_el.find("name")
            if name_el:
                authors.append(name_el.get_text().strip())

        # Abstract
        summary_el = entry.find("summary")
        abstract = summary_el.get_text().replace("\n", " ").strip() if summary_el else None

        # Publication date and year
        published_el = entry.find("published")
        published_at = published_el.get_text().strip() if published_el else None
        year = int(published_at[:4]) if published_at and published_at[:4].isdigit() else None

        # DOI if present in arXiv entry
        doi_el = entry.find("arxiv:doi")
        doi = doi_el.get_text().strip() if doi_el else None

        source_id = f"arxiv_{arxiv_id.replace('.', '_')}"

        return ResearchSourceModel(
            id=source_id,
            source_type="academic",
            title=title,
            authors=authors,
            publisher="arXiv.org e-Print Archive",
            journal="arXiv Preprint",
            published_at=published_at,
            year=year,
            doi=doi,
            arxiv_id=arxiv_id,
            url=paper_url,
            abstract=abstract,
            snippet=abstract[:300] if abstract else None,
            open_access=True,
            pdf_url=pdf_url,
            provider="arxiv",
            metadata_verified=True,
            url_verified=True,
            authority_type="scientific preprint repository",
            verification_badges=["✓ arXiv Verified", "✓ Open Access"],
        )
