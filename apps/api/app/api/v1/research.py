from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project, Source, Citation, ClaimSource, ResearchJob, ResearchResult
from app.repositories.project_repo import project_repo
from app.repositories.source_repo import source_repo, citation_repo, claim_source_repo
from app.repositories.base import BaseRepository
from app.schemas.source import SourceCreate, SourceResponse, CitationResponse, ClaimSourceResponse
from app.api.deps import get_current_user
from app.services.research.search_engine import search_engine
from app.services.research.source_ranker import source_ranker
from app.services.research.scraper import web_scraper

router = APIRouter(prefix="/research", tags=["research"])
job_repo = BaseRepository[ResearchJob](ResearchJob)
result_repo = BaseRepository[ResearchResult](ResearchResult)


@router.post("/search")
async def execute_research(
    project_id: str,
    query: str,
    mode: str = "standard",  # quick (5), standard (10-20), deep (30+)
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    limit = 5 if mode == "quick" else 15 if mode == "standard" else 30

    # 1. Create Research Job
    job = await job_repo.create(db, obj_in={
        "project_id": project_id,
        "query": query,
        "mode": mode,
        "status": "running",
        "progress_percent": 20,
        "status_message": "Đang tìm kiếm nguồn tài liệu chính thức...",
    })

    # 2. Search Provider
    provider = search_engine.get_search_provider()
    raw_results = await provider.search(query, max_results=limit)

    # 3. Rank Sources
    ranked_results = source_ranker.rank_sources(raw_results)

    # 4. Save to Source and ResearchResult tables
    saved_sources: List[Source] = []
    for item in ranked_results:
        src = await source_repo.create(db, obj_in={
            "project_id": project_id,
            "title": item["title"],
            "url": item["url"],
            "authors": item.get("authors", "Official Contributor"),
            "publisher": item.get("publisher", "Web Publisher"),
            "published_date": item.get("published_date", "2024"),
            "source_type": item.get("source_type", "website"),
            "reliability_score": item["reliability_score"],
            "summary": item.get("snippet", ""),
            "content_extracted": item.get("snippet", ""),
            "metadata_json": {},
        })
        saved_sources.append(src)

        await result_repo.create(db, obj_in={
            "job_id": job.id,
            "source_id": src.id,
            "title": item["title"],
            "url": item["url"],
            "snippet": item.get("snippet", ""),
            "rank_score": item["reliability_score"],
            "relevance_score": 0.95,
            "is_selected": True,
        })

    # Update Job status
    await job_repo.update(db, db_obj=job, obj_in={
        "status": "completed",
        "progress_percent": 100,
        "status_message": f"Nghiên cứu hoàn tất. Đã trích xuất {len(saved_sources)} nguồn học thuật uy tín."
    })

    return {
        "job_id": job.id,
        "sources_found": len(saved_sources),
        "sources": [SourceResponse.model_validate(s) for s in saved_sources]
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
