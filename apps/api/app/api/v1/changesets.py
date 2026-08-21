from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models.entities import User, AIChangeSet, AIChange, Report
from app.repositories.base import BaseRepository
from app.repositories.report_repo import report_repo
from app.api.deps import get_current_user
from app.services.changeset.changeset_service import changeset_service

router = APIRouter(prefix="/changesets", tags=["changesets"])
cs_repo = BaseRepository[AIChangeSet](AIChangeSet)
change_repo = BaseRepository[AIChange](AIChange)


class SingleChangePayload(BaseModel):
    section_id: str
    change_type: str = "replace"  # insert, replace, rewrite, delete
    description: Optional[str] = None
    before_text: str = ""
    after_text: str = ""
    before_json: Optional[Dict[str, Any]] = None
    after_json: Optional[Dict[str, Any]] = None


class CreateChangeSetRequest(BaseModel):
    report_id: str
    summary: str
    changes: List[SingleChangePayload]


@router.post("")
async def create_changeset(
    req: CreateChangeSetRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    report = await report_repo.get(db, req.report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    changes_dicts = [c.model_dump() for c in req.changes]
    cs = await changeset_service.create_changeset(
        db=db,
        report_id=req.report_id,
        user_id=current_user.id,
        summary=req.summary,
        changes=changes_dicts,
    )

    return {
        "id": cs.id,
        "report_id": cs.report_id,
        "status": cs.status,
        "summary": cs.summary,
        "changes_count": len(req.changes),
        "created_at": cs.created_at,
    }


@router.get("/report/{report_id}")
async def list_report_changesets(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(AIChangeSet).where(AIChangeSet.report_id == report_id).order_by(AIChangeSet.created_at.desc())
    res = await db.execute(stmt)
    change_sets = res.scalars().all()

    output = []
    for cs in change_sets:
        # Load individual changes
        ch_stmt = select(AIChange).where(AIChange.change_set_id == cs.id)
        ch_res = await db.execute(ch_stmt)
        changes = ch_res.scalars().all()

        output.append({
            "id": cs.id,
            "report_id": cs.report_id,
            "status": cs.status,
            "summary": cs.summary,
            "created_at": cs.created_at,
            "changes": [
                {
                    "id": ch.id,
                    "section_id": ch.section_id,
                    "change_type": ch.change_type,
                    "description": ch.description,
                    "before_text": ch.before_text,
                    "after_text": ch.after_text,
                    "status": ch.status,
                    "diff_segments": changeset_service.compute_diff(ch.before_text, ch.after_text),
                }
                for ch in changes
            ]
        })

    return output


@router.post("/{change_set_id}/accept-all")
async def accept_all_changes(
    change_set_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await changeset_service.accept_all(db, change_set_id)


@router.post("/{change_set_id}/reject-all")
async def reject_all_changes(
    change_set_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await changeset_service.reject_all(db, change_set_id)


@router.post("/changes/{change_id}/accept")
async def accept_single_change(
    change_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await changeset_service.accept_change(db, change_id)


@router.post("/changes/{change_id}/reject")
async def reject_single_change(
    change_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await changeset_service.reject_change(db, change_id)
