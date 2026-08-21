from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project, Report, ReportSection, TemplateVersion
from app.repositories.project_repo import project_repo
from app.repositories.report_repo import report_repo, section_repo
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportDetailResponse,
    ReportSectionCreate, ReportSectionUpdate, ReportSectionResponse, OutlineItem
)
from app.api.deps import get_current_user

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    report_in: ReportCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, report_in.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    settings = report_in.document_settings or {
        "paper": "A4",
        "font_family": "Times New Roman",
        "font_size": 13,
        "line_spacing": 1.5,
        "margins": {"top": 20, "bottom": 20, "left": 30, "right": 20},
        "citation_style": "IEEE"
    }

    report = await report_repo.create(db, obj_in={
        "project_id": report_in.project_id,
        "template_version_id": report_in.template_version_id,
        "title": report_in.title,
        "report_type": report_in.report_type,
        "status": "drafting",
        "revision": 1,
        "document_settings_json": settings,
    })

    # If outline is provided, populate report sections
    sections_created: List[ReportSection] = []
    global_pos = 0

    if report_in.outline:
        for parent_item in report_in.outline:
            global_pos += 1
            # Initial placeholder Tiptap structure
            parent_tiptap = {
                "type": "doc",
                "content": [
                    {
                        "type": "heading",
                        "attrs": {"level": parent_item.level},
                        "content": [{"type": "text", "text": parent_item.title}]
                    },
                    {
                        "type": "paragraph",
                        "content": [{"type": "text", "text": f"Nội dung cho {parent_item.title}..."}]
                    }
                ]
            }

            parent_sec = await section_repo.create(db, obj_in={
                "report_id": report.id,
                "parent_id": None,
                "title": parent_item.title,
                "position": global_pos,
                "level": parent_item.level,
                "section_number": parent_item.section_number,
                "status": "planned",
                "content_json": parent_tiptap,
                "plain_text": f"{parent_item.title}\n\nNội dung cho {parent_item.title}...",
                "word_count": len(f"{parent_item.title} Nội dung".split()),
                "structured_summary_json": {}
            })
            sections_created.append(parent_sec)

            for child_item in parent_item.children:
                global_pos += 1
                child_tiptap = {
                    "type": "doc",
                    "content": [
                        {
                            "type": "heading",
                            "attrs": {"level": child_item.level},
                            "content": [{"type": "text", "text": child_item.title}]
                        },
                        {
                            "type": "paragraph",
                            "content": [{"type": "text", "text": f"Nội dung chi tiết cho mục {child_item.title}..."}]
                        }
                    ]
                }
                child_sec = await section_repo.create(db, obj_in={
                    "report_id": report.id,
                    "parent_id": parent_sec.id,
                    "title": child_item.title,
                    "position": global_pos,
                    "level": child_item.level,
                    "section_number": child_item.section_number,
                    "status": "planned",
                    "content_json": child_tiptap,
                    "plain_text": f"{child_item.title}\n\nNội dung chi tiết cho mục {child_item.title}...",
                    "word_count": len(f"{child_item.title} Nội dung chi tiết".split()),
                    "structured_summary_json": {}
                })
                sections_created.append(child_sec)

    return ReportDetailResponse(
        id=report.id,
        project_id=report.project_id,
        template_version_id=report.template_version_id,
        title=report.title,
        report_type=report.report_type,
        status=report.status,
        revision=report.revision,
        document_settings_json=report.document_settings_json,
        created_at=report.created_at,
        updated_at=report.updated_at,
        sections=[ReportSectionResponse.model_validate(s) for s in sections_created],
        total_words=sum(s.word_count for s in sections_created),
        sources_count=0,
        citations_count=0,
    )


@router.get("/{report_id}", response_model=ReportDetailResponse)
async def get_report(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await report_repo.get_with_sections(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    project = await project_repo.get(db, report.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Report not found")

    sections = await section_repo.get_by_report(db, report_id)

    return ReportDetailResponse(
        id=report.id,
        project_id=report.project_id,
        template_version_id=report.template_version_id,
        title=report.title,
        report_type=report.report_type,
        status=report.status,
        revision=report.revision,
        document_settings_json=report.document_settings_json,
        created_at=report.created_at,
        updated_at=report.updated_at,
        sections=[ReportSectionResponse.model_validate(s) for s in sections],
        total_words=sum(s.word_count for s in sections),
        sources_count=len(project.sources) if project.sources else 0,
        citations_count=0,
    )


@router.put("/sections/{section_id}", response_model=ReportSectionResponse)
async def update_section(
    section_id: str,
    section_in: ReportSectionUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    section = await section_repo.get(db, section_id)
    if not section:
        raise HTTPException(status_code=404, detail="Section not found")

    update_dict = section_in.model_dump(exclude_unset=True)
    if "plain_text" in update_dict and "word_count" not in update_dict:
        update_dict["word_count"] = len((update_dict["plain_text"] or "").split())

    updated = await section_repo.update(db, db_obj=section, obj_in=update_dict)
    return ReportSectionResponse.model_validate(updated)
