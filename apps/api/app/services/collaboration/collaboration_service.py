from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import ProjectMember, Project, Comment, User, AuditLog
from app.repositories.base import BaseRepository
from app.repositories.project_repo import project_repo


class CollaborationService:
    """
    Collaboration Foundation Service (Phase U14).
    Enforces Role-Based Access Control (RBAC), Comment Threads, and Project Audit Trail.
    """

    ROLE_HIERARCHY = {
        "viewer": 1,
        "commenter": 2,
        "editor": 3,
        "owner": 4,
    }

    @classmethod
    async def get_user_role(cls, db: AsyncSession, user_id: str, project_id: str) -> Optional[str]:
        project = await project_repo.get(db, project_id)
        if not project:
            return None
        if project.user_id == user_id:
            return "owner"

        stmt = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
        res = await db.execute(stmt)
        member = res.scalar_one_or_none()
        return member.role if member else None

    @classmethod
    async def check_permission(cls, db: AsyncSession, user_id: str, project_id: str, required_role: str = "viewer") -> bool:
        role = await cls.get_user_role(db, user_id, project_id)
        if not role:
            return False
        return cls.ROLE_HIERARCHY.get(role, 0) >= cls.ROLE_HIERARCHY.get(required_role, 0)

    @classmethod
    async def add_member(
        cls,
        db: AsyncSession,
        project_id: str,
        role: str = "editor",
        invited_email: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> ProjectMember:
        mem_repo = BaseRepository[ProjectMember](ProjectMember)

        if invited_email and not user_id:
            user_stmt = select(User).where(User.email == invited_email)
            u_res = await db.execute(user_stmt)
            found_user = u_res.scalar_one_or_none()
            if found_user:
                user_id = found_user.id

        member = await mem_repo.create(db, obj_in={
            "project_id": project_id,
            "user_id": user_id,
            "invited_email": invited_email,
            "role": role,
        })
        return member

    @classmethod
    async def list_members(cls, db: AsyncSession, project_id: str) -> List[Dict[str, Any]]:
        project = await project_repo.get(db, project_id)
        if not project:
            return []

        stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
        res = await db.execute(stmt)
        members = res.scalars().all()

        output = [
            {
                "id": "owner",
                "project_id": project.id,
                "user_id": project.user_id,
                "role": "owner",
                "invited_email": None,
                "is_owner": True,
            }
        ]

        for m in members:
            output.append({
                "id": m.id,
                "project_id": m.project_id,
                "user_id": m.user_id,
                "role": m.role,
                "invited_email": m.invited_email,
                "is_owner": False,
            })

        return output

    @classmethod
    async def post_comment(
        cls,
        db: AsyncSession,
        report_id: str,
        user_id: str,
        comment_text: str,
        section_id: Optional[str] = None,
        parent_id: Optional[str] = None,
        mentions: Optional[List[str]] = None,
        selected_text: Optional[str] = None,
    ) -> Comment:
        comm_repo = BaseRepository[Comment](Comment)
        return await comm_repo.create(db, obj_in={
            "report_id": report_id,
            "report_section_id": section_id,
            "user_id": user_id,
            "parent_id": parent_id,
            "comment_text": comment_text,
            "selected_text": selected_text,
            "status": "open",
            "mentions_json": mentions or [],
        })

    @classmethod
    async def list_comments(cls, db: AsyncSession, report_id: str) -> List[Dict[str, Any]]:
        stmt = select(Comment).where(Comment.report_id == report_id, Comment.parent_id.is_(None)).order_by(Comment.created_at.asc())
        res = await db.execute(stmt)
        root_comments = res.scalars().all()

        output = []
        for c in root_comments:
            # fetch replies
            rep_stmt = select(Comment).where(Comment.parent_id == c.id).order_by(Comment.created_at.asc())
            rep_res = await db.execute(rep_stmt)
            replies = rep_res.scalars().all()

            output.append({
                "id": c.id,
                "report_id": c.report_id,
                "section_id": c.report_section_id,
                "user_id": c.user_id,
                "comment_text": c.comment_text,
                "selected_text": c.selected_text,
                "status": c.status,
                "mentions": c.mentions_json,
                "created_at": c.created_at,
                "replies": [
                    {
                        "id": r.id,
                        "user_id": r.user_id,
                        "comment_text": r.comment_text,
                        "status": r.status,
                        "created_at": r.created_at,
                    }
                    for r in replies
                ]
            })

        return output

    @classmethod
    async def resolve_comment(cls, db: AsyncSession, comment_id: str) -> Dict[str, Any]:
        comm_repo = BaseRepository[Comment](Comment)
        comm = await comm_repo.get(db, comment_id)
        if not comm:
            return {"error": "Comment not found"}

        await comm_repo.update(db, db_obj=comm, obj_in={"status": "resolved"})
        return {"status": "resolved", "comment_id": comm.id}


collaboration_service = CollaborationService()
