from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.entities import User, Automation, AutomationRun, Project
from app.repositories.base import BaseRepository
from app.repositories.project_repo import project_repo
from app.api.deps import get_current_user
from app.services.automation.automation_engine import automation_engine

router = APIRouter(prefix="/automations", tags=["automations"])
auto_repo = BaseRepository[Automation](Automation)
run_repo = BaseRepository[AutomationRun](AutomationRun)


class CreateAutomationRequest(BaseModel):
    project_id: str
    name: str
    trigger_type: str = "manual"  # manual, schedule, data_refresh
    cron_expression: Optional[str] = None
    data_source_id: Optional[str] = None
    template_id: Optional[str] = None
    report_title_pattern: str = "Báo cáo Tự động {date}"
    export_formats: Optional[List[str]] = None


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
        trigger_type=req.trigger_type,
        cron_expression=req.cron_expression,
        data_source_id=req.data_source_id,
        template_id=req.template_id,
        report_title_pattern=req.report_title_pattern,
        export_formats=req.export_formats,
    )
    return {
        "id": auto.id,
        "name": auto.name,
        "trigger_type": auto.trigger_type,
        "cron_expression": auto.cron_expression,
        "is_active": auto.is_active,
        "created_at": auto.created_at,
    }


@router.get("/project/{project_id}")
async def list_project_automations(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Automation).where(Automation.project_id == project_id).order_by(Automation.created_at.desc())
    res = await db.execute(stmt)
    autos = res.scalars().all()
    return [
        {
            "id": a.id,
            "name": a.name,
            "trigger_type": a.trigger_type,
            "cron_expression": a.cron_expression,
            "is_active": a.is_active,
            "last_run_at": a.last_run_at,
            "created_at": a.created_at,
        }
        for a in autos
    ]


@router.post("/{automation_id}/trigger")
async def trigger_automation(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await automation_engine.execute_run(db, automation_id, trigger_source="manual")


@router.get("/{automation_id}/runs")
async def list_automation_runs(
    automation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AutomationRun).where(AutomationRun.automation_id == automation_id).order_by(AutomationRun.started_at.desc())
    res = await db.execute(stmt)
    runs = res.scalars().all()
    return [
        {
            "id": r.id,
            "status": r.status,
            "trigger_source": r.trigger_source,
            "retry_count": r.retry_count,
            "report_id": r.report_id,
            "logs": r.log_messages_json,
            "error_message": r.error_message,
            "started_at": r.started_at,
            "finished_at": r.finished_at,
        }
        for r in runs
    ]


@router.post("/runs/{run_id}/retry")
async def retry_automation_run(
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await automation_engine.retry_run(db, run_id)
