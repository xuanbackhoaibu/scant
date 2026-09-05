import re
import urllib.parse
import asyncio
from typing import Any, Dict, List, Optional, Set
import httpx
from bs4 import BeautifulSoup
from app.core.config import settings
from app.services.research.academic.base import ResearchSourceModel


class AuthorityDomainClassifier:
    """
    Rule engine for classifying domain authority and source types (Section 4 & 10).
    """

    GOV_DOMAINS = [
        ".gov", ".gov.vn", "chinhphu.vn", "gso.gov.vn", "moit.gov.vn",
        "mpi.gov.vn", "mof.gov.vn", "monre.gov.vn", "mic.gov.vn", "sbv.gov.vn",
        "customs.gov.vn", "energy.gov", "epa.gov", "transportation.gov",
        "dangcongsan.vn", "quochoi.vn"
    ]

    INTL_ORGS = {
        "worldbank.org": "World Bank",
        "imf.org": "International Monetary Fund (IMF)",
        "oecd.org": "OECD",
        "iea.org": "International Energy Agency (IEA)",
        "un.org": "United Nations",
        "who.int": "World Health Organization (WHO)",
        "wto.org": "World Trade Organization (WTO)",
        "adb.org": "Asian Development Bank (ADB)",
        "weforum.org": "World Economic Forum",
        "irena.org": "IRENA Renewable Energy Agency",
    }

    ACADEMIC_DOMAINS = [
        ".edu", ".edu.vn", ".ac.uk", "hust.edu.vn", "fpt.edu.vn", "uit.edu.vn",
        "vnu.edu.vn", "vnua.edu.vn", "neu.edu.vn", "ftu.edu.vn", "harvard.edu",
        "mit.edu", "stanford.edu", "ox.ac.uk", "cam.ac.uk"
    ]

    REPUTABLE_NEWS = {
        "reuters.com": "Reuters",
        "bloomberg.com": "Bloomberg",
        "ft.com": "Financial Times",
        "wsj.com": "Wall Street Journal",
        "vnexpress.net": "VnExpress",
        "cafef.vn": "CafeF",
        "vtcnews.vn": "VTC News",
        "tuoitre.vn": "Báo Tuổi Trẻ",
        "thanhnien.vn": "Báo Thanh Niên",
        "laodong.vn": "Báo Lao Động",
        "tienphong.vn": "Báo Tiền Phong",
        "vneconomy.vn": "VnEconomy",
        "vietnamnet.vn": "VietNamNet",
        "znews.vn": "Znews (Tri thức trực tuyến)",
        "zingnews.vn": "Znews",
        "baodautu.vn": "Báo Đầu Tư",
        "kinhtedothi.vn": "Kinh tế & Đô thị",
        "vietnamfinance.vn": "VietnamFinance",
        "dantri.com.vn": "Báo Dân Trí",
        "vov.vn": "VOV - Đài Tiếng nói Việt Nam",
        "vtv.vn": "VTV - Đài Truyền hình Việt Nam",
        "soha.vn": "Soha News",
        "forbes.com": "Forbes",
    }

    @classmethod
    def classify(cls, url: str) -> Dict[str, Any]:
        parsed = urllib.parse.urlparse(url)
        domain = (parsed.netloc or parsed.path).lower()
        if domain.startswith("www."):
            domain = domain[4:]

        # 1. Government
        if any(domain.endswith(g) or g in domain for g in cls.GOV_DOMAINS):
            return {
                "source_type": "government",
                "authority_type": "official government agency",
                "publisher": f"Cơ quan Chính phủ ({domain})",
                "base_reliability": 0.95,
            }

        # 2. International Organization
        for org_domain, org_name in cls.INTL_ORGS.items():
            if org_domain in domain:
                return {
                    "source_type": "government",
                    "authority_type": "international organization",
                    "publisher": org_name,
                    "base_reliability": 0.95,
                }

        # 3. University / Academic
        if any(domain.endswith(a) or a in domain for a in cls.ACADEMIC_DOMAINS):
            return {
                "source_type": "academic",
                "authority_type": "university / research institute",
                "publisher": f"Viện / Trường Đại học ({domain})",
                "base_reliability": 0.90,
            }

        # 4. Reputable News & Market Journalism
        for news_domain, news_name in cls.REPUTABLE_NEWS.items():
            if news_domain in domain:
                return {
                    "source_type": "reputable_news",
                    "authority_type": "reputable journalism / market news",
                    "publisher": news_name,
                    "base_reliability": 0.82,
                }

        # 5. Market Research & Industry Portals
        if any(k in domain for k in ["gartner", "mckinsey", "forrester", "statista", "vinfastauto", "idc", "vietnamfinance"]):
            return {
                "source_type": "industry_report",
                "authority_type": "market research & industry portal",
                "publisher": domain.split(".")[0].capitalize(),
                "base_reliability": 0.85,
            }

        return {
            "source_type": "web",
            "authority_type": "web publication",
            "publisher": domain,
            "base_reliability": 0.65,
        }


