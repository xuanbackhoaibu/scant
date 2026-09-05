import hashlib
import logging
from typing import Any, Dict, List, Optional
import httpx
from app.services.research.academic.base import AcademicProvider, ResearchSourceModel

logger = logging.getLogger("academic.openalex")


class OpenAlexProvider(AcademicProvider):
    """
    Real OpenAlex Academic Provider.
    OpenAlex is a fully open catalog of hundreds of millions of scholarly papers,
    authors, venues, and research works.
    Free, zero paywalls, official DOIs, genuine citations and publication years.
    """

    name: str = "openalex"
    BASE_URL = "https://api.openalex.org/works"

    def __init__(self, timeout: float = 12.0):
        self.timeout = timeout

    @staticmethod
    def _reconstruct_abstract(inverted_index: Optional[Dict[str, List[int]]]) -> Optional[str]:
        if not inverted_index or not isinstance(inverted_index, dict):
            return None
        words: List[tuple[int, str]] = []
        for word, positions in inverted_index.items():
            for pos in positions:
                words.append((pos, word))
        words.sort(key=lambda x: x[0])
        return " ".join(w[1] for w in words[:180])

    async def search(self, query: str, limit: int = 10, **kwargs) -> List[ResearchSourceModel]:
        cleaned = query.strip()
        if not cleaned:
            return []

        params = {
            "search": cleaned,
            "per-page": min(limit, 25),
            "mailto": "researcher@studio.ai",
        }
        headers = {
            "User-Agent": "AIReportStudio-VerificationEngine/2.0 (mailto:researcher@studio.ai)"
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                resp = await client.get(self.BASE_URL, params=params, headers=headers)
                if resp.status_code != 200:
                    logger.warning(f"OpenAlex returned {resp.status_code} for query '{query}'")
                    return []
                data = resp.json()

            results: List[ResearchSourceModel] = []
            works = data.get("results", [])

            for item in works:
                title = (item.get("display_name") or item.get("title") or "").strip()
                if not title:
                    continue

                doi_url = item.get("doi") or ""
                doi_clean = doi_url.replace("https://doi.org/", "").strip() if doi_url else None

                authors = []
                for auth_obj in item.get("authorships", []):
                    a_name = auth_obj.get("author", {}).get("display_name")
                    if a_name:
                        authors.append(a_name.strip())

                primary_loc = item.get("primary_location") or {}
                source_meta = primary_loc.get("source") or {}
                journal = source_meta.get("display_name")
                publisher = source_meta.get("host_organization_name") or "Scholarly Publisher"

                oa = item.get("open_access") or {}
                open_access = bool(oa.get("is_oa"))
                pdf_url = oa.get("oa_url") or primary_loc.get("pdf_url")

                landing_url = primary_loc.get("landing_page_url") or doi_url or item.get("id")
                cited_by = item.get("cited_by_count", 0)
                year = item.get("publication_year")
                pub_date = item.get("publication_date") or (str(year) if year else None)

                abstract = self._reconstruct_abstract(item.get("abstract_inverted_index"))
                unique_id = f"openalex_{hashlib.md5((doi_url or title).encode()).hexdigest()[:12]}"

                # Compute baseline verification & quality score
                score = 80.0
                if doi_clean:
                    score += 15.0
                if authors:
                    score += 5.0
                if open_access:
                    score += 5.0

                badges = ["OpenAlex Verified"]
                if doi_clean:
                    badges.append("Official DOI")
                if open_access:
                    badges.append("Open Access")

                results.append(
                    ResearchSourceModel(
                        id=unique_id,
                        source_type="ACADEMIC_PAPER",
                        title=title,
                        authors=authors[:8],
                        publisher=publisher,
                        journal=journal,
                        published_at=pub_date,
                        year=year,
                        doi=doi_clean,
                        url=landing_url,
                        abstract=abstract,
                        snippet=abstract[:300] if abstract else f"Paper xuất bản năm {year or 'gần đây'}. Được trích dẫn {cited_by} lần.",
                        citation_count=cited_by,
                        referenced_by_count=cited_by,
                        open_access=open_access,
                        pdf_url=pdf_url,
                        provider="openalex",
                        metadata_verified=True,
                        url_verified=bool(landing_url),
                        quality_score=min(score, 100.0),
                        authority_type="peer_reviewed_academic",
                        verification_badges=badges,
                    )
                )

            return results
        except Exception as e:
            logger.warning(f"OpenAlex search error: {e}")
            return []
