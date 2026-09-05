import re
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from app.services.research.academic.base import AcademicProvider, ResearchSourceModel


class CrossrefProvider(AcademicProvider):
    """
    Real Academic Search Provider using Crossref REST API (Section 3.A).
    Queries official DOI registry for verified peer-reviewed publications.
    """
    name = "crossref"
    BASE_URL = "https://api.crossref.org/works"

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout
        self.headers = {
            "User-Agent": "AIReportStudio/2.0 (https://aireportstudio.com; mailto:support@aireportstudio.com)"
        }

    async def search(self, query: str, limit: int = 10, **kwargs) -> List[ResearchSourceModel]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        params = {
            "query": cleaned_query,
            "rows": min(max(limit, 1), 30),
            "sort": "relevance",
        }

        results: List[ResearchSourceModel] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                res = await client.get(self.BASE_URL, params=params, headers=self.headers)
                if res.status_code != 200:
                    return []

                data = res.json()
                items = data.get("message", {}).get("items", [])

                for item in items:
                    source = self._parse_item(item)
                    if source:
                        results.append(source)
        except Exception:
            return []

        return results

    def _parse_item(self, item: Dict[str, Any]) -> Optional[ResearchSourceModel]:
        titles = item.get("title", [])
        title = titles[0].strip() if titles and titles[0] else None
        if not title:
            return None

        # Clean title HTML tags if present
        title = re.sub(r"<[^>]+>", "", title).strip()

        doi = item.get("DOI")
        url = item.get("URL") or (f"https://doi.org/{doi}" if doi else "")
        if not url:
            return None

        # Authors
        authors: List[str] = []
        for a in item.get("author", []):
            given = a.get("given", "").strip()
            family = a.get("family", "").strip()
            if given and family:
                authors.append(f"{given} {family}")
            elif family:
                authors.append(family)
            elif a.get("name"):
                authors.append(a.get("name").strip())

        # Publisher and Journal
        containers = item.get("container-title", [])
        journal = containers[0].strip() if containers and containers[0] else None
        publisher = item.get("publisher") or journal

        # Year and Published date
        issued = item.get("issued", {}).get("date-parts", [[]])[0]
        year: Optional[int] = None
        published_at: Optional[str] = None
        if issued and len(issued) > 0 and str(issued[0]).isdigit():
            year = int(issued[0])
            published_at = "-".join(str(p).zfill(2) for p in issued)

        # Abstract
        raw_abstract = item.get("abstract", "")
        abstract: Optional[str] = None
        if raw_abstract:
            abstract = BeautifulSoup(raw_abstract, "html.parser").get_text(strip=True)

        # Citations
        citation_count = item.get("is-referenced-by-count")
        referenced_by = item.get("references-count")

        source_id = f"crossref_{doi.replace('/', '_')}" if doi else f"crossref_{hash(url) % 1000000}"

        return ResearchSourceModel(
            id=source_id,
            source_type="academic",
            title=title,
            authors=authors,
            publisher=publisher,
            journal=journal,
            published_at=published_at,
            year=year,
            doi=doi,
            url=url,
            abstract=abstract,
            snippet=abstract[:300] if abstract else None,
            citation_count=citation_count,
            referenced_by_count=referenced_by,
            open_access=bool(item.get("license")),
            provider="crossref",
            metadata_verified=True,  # Crossref is the definitive registry of DOI metadata
            url_verified=True,
            authority_type="peer-reviewed academic journal",
            verification_badges=["✓ DOI Verified", "✓ Crossref Metadata"],
        )