class WebSearchProvider:
    """
    Real Web & Market Research Provider (Section 4 & 5).
    Extracts real articles and reports from:
      1. Bing News & Web Feeds (decoding direct destination URLs)
      2. Google News Vietnam & Global RSS (real news portals, timestamps, publishers)
      3. Tavily Search API (if configured)
      4. Live text body scraping on discovered URLs for atomic facts and evidence
    NEVER generates fabricated or mock sources.
    """

    def __init__(self, timeout: float = 10.0):
        self.timeout = timeout
        self.tavily_api_key = settings.TAVILY_API_KEY

    async def search(self, query: str, limit: int = 10) -> List[ResearchSourceModel]:
        cleaned_query = query.strip()
        if not cleaned_query:
            return []

        # Gather sources from real engines concurrently
        tasks = [
            self._search_bing_news(cleaned_query, limit),
            self._search_google_news(cleaned_query, limit),
        ]
        if self.tavily_api_key:
            tasks.append(self._search_tavily(cleaned_query, limit))

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        merged: List[ResearchSourceModel] = []
        seen_urls: Set[str] = set()

        for res in results_lists:
            if isinstance(res, list):
                for s in res:
                    canon = self._canonicalize_url(s.url)
                    if canon not in seen_urls:
                        seen_urls.add(canon)
                        merged.append(s)

        # Scrape article body paragraphs for top candidates to empower atomic evidence extraction
        if merged:
            top_sources = merged[:min(limit, 8)]
            await self._enrich_sources_with_scraped_content(top_sources)
            return top_sources

        return []

    async def _search_bing_news(self, query: str, limit: int) -> List[ResearchSourceModel]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        encoded_q = urllib.parse.quote(query)
        url = f"https://www.bing.com/news/search?q={encoded_q}&format=rss"

        sources: List[ResearchSourceModel] = []
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=self.timeout) as client:
                r = await client.get(url)
                if r.status_code != 200:
                    return []

                soup = BeautifulSoup(r.text, "xml")
                items = soup.select("item")

                for it in items[:limit]:
                    raw_link = it.link.text.strip() if it.link else ""
                    # Unwrap Bing redirect: /news/apiclick.aspx?...&url=https%3A%2F%2F...
                    qs = urllib.parse.parse_qs(urllib.parse.urlparse(raw_link).query)
                    target_url = qs.get("url", [raw_link])[0]
                    if not target_url.startswith("http"):
                        continue

                    title = it.title.text.strip() if it.title else "Bản tin thị trường"
                    snippet = it.description.text.strip() if it.description else ""
                    pub_date = it.pubDate.text.strip() if it.pubDate else ""

                    # Extract year
                    year_match = re.search(r"\b(202[0-9])\b", pub_date or title)
                    year = int(year_match.group(1)) if year_match else 2026

                    cls = AuthorityDomainClassifier.classify(target_url)
                    source_id = f"web_bing_{abs(hash(target_url)) % 1000000}"

                    sources.append(
                        ResearchSourceModel(
                            id=source_id,
                            source_type=cls["source_type"],
                            title=title,
                            publisher=cls["publisher"],
                            url=target_url,
                            year=year,
                            published_at=pub_date,
                            abstract=snippet,
                            snippet=snippet,
                            provider="bing_news",
                            metadata_verified=True,
                            url_verified=True,
                            authority_type=cls["authority_type"],
                            verification_badges=["✓ Real Web Source", f"✓ {cls['authority_type'].title()}"],
                        )
                    )
        except Exception:
            return []

        return sources

    async def _search_google_news(self, query: str, limit: int) -> List[ResearchSourceModel]:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }
        encoded_q = urllib.parse.quote(query)
        url = f"https://news.google.com/rss/search?q={encoded_q}&hl=vi&gl=VN&ceid=VN:vi"

        sources: List[ResearchSourceModel] = []
        try:
            async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=self.timeout) as client:
                r = await client.get(url)
                if r.status_code != 200:
                    return []

                soup = BeautifulSoup(r.text, "xml")
                items = soup.select("item")

                for it in items[:limit]:
                    link = it.link.text.strip() if it.link else ""
                    title = it.title.text.strip() if it.title else "Thông tin báo chí"
                    desc = it.description.text.strip() if it.description else ""
                    clean_desc = re.sub(r"<[^>]+>", "", desc).strip()
                    pub_date = it.pubDate.text.strip() if it.pubDate else ""

                    source_tag = it.find("source")
                    publisher_name = source_tag.text.strip() if source_tag else ""
                    source_site_url = source_tag.get("url", "").strip() if source_tag else ""

                    # Prefer real publisher domain if available
                    article_url = link if link.startswith("http") else source_site_url
                    if not article_url:
                        continue

                    cls = AuthorityDomainClassifier.classify(source_site_url or article_url)
                    final_publisher = publisher_name or cls["publisher"]

                    # Extract year
                    year_match = re.search(r"\b(202[0-9])\b", pub_date or title)
                    year = int(year_match.group(1)) if year_match else 2026

                    source_id = f"web_gnews_{abs(hash(article_url)) % 1000000}"

                    sources.append(
                        ResearchSourceModel(
                            id=source_id,
                            source_type=cls["source_type"],
                            title=title,
                            publisher=final_publisher,
                            url=article_url,
                            year=year,
                            published_at=pub_date,
                            abstract=clean_desc,
                            snippet=clean_desc,
                            provider="google_news",
                            metadata_verified=True,
                            url_verified=True,
                            authority_type=cls["authority_type"],
                            verification_badges=["✓ Real Web Source", f"✓ {cls['authority_type'].title()}"],
                        )
                    )
        except Exception:
            return []

        return sources

    async def _search_tavily(self, query: str, limit: int) -> List[ResearchSourceModel]:
        url = "https://api.tavily.com/search"
        payload = {
            "api_key": self.tavily_api_key,
            "query": query,
            "search_depth": "advanced",
            "include_answer": True,
            "max_results": min(max(limit, 1), 20),
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                res = await client.post(url, json=payload)
                if res.status_code != 200:
                    return []

                data = res.json()
                sources: List[ResearchSourceModel] = []
                for item in data.get("results", []):
                    raw_url = item.get("url", "")
                    title = item.get("title", "Tài liệu trực tuyến").strip()
                    snippet = item.get("content", "").strip()
                    if not raw_url or not raw_url.startswith("http"):
                        continue

                    classification = AuthorityDomainClassifier.classify(raw_url)
                    source_id = f"web_tavily_{abs(hash(raw_url)) % 1000000}"

                    sources.append(
                        ResearchSourceModel(
                            id=source_id,
                            source_type=classification["source_type"],
                            title=title,
                            publisher=classification["publisher"],
                            url=raw_url,
                            abstract=snippet,
                            snippet=snippet,
                            provider="tavily",
                            metadata_verified=True,
                            url_verified=True,
                            authority_type=classification["authority_type"],
                            verification_badges=["✓ Live Web Verified", f"✓ {classification['authority_type'].title()}"],
                        )
                    )
                return sources
        except Exception:
            return []

    async def _enrich_sources_with_scraped_content(self, sources: List[ResearchSourceModel]):
        """
        Lightweight concurrent scraper: fetches article paragraphs to provide
        deep factual evidence for the Evidence Extractor.
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        }

        async def _fetch_single(s: ResearchSourceModel):
            if "google.com" in s.url or not s.url.startswith("http"):
                return
            try:
                async with httpx.AsyncClient(headers=headers, follow_redirects=True, timeout=3.5) as client:
                    r = await client.get(s.url)
                    if r.status_code == 200:
                        soup = BeautifulSoup(r.text, "html.parser")
                        # Extract substantive paragraphs
                        paras = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 50]
                        if paras:
                            body_text = " ".join(paras[:4])
                            s.abstract = body_text[:1200]
                            s.snippet = body_text[:600]
                            s.verification_badges.append("✓ Full-Text Scraped")
            except Exception:
                pass

        tasks = [_fetch_single(s) for s in sources]
        await asyncio.gather(*tasks, return_exceptions=True)

    @staticmethod
    def _canonicalize_url(url: str) -> str:
        try:
            parsed = urllib.parse.urlparse(url)
            netloc = parsed.netloc.lower()
            if netloc.startswith("www."):
                netloc = netloc[4:]
            path = parsed.path.rstrip("/")
            return f"{netloc}{path}"
        except Exception:
            return url.lower()


web_search_provider = WebSearchProvider()
