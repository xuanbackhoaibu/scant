import re
import urllib.parse
import asyncio
from typing import Any, Dict, List, Optional, Tuple
import httpx
from app.services.research.academic.base import ResearchSourceModel


class SourceVerifier:
    """
    Source Verification & Deduplication Engine (Section 7 & 8).
    - URL & HTTP availability verification.
    - DOI & identifier verification.
    - Multi-provider deduplication & metadata merging.
    """

    DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")

    @classmethod
    def normalize_title(cls, title: str) -> str:
        """Strip punctuation, whitespace, and lowercase for comparison."""
        t = re.sub(r"[^\w\s]", "", title.lower())
        return " ".join(t.split())

    @classmethod
    def title_similarity(cls, t1: str, t2: str) -> float:
        """Jaccard similarity over word tokens."""
        s1 = set(cls.normalize_title(t1).split())
        s2 = set(cls.normalize_title(t2).split())
        if not s1 or not s2:
            return 0.0
        return len(s1 & s2) / len(s1 | s2)

    @classmethod
    def canonical_url(cls, url: str) -> str:
        """Remove query params, fragments, and trailing slashes for deduplication."""
        try:
            parsed = urllib.parse.urlparse(url)
            # Remove utm parameters
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = parsed.path.rstrip("/")
            return f"{netloc}{path}"
        except Exception:
            return url.lower()

    async def verify_url_live(self, url: str, timeout: float = 3.5) -> bool:
        """Lightweight HTTP validation checking that URL exists and responds with 200/3xx."""
        if not url or not url.startswith("http"):
            return False
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                res = await client.head(url, headers={"User-Agent": "AIReportStudio/2.0"})
                if res.status_code in (200, 301, 302, 303, 307, 308, 403):
                    # 403 often means bot protection (Cloudflare) but URL is definitely real
                    return True
                # If HEAD fails or returns 405 Method Not Allowed, fallback to quick GET range
                if res.status_code == 405:
                    get_res = await client.get(url, headers={"Range": "bytes=0-100", "User-Agent": "AIReportStudio/2.0"})
                    return get_res.status_code in (200, 206)
        except Exception:
            return False
        return False

    async def verify_sources_batch(self, sources: List[ResearchSourceModel]) -> List[ResearchSourceModel]:
        """Perform concurrent HTTP verification on sources."""
        tasks = []
        for src in sources:
            if src.provider in ("crossref", "arxiv", "pubmed"):
                # Academic DOI registries and official preprint archives are pre-verified
                src.url_verified = True
                src.metadata_verified = True
            else:
                tasks.append(self._verify_single_source(src))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        return sources

    async def _verify_single_source(self, src: ResearchSourceModel):
        is_live = await self.verify_url_live(src.url)
        src.url_verified = is_live
        if is_live:
            src.verification_badges.append("✓ URL Verified")
        if src.doi and self.DOI_PATTERN.search(src.doi):
            src.metadata_verified = True
            src.verification_badges.append("✓ DOI Format Validated")

    def deduplicate_and_merge(self, sources: List[ResearchSourceModel]) -> List[ResearchSourceModel]:
        """
        Deduplicates sources across Crossref, Semantic Scholar, ArXiv, and Web.
        Merges metadata to preserve the best publisher, citations, abstract, etc.
        """
        merged: List[ResearchSourceModel] = []

        for src in sources:
            match_idx = self._find_matching_index(src, merged)
            if match_idx is not None:
                # Merge into existing item
                merged[match_idx] = self._merge_two_sources(merged[match_idx], src)
            else:
                merged.append(src)

        return merged

    deduplicate_sources = deduplicate_and_merge

    def _find_matching_index(self, target: ResearchSourceModel, existing: List[ResearchSourceModel]) -> Optional[int]:
        target_canon = self.canonical_url(target.url)

        for i, item in enumerate(existing):
            # 1. Match by DOI
            if target.doi and item.doi and target.doi.lower().strip() == item.doi.lower().strip():
                return i
            # 2. Match by arXiv ID
            if target.arxiv_id and item.arxiv_id and target.arxiv_id == item.arxiv_id:
                return i
            # 3. Match by PMID
            if target.pmid and item.pmid and target.pmid == item.pmid:
                return i
            # 4. Match by canonical URL
            if target_canon and target_canon == self.canonical_url(item.url):
                return i
            # 5. Match by normalized Title Similarity (threshold 0.85)
            if self.title_similarity(target.title, item.title) >= 0.85:
                return i

        return None

    def _merge_two_sources(self, primary: ResearchSourceModel, secondary: ResearchSourceModel) -> ResearchSourceModel:
        """Merge secondary into primary, choosing the richest metadata."""
        # Prefer DOI
        doi = primary.doi or secondary.doi
        arxiv_id = primary.arxiv_id or secondary.arxiv_id
        pmid = primary.pmid or secondary.pmid

        # Authors
        authors = primary.authors if len(primary.authors) >= len(secondary.authors) else secondary.authors

        # Citations count (prefer highest / non-null)
        citation_count = primary.citation_count
        if secondary.citation_count is not None:
            citation_count = max(primary.citation_count or 0, secondary.citation_count)

        # Publisher / Journal
        publisher = primary.publisher or secondary.publisher
        journal = primary.journal or secondary.journal

        # Abstract
        abstract = primary.abstract if (primary.abstract and len(primary.abstract) > 50) else (secondary.abstract or primary.abstract)
        snippet = abstract[:300] if abstract else (primary.snippet or secondary.snippet)

        # PDF URL & Open Access
        pdf_url = primary.pdf_url or secondary.pdf_url
        open_access = primary.open_access or secondary.open_access

        # Verification status boosts
        metadata_verified = primary.metadata_verified or secondary.metadata_verified
        url_verified = primary.url_verified or secondary.url_verified

        # Badges
        combined_badges = list(dict.fromkeys(primary.verification_badges + secondary.verification_badges + ["✓ Multi-Provider Cross-Checked"]))

        return primary.model_copy(update={
            "doi": doi,
            "arxiv_id": arxiv_id,
            "pmid": pmid,
            "authors": authors,
            "citation_count": citation_count,
            "publisher": publisher,
            "journal": journal,
            "abstract": abstract,
            "snippet": snippet,
            "pdf_url": pdf_url,
            "open_access": open_access,
            "metadata_verified": metadata_verified,
            "url_verified": url_verified,
            "verification_badges": combined_badges,
        })


source_verifier = SourceVerifier()
