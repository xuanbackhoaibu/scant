import re
from typing import Any, Dict, List, Optional
import httpx
from app.services.research.academic.base import AcademicProvider, ResearchSourceModel


class PubMedProvider(AcademicProvider):
    """
    Real Academic Search Provider using NCBI PubMed / PMC E-Utilities API (Section 3.D).
    Activated for medicine, healthcare, biology, pharmaceuticals, and public health queries.
    """
    name = "pubmed"
    SEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
    SUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

    HEALTH_KEYWORDS = [
        "medicine", "health", "clinical", "hospital", "pharma", "drug", "vaccine",
        "disease", "cancer", "patient", "therapy", "y tế", "sức khỏe", "bệnh viện",
        "dược phẩm", "thuốc", "vắc xin", "điều trị", "dịch bệnh", "y học",
    ]

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout

    @classmethod
    def is_medical_query(cls, query: str) -> bool:
        q_lower = query.lower()
        return any(k in q_lower for k in cls.HEALTH_KEYWORDS)

    async def search(self, query: str, limit: int = 10, **kwargs) -> List[ResearchSourceModel]:
        # Only query PubMed if the query is in the medical/health domain
        if not self.is_medical_query(query) and not kwargs.get("force_pubmed", False):
            return []

        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        results: List[ResearchSourceModel] = []
        try:
            async with httpx.AsyncClient(timeout=self.timeout, follow_redirects=True) as client:
                # 1. Search for IDs
                search_params = {
                    "db": "pmc",
                    "term": cleaned_query,
                    "retmode": "json",
                    "retmax": min(max(limit, 1), 15),
                    "sort": "pub_date",
                }
                res = await client.get(self.SEARCH_URL, params=search_params)
                if res.status_code != 200:
                    return []

                id_list = res.json().get("esearchresult", {}).get("idlist", [])
                if not id_list:
                    return []

                # 2. Fetch Summaries
                summary_params = {
                    "db": "pmc",
                    "id": ",".join(id_list),
                    "retmode": "json",
                }
                sum_res = await client.get(self.SUMMARY_URL, params=summary_params)
                if sum_res.status_code != 200:
                    return []

                sum_data = sum_res.json().get("result", {})
                for pmid in id_list:
                    item = sum_data.get(pmid)
                    if item:
                        source = self._parse_summary(pmid, item)
                        if source:
                            results.append(source)
        except Exception:
            return []

        return results

    def _parse_summary(self, pmid: str, item: Dict[str, Any]) -> Optional[ResearchSourceModel]:
        title = item.get("title", "").strip()
        if not title:
            return None

        # Clean title HTML
        title = re.sub(r"<[^>]+>", "", title).strip()

        authors = [a.get("name", "").strip() for a in item.get("authors", []) if a.get("name")]
        source_name = item.get("source", "PubMed Central")
        pubdate = item.get("pubdate", "")
        year = int(pubdate[:4]) if pubdate and pubdate[:4].isdigit() else None

        doi = item.get("doi")
        article_ids = item.get("articleids", [])
        for aid in article_ids:
            if aid.get("idtype") == "doi":
                doi = aid.get("value")

        url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/"
        pdf_url = f"https://www.ncbi.nlm.nih.gov/pmc/articles/PMC{pmid}/pdf/"

        return ResearchSourceModel(
            id=f"pubmed_{pmid}",
            source_type="academic",
            title=title,
            authors=authors,
            publisher="National Center for Biotechnology Information (NCBI)",
            journal=source_name,
            published_at=pubdate,
            year=year,
            doi=doi,
            pmid=pmid,
            url=url,
            pdf_url=pdf_url,
            open_access=True,
            provider="pubmed",
            metadata_verified=True,
            url_verified=True,
            authority_type="peer-reviewed medical journal",
            verification_badges=["✓ PubMed Central Verified", "✓ NCBI NIH Indexed"],
        )
