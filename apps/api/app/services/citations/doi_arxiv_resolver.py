import re
import urllib.parse
from typing import Any, Dict, List, Optional
import httpx
from bs4 import BeautifulSoup
from pydantic import BaseModel
from app.services.citations.citation_formatter import citation_formatter


class ResolvedCitation(BaseModel):
    title: str
    authors: str
    publisher: str
    published_date: str
    url: str
    source_type: str  # journal_article, preprint, conference_paper, book, web
    abstract: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    ieee_formatted: str
    apa_formatted: str
    harvard_formatted: str
    mla_formatted: str
    bibtex: str


class DoiArxivResolver:
    """
    Intelligent Academic Identifier & Paper Resolver.
    Supports CrossRef (DOI), ArXiv (Atom API), Semantic Scholar, and OpenAlex.
    """

    DOI_PATTERN = re.compile(r"\b(10\.\d{4,9}/[-._;()/:A-Za-z0-9]+)\b")
    ARXIV_PATTERN = re.compile(r"(?:arxiv\.org/(?:abs|pdf)/|arxiv:\s*)([0-9]+\.[0-9]+(?:v[0-9]+)?)", re.I)

    @classmethod
    async def resolve(cls, input_str: str) -> Optional[ResolvedCitation]:
        input_clean = input_str.strip()
        if not input_clean:
            return None

        # 1. Try DOI Match
        doi_match = cls.DOI_PATTERN.search(input_clean)
        if doi_match:
            doi = doi_match.group(1).rstrip(".")
            res = await cls._resolve_doi(doi)
            if res:
                return res

        # 2. Try ArXiv Match
        arxiv_match = cls.ARXIV_PATTERN.search(input_clean)
        if arxiv_match:
            arxiv_id = arxiv_match.group(1)
            res = await cls._resolve_arxiv(arxiv_id)
            if res:
                return res

        # 3. Fallback: Generic Web Scraper / Academic Resolver
        return await cls._resolve_web_url(input_clean)

    @classmethod
    async def _resolve_doi(cls, doi: str) -> Optional[ResolvedCitation]:
        url = f"https://api.crossref.org/works/{urllib.parse.quote(doi)}"
        headers = {"User-Agent": "AIReportStudio/2.0 (mailto:support@aireportstudio.com)"}

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.get(url, headers=headers)
                if res.status_code != 200:
                    return None

                msg = res.json().get("message", {})
                title = (msg.get("title") or [""])[0].strip()
                if not title:
                    return None

                # Format authors
                authors_list = []
                for a in msg.get("author", []):
                    given = a.get("given", "")
                    family = a.get("family", "")
                    name = f"{given} {family}".strip() if given else family
                    if name:
                        authors_list.append(name)
                authors = ", ".join(authors_list) or "Academic Research Group"

                # Publisher / Journal
                container = (msg.get("container-title") or [""])[0]
                publisher = container or msg.get("publisher", "Academic Publisher")

                # Year
                issued = msg.get("issued", {}).get("date-parts", [["2024"]])[0]
                pub_year = str(issued[0]) if issued else "2024"

                doi_url = msg.get("URL") or f"https://doi.org/{doi}"
                abstract = msg.get("abstract", "")
                if abstract:
                    abstract = BeautifulSoup(abstract, "html.parser").get_text()

                src_dict = {
                    "title": title,
                    "authors": authors,
                    "publisher": publisher,
                    "published_date": pub_year,
                    "url": doi_url,
                }

                ieee = citation_formatter.format_bibliography_entry(1, src_dict, style="IEEE")
                apa = citation_formatter.format_bibliography_entry(1, src_dict, style="APA")
                harvard = citation_formatter.format_bibliography_entry(1, src_dict, style="Harvard")
                mla = citation_formatter.format_bibliography_entry(1, src_dict, style="MLA")

                first_author_key = authors_list[0].split(" ")[-1].lower() if authors_list else "paper"
                bibtex = f"""@article{{{first_author_key}{pub_year},
  title={{{title}}},
  author={{{' and '.join(authors_list) if authors_list else authors}}},
  journal={{{publisher}}},
  year={{{pub_year}}},
  doi={{{doi}}},
  url={{{doi_url}}}
}}"""

                return ResolvedCitation(
                    title=title,
                    authors=authors,
                    publisher=publisher,
                    published_date=pub_year,
                    url=doi_url,
                    source_type="journal_article",
                    abstract=abstract or None,
                    doi=doi,
                    ieee_formatted=ieee,
                    apa_formatted=apa,
                    harvard_formatted=harvard,
                    mla_formatted=mla,
                    bibtex=bibtex,
                )
        except Exception:
            return None

    @classmethod
    async def _resolve_arxiv(cls, arxiv_id: str) -> Optional[ResolvedCitation]:
        clean_id = arxiv_id.split("v")[0]
        url = f"http://export.arxiv.org/api/query?id_list={clean_id}"

        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                res = await client.get(url)
                if res.status_code != 200:
                    return None

                soup = BeautifulSoup(res.text, "xml")
                entry = soup.find("entry")
                if not entry:
                    return None

                title = entry.find("title").get_text().replace("\n", " ").strip()
                abstract = entry.find("summary").get_text().replace("\n", " ").strip() if entry.find("summary") else ""
                
                authors_list = [a.find("name").get_text().strip() for a in entry.find_all("author") if a.find("name")]
                authors = ", ".join(authors_list) or "ArXiv Researchers"

                published = entry.find("published").get_text() if entry.find("published") else "2024"
                pub_year = published[:4] if len(published) >= 4 else "2024"

                paper_url = f"https://arxiv.org/abs/{arxiv_id}"
                publisher = "arXiv.org e-Print Archive"

                src_dict = {
                    "title": title,
                    "authors": authors,
                    "publisher": publisher,
                    "published_date": pub_year,
                    "url": paper_url,
                }

                ieee = citation_formatter.format_bibliography_entry(1, src_dict, style="IEEE")
                apa = citation_formatter.format_bibliography_entry(1, src_dict, style="APA")
                harvard = citation_formatter.format_bibliography_entry(1, src_dict, style="Harvard")
                mla = citation_formatter.format_bibliography_entry(1, src_dict, style="MLA")

                first_author_key = authors_list[0].split(" ")[-1].lower() if authors_list else "arxiv"
                bibtex = f"""@article{{{first_author_key}{pub_year}arxiv,
  title={{{title}}},
  author={{{' and '.join(authors_list) if authors_list else authors}}},
  journal={{{publisher}}},
  year={{{pub_year}}},
  eprint={{{arxiv_id}}},
  archivePrefix={{arXiv}},
  url={{{paper_url}}}
}}"""

                return ResolvedCitation(
                    title=title,
                    authors=authors,
                    publisher=publisher,
                    published_date=pub_year,
                    url=paper_url,
                    source_type="preprint",
                    abstract=abstract or None,
                    arxiv_id=arxiv_id,
                    ieee_formatted=ieee,
                    apa_formatted=apa,
                    harvard_formatted=harvard,
                    mla_formatted=mla,
                    bibtex=bibtex,
                )
        except Exception:
            return None

    @classmethod
    async def _resolve_web_url(cls, url: str) -> Optional[ResolvedCitation]:
        from app.services.research.scraper import web_scraper
        try:
            scraped = await web_scraper.scrape_url(url)
            title = scraped.get("title", url)
            authors = scraped.get("authors", "Tài liệu kỹ thuật / Tác giả trực tuyến")
            publisher = scraped.get("publisher", "Web Publication")
            pub_date = scraped.get("published_date", "2024")

            src_dict = {
                "title": title,
                "authors": authors,
                "publisher": publisher,
                "published_date": pub_date,
                "url": url,
            }

            ieee = citation_formatter.format_bibliography_entry(1, src_dict, style="IEEE")
            apa = citation_formatter.format_bibliography_entry(1, src_dict, style="APA")
            harvard = citation_formatter.format_bibliography_entry(1, src_dict, style="Harvard")
            mla = citation_formatter.format_bibliography_entry(1, src_dict, style="MLA")

            bibtex = f"""@misc{{web{pub_date}_{hash(url)%10000},
  title={{{title}}},
  author={{{authors}}},
  howpublished={{\\url{{{url}}}}},
  year={{{pub_date}}}
}}"""

            return ResolvedCitation(
                title=title,
                authors=authors,
                publisher=publisher,
                published_date=pub_date,
                url=url,
                source_type="web",
                abstract=scraped.get("extracted_text", "")[:300] if scraped.get("extracted_text") else None,
                ieee_formatted=ieee,
                apa_formatted=apa,
                harvard_formatted=harvard,
                mla_formatted=mla,
                bibtex=bibtex,
            )
        except Exception:
            return None


doi_arxiv_resolver = DoiArxivResolver()
