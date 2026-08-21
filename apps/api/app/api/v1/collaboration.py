from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User
from app.api.deps import get_current_user
from app.services.collaboration.collaboration_service import collaboration_service

router = APIRouter(prefix="/collaboration", tags=["collaboration"])


class AddMemberRequest(BaseModel):
    project_id: str
    invited_email: str
    role: str = "editor"  # owner, editor, commenter, viewer


class PostCommentRequest(BaseModel):
    report_id: str
    comment_text: str
    section_id: Optional[str] = None
    parent_id: Optional[str] = None
    selected_text: Optional[str] = None
    mentions: Optional[List[str]] = None


@router.post("/members")
async def add_project_member(
    req: AddMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Check if current user is owner or editor
    has_perm = await collaboration_service.check_permission(db, current_user.id, req.project_id, required_role="owner")
    if not has_perm:
        raise HTTPException(status_code=403, detail="Only project owners can manage members")

    member = await collaboration_service.add_member(
        db=db,
        project_id=req.project_id,
        role=req.role,
        invited_email=req.invited_email,
    )
    return {"status": "success", "member_id": member.id, "role": member.role, "invited_email": member.invited_email}


@router.get("/projects/{project_id}/members")
async def list_project_members(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await collaboration_service.list_members(db, project_id)


@router.post("/comments")
async def post_comment(
    req: PostCommentRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    comm = await collaboration_service.post_comment(
        db=db,
        report_id=req.report_id,
        user_id=current_user.id,
        comment_text=req.comment_text,
        section_id=req.section_id,
        parent_id=req.parent_id,
        mentions=req.mentions,
        selected_text=req.selected_text,
    )
    return {
        "id": comm.id,
        "report_id": comm.report_id,
        "comment_text": comm.comment_text,
        "status": comm.status,
        "created_at": comm.created_at,
    }


@router.get("/reports/{report_id}/comments")
async def list_report_comments(
    report_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await collaboration_service.list_comments(db, report_id)


@router.post("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await collaboration_service.resolve_comment(db, comment_id)
