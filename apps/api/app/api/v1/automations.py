from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.entities import User, Automation, AutomationRun, Project, UploadedFile, Template
from app.repositories.base import BaseRepository
from app.repositories.project_repo import project_repo
from app.api.deps import get_current_user
from app.services.automation.automation_engine import automation_engine
from app.services.automation.automation_scheduler import automation_scheduler

router = APIRouter(prefix="/automations", tags=["automations"])
auto_repo = BaseRepository[Automation](Automation)
run_repo = BaseRepository[AutomationRun](AutomationRun)


class CreateAutomationRequest(BaseModel):
    project_id: str
    name: str
    description: Optional[str] = None
    trigger_type: str = "manual"  # manual, schedule, data_refresh
    cron_expression: Optional[str] = None
    timezone: str = "Asia/Ho_Chi_Minh"
    data_source_id: Optional[str] = None
    source_type: str = "file"  # file, dataset, all_project_files
    source_config: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    analysis_prompt: Optional[str] = None
    analysis_mode: str = "comprehensive"  # comprehensive, kpi_financial, summary, academic
    report_title_pattern: str = "Báo cáo Tự động {date}"
    export_formats: Optional[List[str]] = None
    is_active: bool = True


class UpdateAutomationRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    trigger_type: Optional[str] = None
    cron_expression: Optional[str] = None
    timezone: Optional[str] = None
    data_source_id: Optional[str] = None
    source_type: Optional[str] = None
    source_config: Optional[Dict[str, Any]] = None
    template_id: Optional[str] = None
    analysis_prompt: Optional[str] = None
    analysis_mode: Optional[str] = None
    report_title_pattern: Optional[str] = None
    export_formats: Optional[List[str]] = None
    is_active: Optional[bool] = None


async def _ensure_automation_owner(db: AsyncSession, automation_id: str, current_user: User) -> Automation:
    auto = await auto_repo.get(db, automation_id)
    if not auto:
        raise HTTPException(status_code=404, detail="Automation not found")
    project = await project_repo.get(db, auto.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Automation not found")
    return auto


def _serialize_automation(a: Automation, project_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "id": a.id,
        "project_id": a.project_id,
        "project_name": project_name or (a.project.name if a.project else None),
        "name": a.name,
        "description": a.description,
        "trigger_type": a.trigger_type,
        "cron_expression": a.cron_expression,
        "timezone": a.timezone,
        "data_source_id": a.data_source_id,
        "source_type": a.source_type,
        "source_config": a.source_config_json or {},
        "template_id": a.template_id,
        "analysis_prompt": a.analysis_prompt,
        "analysis_mode": a.analysis_mode,
        "report_title_pattern": a.report_title_pattern,
        "export_formats": a.export_formats_json or ["docx"],
        "is_active": a.is_active,
        "last_run_at": a.last_run_at,
        "next_run_at": a.next_run_at,
        "created_at": a.created_at,
        "updated_at": a.updated_at,
    }


def _serialize_run(r: AutomationRun) -> Dict[str, Any]:
    return {
        "id": r.id,
        "automation_id": r.automation_id,
        "report_id": r.report_id,
        "status": r.status,
        "trigger_source": r.trigger_source,
        "retry_count": r.retry_count,
        "duration_ms": r.duration_ms,
        "source_snapshot": r.source_snapshot_json or {},
        "output_files": r.output_files_json or [],
        "failed_step": r.failed_step,
        "error_message": r.error_message,
        "logs": r.log_messages_json or [],
        "started_at": r.started_at,
        "finished_at": r.finished_at,
    }


@router.get("")
async def list_automations(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = (
        select(Automation, Project.name.label("project_name"))
        .join(Project, Automation.project_id == Project.id)
        .where(Project.user_id == current_user.id)
        .order_by(Automation.created_at.desc())
    )
    res = await db.execute(stmt)
    rows = res.all()
    return [_serialize_automation(row[0], project_name=row[1]) for row in rows]


@router.post("")
async def create_automation(
    req: CreateAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, req.project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    auto = await automation_engine.create_automation(
        db=db,
        project_id=req.project_id,
        user_id=current_user.id,
        name=req.name,
        description=req.description,
        trigger_type=req.trigger_type,
        cron_expression=req.cron_expression,
        timezone_name=req.timezone,
        data_source_id=req.data_source_id,
        source_type=req.source_type,
        source_config_json=req.source_config,
        template_id=req.template_id,
        analysis_prompt=req.analysis_prompt,
        analysis_mode=req.analysis_mode,
        report_title_pattern=req.report_title_pattern,
        export_formats=req.export_formats,
        is_active=req.is_active,
    )
    await db.commit()
    return _serialize_automation(auto, project_name=project.name)


@router.get("/{automation_id}")
async def get_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auto = await _ensure_automation_owner(db, automation_id, current_user)
    project = await project_repo.get(db, auto.project_id)
    return _serialize_automation(auto, project_name=project.name if project else None)


@router.put("/{automation_id}")
async def update_automation(
    automation_id: str,
    req: UpdateAutomationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auto = await _ensure_automation_owner(db, automation_id, current_user)

    update_dict = {k: v for k, v in req.model_dump().items() if v is not None}
    if "source_config" in update_dict:
        update_dict["source_config_json"] = update_dict.pop("source_config")

    updated = await automation_engine.update_automation(db, auto, update_dict)
    await db.commit()
    project = await project_repo.get(db, updated.project_id)
    return _serialize_automation(updated, project_name=project.name if project else None)


@router.delete("/{automation_id}")
async def delete_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auto = await _ensure_automation_owner(db, automation_id, current_user)
    await auto_repo.remove(db, id=auto.id)
    return {"message": "Automation deleted successfully", "id": automation_id}


@router.post("/{automation_id}/pause")
async def pause_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auto = await _ensure_automation_owner(db, automation_id, current_user)
    updated = await automation_engine.update_automation(db, auto, {"is_active": False, "next_run_at": None})
    await db.commit()
    return {"message": "Automation paused", "is_active": updated.is_active}


@router.post("/{automation_id}/resume")
async def resume_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    auto = await _ensure_automation_owner(db, automation_id, current_user)
    updated = await automation_engine.update_automation(db, auto, {"is_active": True})
    await db.commit()
    return {"message": "Automation resumed", "is_active": updated.is_active, "next_run_at": updated.next_run_at}


@router.post("/{automation_id}/trigger")
async def trigger_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_automation_owner(db, automation_id, current_user)
    return await automation_engine.execute_run(db, automation_id, trigger_source="manual")


@router.get("/{automation_id}/runs")
async def list_automation_runs(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await _ensure_automation_owner(db, automation_id, current_user)
    stmt = (
        select(AutomationRun)
        .where(AutomationRun.automation_id == automation_id)
        .order_by(AutomationRun.started_at.desc())
    )
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [_serialize_run(r) for r in runs]


@router.get("/runs/{run_id}")
async def get_automation_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await run_repo.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await _ensure_automation_owner(db, run.automation_id, current_user)
    return _serialize_run(run)


@router.post("/runs/{run_id}/retry")
async def retry_automation_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    run = await run_repo.get(db, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    await _ensure_automation_owner(db, run.automation_id, current_user)
    return await automation_engine.retry_run(db, run_id)
