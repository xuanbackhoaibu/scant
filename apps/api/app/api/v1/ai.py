from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project, Report, ReportSection, Document
from app.repositories.project_repo import project_repo, document_repo
from app.repositories.report_repo import report_repo, section_repo
from app.repositories.source_repo import source_repo
from app.schemas.ai import (
    OutlineGenerationRequest, OutlineGenerationResponse,
    SectionDraftRequest, SectionEditRequest, AICompletionResponse,
    ReportQualityCheckResponse
)
from app.api.deps import get_current_user
from app.services.editor.outline_service import outline_service
from app.services.editor.writing_engine import writing_engine
from app.services.editor.context_summarizer import context_summarizer

router = APIRouter(prefix="/ai", tags=["ai"])


@router.post("/generate-outline", response_model=OutlineGenerationResponse)
async def generate_outline(
    req: OutlineGenerationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, req.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    if not req.requirements_text:
        docs = await document_repo.get_multi(db, project_id=req.project_id)
        req_docs = [d.content_text for d in docs if d.document_type in ["requirement", "rubric"]]
        if req_docs:
            req.requirements_text = "\n\n".join(req_docs)[:4000]

    outline_result = await outline_service.generate_outline(req)
    return outline_result


@router.post("/draft-section", response_model=AICompletionResponse)
async def draft_section(
    req: SectionDraftRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, req.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    section = await section_repo.get(db, req.section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    # Fetch sources and previous sections for context chaining
    sources = await source_repo.get_by_project(db, req.project_id)
    all_sections = await section_repo.get_by_report(db, req.report_id)
    prev_sections = [s for s in all_sections if s.position < section.position]
    chain_summary = context_summarizer.build_chain_summary(prev_sections)

    sources_dicts = [
        {
            "id": s.id,
            "title": s.title,
            "url": s.url,
            "authors": s.authors,
            "publisher": s.publisher,
            "published_date": s.published_date,
            "summary": s.summary,
            "reliability_score": s.reliability_score
        }
        for s in sources
    ]

    draft_result = await writing_engine.draft_section(
        section_title=section.title,
        section_level=section.level,
        topic_name=project.name,
        sources=sources_dicts,
        previous_summary=chain_summary,
        instruction=req.instruction,
        tone=req.tone,
    )

    # Update section in DB
    await section_repo.update(db, db_obj=section, obj_in={
        "status": "draft",
        "content_json": draft_result["tiptap_json"],
        "plain_text": draft_result["plain_text"],
        "word_count": draft_result["word_count"],
    })

    return AICompletionResponse(
        text=draft_result["plain_text"],
        tiptap_json=draft_result["tiptap_json"],
        claims_verified=draft_result["claims_verified"],
        tokens_used=draft_result["tokens_used"],
    )


@router.post("/edit-selection")
async def edit_selection(
    req: SectionEditRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, req.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    edited_text = await writing_engine.edit_selection(
        selected_text=req.selected_text,
        action=req.action,
        custom_instruction=req.custom_instruction,
    )
    return {"edited_text": edited_text}


@router.post("/check-report/{report_id}", response_model=ReportQualityCheckResponse)
async def check_report_quality(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await report_repo.get(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    project = await project_repo.get(db, report.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    sections = await section_repo.get_by_report(db, report_id)
    sources = await source_repo.get_by_project(db, project.id)

    quality = writing_engine.check_report_quality(sections=sections, sources_count=len(sources))
    return ReportQualityCheckResponse(**quality)
