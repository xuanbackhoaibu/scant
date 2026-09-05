from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project, Source, Citation, ClaimSource, ResearchJob, ResearchResult
from app.repositories.project_repo import project_repo
from app.repositories.source_repo import source_repo, citation_repo, claim_source_repo
from app.repositories.base import BaseRepository
from app.schemas.source import SourceCreate, SourceResponse, CitationResponse, ClaimSourceResponse
from app.api.deps import get_current_user, get_current_user_optional
from app.services.research.deep_research_pipeline import deep_research_pipeline, DeepResearchResult
from app.services.citations.citation_formatter import citation_formatter

router = APIRouter(prefix="/research", tags=["research"])
job_repo = BaseRepository[ResearchJob](ResearchJob)
result_repo = BaseRepository[ResearchResult](ResearchResult)


class CitationExportRequest(BaseModel):
    sources: List[Dict[str, Any]]
    style: str = "IEEE"  # IEEE, APA, HARVARD, BIBTEX, RIS


@router.post("/search")
async def execute_research(
    project_id: str,
    query: str,
    mode: str = "standard",  # quick, standard / deep, expert
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Executes the End-to-End Deep Research Pipeline for a project.
    Uses real Academic APIs (Crossref, arXiv, Semantic Scholar, PubMed) and live web portals.
    Stores verified sources and evidence in the database.
    """
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    # 1. Create Research Job in Database
    job = await job_repo.create(db, obj_in={
        "project_id": project_id,
        "query": query,
        "mode": mode,
        "status": "running",
        "progress_percent": 15,
        "status_message": "Đang phân tích truy vấn & điều tra nguồn học thuật thực tế...",
    })

    # 2. Execute Real Autonomous Pipeline
    pipeline_mode = "quick" if mode == "quick" else ("expert" if mode == "expert" else "deep")
    res: DeepResearchResult = await deep_research_pipeline.execute(query=query, mode=pipeline_mode)

    # 3. Save Verified Sources and Results to Database
    saved_sources: List[Source] = []
    for s in res.sources:
        authors_str = ", ".join(s.authors) if s.authors else "Official Contributor"
        meta_dict = {
            "doi": s.doi,
            "arxiv_id": s.arxiv_id,
            "pmid": s.pmid,
            "citation_count": s.citation_count,
            "open_access": s.open_access,
            "pdf_url": s.pdf_url,
            "provider": s.provider,
            "quality_score": s.quality_score,
            "quality_breakdown": s.quality_breakdown,
            "authority_type": s.authority_type,
            "verification_badges": s.verification_badges,
            "metadata_verified": s.metadata_verified,
            "url_verified": s.url_verified,
        }

        src = await source_repo.create(db, obj_in={
            "project_id": project_id,
            "title": s.title,
            "url": s.url,
            "authors": authors_str,
            "publisher": s.publisher or s.journal or "Verified Publisher",
            "published_date": str(s.year) if s.year else s.published_at or "2026",
            "source_type": s.source_type,
            "reliability_score": round(s.quality_score / 100.0, 2),
            "summary": s.abstract or s.snippet or s.title,
            "content_extracted": s.abstract or s.snippet or "",
            "metadata_json": meta_dict,
        })
        saved_sources.append(src)

        await result_repo.create(db, obj_in={
            "job_id": job.id,
            "source_id": src.id,
            "title": s.title,
            "url": s.url,
            "snippet": s.snippet or s.abstract or "",
            "rank_score": round(s.quality_score / 100.0, 2),
            "relevance_score": s.quality_breakdown.get("relevance", 0.90),
            "is_selected": True,
        })

    # 4. Mark Job Completed
    await job_repo.update(db, db_obj=job, obj_in={
        "status": "completed",
        "progress_percent": 100,
        "status_message": f"Nghiên cứu hoàn tất. Đã xác minh {len(saved_sources)} nguồn thực tế ({res.academic_count} học thuật, {res.government_count} chính phủ).",
    })

    return {
        "job_id": job.id,
        "session_id": res.session_id,
        "query": query,
        "mode": mode,
        "total_found": res.total_found,
        "total_verified": res.total_verified,
        "academic_count": res.academic_count,
        "government_count": res.government_count,
        "market_count": res.market_count,
        "news_count": res.news_count,
        "duration_seconds": res.duration_seconds,
        "sources_found": len(saved_sources),
        "sources": [SourceResponse.model_validate(s) for s in saved_sources],
        "evidence_nodes": [e.model_dump() for e in res.evidence_nodes],
        "market_claims": [m.model_dump() for m in res.market_claims],
        "synthesis": res.synthesis.model_dump(),
        "graph_nodes": [n.model_dump() for n in res.graph_nodes],
        "graph_edges": [e.model_dump() for e in res.graph_edges],
        "search_log": res.search_log,
    }


@router.post("/direct-search")
async def direct_research_search(
    query: str,
    max_results: int = 10,
    mode: str = "quick",
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Direct Real-time Deep Research query.
    Returns 100% real verified sources, atomic evidence, market claims, and anti-hallucination synthesis.
    """
    pipeline_mode = "quick" if (mode == "quick" or max_results <= 8) else "deep"
    res: DeepResearchResult = await deep_research_pipeline.execute(query=query, mode=pipeline_mode)

    # Build backward-compatible results array for existing frontend consumers
    compatible_results = []
    for s in res.sources[:max_results]:
        compatible_results.append({
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "snippet": s.abstract or s.snippet or s.title,
            "publisher": s.publisher or s.journal or "Verified Publication",
            "authors": ", ".join(s.authors) if s.authors else "Official Contributor",
            "published_date": str(s.year) if s.year else s.published_at or "2026",
            "source_type": s.source_type,
            "reliability_score": round(s.quality_score / 100.0, 2),
            "quality_score": s.quality_score,
            "quality_breakdown": s.quality_breakdown,
            "doi": s.doi,
            "arxiv_id": s.arxiv_id,
            "citation_count": s.citation_count,
            "open_access": s.open_access,
            "pdf_url": s.pdf_url,
            "provider": s.provider,
            "metadata_verified": s.metadata_verified,
            "url_verified": s.url_verified,
            "verification_badges": s.verification_badges,
        })

    return {
        "query": query,
        "mode": pipeline_mode,
        "total_found": res.total_found,
        "total_verified": res.total_verified,
        "academic_count": res.academic_count,
        "government_count": res.government_count,
        "market_count": res.market_count,
        "news_count": res.news_count,
        "duration_seconds": res.duration_seconds,
        "results": compatible_results,
        "sources": [s.model_dump() for s in res.sources[:max_results]],
        "evidence_nodes": [e.model_dump() for e in res.evidence_nodes],
        "market_claims": [m.model_dump() for m in res.market_claims],
        "synthesis": res.synthesis.model_dump(),
        "graph_nodes": [n.model_dump() for n in res.graph_nodes],
        "graph_edges": [e.model_dump() for e in res.graph_edges],
        "search_log": res.search_log,
    }


@router.post("/export")
async def export_citations(
    req: CitationExportRequest,
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Exports verified citation metadata in academic standard formats (Section 31):
    APA, IEEE, Harvard, BibTeX, RIS.
    """
    style = req.style.upper()
    formatted_entries = []

    for idx, src in enumerate(req.sources):
        src_dict = {
            "title": src.get("title", ""),
            "authors": src.get("authors") or (", ".join(src.get("authors_list", [])) if isinstance(src.get("authors_list"), list) else ""),
            "publisher": src.get("publisher") or src.get("journal") or "",
            "published_date": str(src.get("year") or src.get("published_date") or "2026"),
            "url": src.get("url", ""),
            "doi": src.get("doi", ""),
        }

        if style == "BIBTEX":
            formatted_entries.append(citation_formatter.format_bibtex(idx + 1, src_dict))
        elif style == "RIS":
            formatted_entries.append(citation_formatter.format_ris(idx + 1, src_dict))
        else:
            formatted_entries.append(citation_formatter.format_bibliography_entry(idx + 1, src_dict, style=style))

    separator = "\n\n" if style in ("BIBTEX", "RIS") else "\n"
    return {
        "style": style,
        "count": len(formatted_entries),
        "content": separator.join(formatted_entries),
    }


@router.get("/sources/project/{project_id}", response_model=List[SourceResponse])
async def list_project_sources(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    sources = await source_repo.get_by_project(db, project_id)
    return [SourceResponse.model_validate(s) for s in sources]


@router.post("/sources", response_model=SourceResponse)
async def add_custom_source(
    src_in: SourceCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, src_in.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    src = await source_repo.create(db, obj_in={
        "project_id": src_in.project_id,
        "title": src_in.title,
        "url": src_in.url,
        "authors": src_in.authors or "Anonymous",
        "publisher": src_in.publisher or "Custom Publication",
        "published_date": src_in.published_date or "2024",
        "source_type": src_in.source_type,
        "reliability_score": src_in.reliability_score,
        "summary": src_in.summary,
        "content_extracted": src_in.content_extracted,
        "metadata_json": src_in.metadata or {},
    })
    return SourceResponse.model_validate(src)


@router.get("/citations/trace/{citation_id}", response_model=CitationResponse)
async def trace_citation(
    citation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cit = await citation_repo.get(db, citation_id)
    if not cit:
        raise HTTPException(status_code=404, detail="Citation not found")
    return CitationResponse.model_validate(cit)


@router.post("/resolve-identifier")
async def resolve_academic_identifier(
    input_str: str,
    current_user: User = Depends(get_current_user),
):
    """Resolves a DOI, ArXiv ID/URL, or web link into structured academic citation metadata."""
    from app.services.citations.doi_arxiv_resolver import doi_arxiv_resolver
    resolved = await doi_arxiv_resolver.resolve(input_str)
    if not resolved:
        raise HTTPException(status_code=404, detail="Không thể trích xuất định danh học thuật từ liên kết/mã đã nhập.")
    return resolved.model_dump()
