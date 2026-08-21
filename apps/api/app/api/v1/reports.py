import asyncio
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Form, UploadFile, File
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
    from app.repositories.source_repo import source_repo
    sources = await source_repo.get_by_project(db, project.id)

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
        sources_count=len(sources),
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


@router.post("/{report_id}/generate-all")
async def start_agentic_report_generation(
    report_id: str,
    instructions: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Starts the 12-step autonomous document generation engine."""
    report = await report_repo.get(db, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    project = await project_repo.get(db, report.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    from app.models.entities import Job
    from app.repositories.base import BaseRepository
    from app.services.agent.agentic_report_orchestrator import agentic_orchestrator

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.create(db, obj_in={
        "project_id": project.id,
        "job_type": "agentic_report_generation",
        "status": "running",
        "progress_percent": 5,
        "status_message": "Đang khởi tạo Agentic Report Engine...",
        "payload_json": {"report_id": report.id},
    })

    # Run workflow
    asyncio_task = asyncio.create_task(
        agentic_orchestrator.run_workflow(
            db=db,
            job_id=job.id,
            project_id=project.id,
            report_id=report.id,
            instructions=instructions,
        )
    )

    return {
        "job_id": job.id,
        "status": "running",
        "message": "Hệ thống Agentic Report Engine đã bắt đầu thực thi tự động.",
    }


@router.post("/auto-create")
async def one_click_auto_create(
    prompt: str = Form(...),
    template_id: Optional[str] = Form(None),
    files: Optional[List[UploadFile]] = File(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Phase U11: One-Click Autonomous Report Generation."""
    from app.services.editor.outline_service import outline_service
    from app.schemas.ai import AnalyzeIntentRequest
    from app.models.entities import Job, UploadedFile, Document
    from app.repositories.base import BaseRepository
    from app.repositories.project_repo import file_repo, document_repo
    from app.services.agent.agentic_report_orchestrator import agentic_orchestrator
    from app.services.documents.pdf_parser import pdf_parser
    from app.services.documents.docx_parser import docx_parser
    from app.services.documents.excel_parser import excel_parser
    from app.core.config import settings
    import hashlib
    from pathlib import Path

    # 1. AI Intent Analysis
    intent = await outline_service.analyze_intent(AnalyzeIntentRequest(user_prompt=prompt))

    # 2. Create Project
    project = await project_repo.create(db, obj_in={
        "user_id": current_user.id,
        "name": intent.suggested_title or prompt[:60],
        "type": intent.suggested_type,
        "description": intent.objective,
        "metadata_json": {
            "document_type": intent.suggested_type,
            "document_profile": intent.suggested_type,
            "audience": intent.target_audience,
            "custom_fields": intent.suggested_custom_fields or [],
        }
    })

    # 3. Upload and parse any attached files
    if files:
        for f in files:
            contents = await f.read()
            if not contents:
                continue
            filename = f.filename or "attachment"
            ext = Path(filename).suffix.lower()
            file_hash = hashlib.sha256(contents).hexdigest()
            stored_filename = f"{project.id}_{file_hash[:12]}_{filename}"
            file_path = settings.UPLOAD_DIR / stored_filename
            with open(file_path, "wb") as out_f:
                out_f.write(contents)

            cat = "pdf" if ext == ".pdf" else "docx" if ext in [".docx", ".doc"] else "excel" if ext in [".xlsx", ".xls", ".csv"] else "text"
            up_file = await file_repo.create(db, obj_in={
                "project_id": project.id,
                "filename": stored_filename,
                "original_name": filename,
                "file_type": cat,
                "mime_type": f.content_type or "application/octet-stream",
                "file_size": len(contents),
                "file_path": str(file_path),
                "file_hash": file_hash,
                "is_parsed": True,
            })

            # Extract text
            try:
                txt = ""
                if cat == "pdf":
                    txt = pdf_parser.extract_text_and_metadata(str(file_path)).get("full_text", "")
                elif cat == "docx":
                    txt = docx_parser.extract_document(str(file_path)).get("full_text", "")
                elif cat == "text":
                    txt = contents.decode("utf-8", errors="ignore")
                elif cat == "excel":
                    txt = f"Dataset: {filename}"
                if txt:
                    await document_repo.create(db, obj_in={
                        "project_id": project.id,
                        "file_id": up_file.id,
                        "title": filename,
                        "content_text": txt,
                        "document_type": "dataset" if cat == "excel" else "reference",
                        "token_count": len(txt) // 4,
                    })
            except Exception:
                pass

    # 4. Create Initial Report
    report = await report_repo.create(db, obj_in={
        "project_id": project.id,
        "template_version_id": template_id,
        "title": project.name,
        "report_type": intent.suggested_type,
        "status": "generating",
        "revision": 1,
    })

    # 5. Create Job Record
    job_repo = BaseRepository[Job](Job)
    job = await job_repo.create(db, obj_in={
        "project_id": project.id,
        "job_type": "one_click_auto_report",
        "status": "running",
        "progress_percent": 5,
        "status_message": "Đang khởi tạo quy trình One-Click Auto Report...",
        "payload_json": {"report_id": report.id, "prompt": prompt},
        "metadata_json": {"report_id": report.id, "project_id": project.id},
    })

    # 6. Launch background execution
    asyncio.create_task(
        agentic_orchestrator.run_workflow(
            db=db,
            job_id=job.id,
            project_id=project.id,
            report_id=report.id,
            instructions=prompt,
        )
    )

    return {
        "job_id": job.id,
        "project_id": project.id,
        "report_id": report.id,
        "status": "running",
        "message": "Hệ thống One-Click Auto Report đang tự động khởi tạo báo cáo hoàn chỉnh.",
    }


@router.post("/jobs/{job_id}/pause")
async def pause_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.entities import Job
    from app.repositories.base import BaseRepository

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await job_repo.update(db, db_obj=job, obj_in={"status": "paused", "status_message": "Quy trình đang tạm dừng."})
    return {"job_id": job.id, "status": "paused"}


@router.post("/jobs/{job_id}/resume")
async def resume_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.entities import Job
    from app.repositories.base import BaseRepository

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await job_repo.update(db, db_obj=job, obj_in={"status": "running", "status_message": "Tiếp tục thực thi quy trình..."})
    return {"job_id": job.id, "status": "running"}


@router.post("/jobs/{job_id}/cancel")
async def cancel_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.entities import Job
    from app.repositories.base import BaseRepository

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    await job_repo.update(db, db_obj=job, obj_in={"status": "cancelled", "status_message": "Quy trình đã bị hủy bỏ."})
    return {"job_id": job.id, "status": "cancelled"}


@router.post("/jobs/{job_id}/retry")
async def retry_job(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.entities import Job
    from app.repositories.base import BaseRepository
    from app.services.agent.agentic_report_orchestrator import agentic_orchestrator

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    report_id = (job.metadata_json or {}).get("report_id") or (job.payload_json or {}).get("report_id")
    if not report_id:
        raise HTTPException(status_code=400, detail="Cannot retry: missing report_id in job metadata")

    await job_repo.update(db, db_obj=job, obj_in={
        "status": "running",
        "progress_percent": 5,
        "status_message": "Đang thực hiện lại quy trình...",
        "error_message": None,
    })

    asyncio.create_task(
        agentic_orchestrator.run_workflow(
            db=db,
            job_id=job.id,
            project_id=job.project_id,
            report_id=report_id,
            instructions=(job.payload_json or {}).get("prompt"),
        )
    )

    return {"job_id": job.id, "status": "running", "message": "Đã khởi động lại quy trình thành công."}


@router.get("/jobs/{job_id}")
async def get_job_status(
    job_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.models.entities import Job
    from app.repositories.base import BaseRepository

    job_repo = BaseRepository[Job](Job)
    job = await job_repo.get(db, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    return {
        "job_id": job.id,
        "status": job.status,
        "progress_percent": job.progress_percent,
        "status_message": job.status_message,
        "metadata": job.metadata_json or {},
        "payload": job.payload_json or {},
        "created_at": job.created_at,
        "updated_at": job.updated_at,
    }

