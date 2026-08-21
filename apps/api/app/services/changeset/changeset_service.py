import difflib
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import AIChangeSet, AIChange, ReportSection, Report
from app.repositories.base import BaseRepository
from app.repositories.report_repo import section_repo


class ChangeSetService:
    """
    AI ChangeSet and Diff System (Phase U13).
    Ensures safe review, diff visualization, and granular accept/reject controls for AI modifications.
    """

    @classmethod
    async def create_changeset(
        cls,
        db: AsyncSession,
        report_id: str,
        user_id: Optional[str],
        summary: str,
        changes: List[Dict[str, Any]]
    ) -> AIChangeSet:
        cs_repo = BaseRepository[AIChangeSet](AIChangeSet)
        change_repo = BaseRepository[AIChange](AIChange)

        change_set = await cs_repo.create(db, obj_in={
            "report_id": report_id,
            "user_id": user_id,
            "status": "pending",
            "summary": summary,
        })

        for ch in changes:
            await change_repo.create(db, obj_in={
                "change_set_id": change_set.id,
                "section_id": ch["section_id"],
                "change_type": ch.get("change_type", "replace"),
                "description": ch.get("description", "Đề xuất chỉnh sửa từ AI"),
                "before_text": ch.get("before_text", ""),
                "after_text": ch.get("after_text", ""),
                "before_json": ch.get("before_json", {}),
                "after_json": ch.get("after_json", {}),
                "status": "pending",
            })

        # Reload with changes
        stmt = select(AIChangeSet).where(AIChangeSet.id == change_set.id)
        res = await db.execute(stmt)
        return res.scalar_one()

    @classmethod
    async def accept_change(cls, db: AsyncSession, change_id: str) -> Dict[str, Any]:
        change_repo = BaseRepository[AIChange](AIChange)
        ch = await change_repo.get(db, change_id)
        if not ch:
            return {"error": "Change not found"}

        # Apply to Section
        sec = await section_repo.get(db, ch.section_id)
        if sec:
            await section_repo.update(db, db_obj=sec, obj_in={
                "plain_text": ch.after_text,
                "content_json": ch.after_json if ch.after_json else sec.content_json,
                "word_count": len((ch.after_text or "").split()),
            })

        await change_repo.update(db, db_obj=ch, obj_in={"status": "accepted"})
        return {"status": "accepted", "change_id": ch.id, "section_id": ch.section_id}

    @classmethod
    async def reject_change(cls, db: AsyncSession, change_id: str) -> Dict[str, Any]:
        change_repo = BaseRepository[AIChange](AIChange)
        ch = await change_repo.get(db, change_id)
        if not ch:
            return {"error": "Change not found"}

        await change_repo.update(db, db_obj=ch, obj_in={"status": "rejected"})
        return {"status": "rejected", "change_id": ch.id}

    @classmethod
    async def accept_all(cls, db: AsyncSession, change_set_id: str) -> Dict[str, Any]:
        cs_repo = BaseRepository[AIChangeSet](AIChangeSet)
        cs = await cs_repo.get(db, change_set_id)
        if not cs:
            return {"error": "ChangeSet not found"}

        stmt = select(AIChange).where(AIChange.change_set_id == change_set_id, AIChange.status == "pending")
        res = await db.execute(stmt)
        pending_changes = res.scalars().all()

        for ch in pending_changes:
            await cls.accept_change(db, ch.id)

        await cs_repo.update(db, db_obj=cs, obj_in={"status": "accepted"})
        return {"status": "accepted", "changes_count": len(pending_changes)}

    @classmethod
    async def reject_all(cls, db: AsyncSession, change_set_id: str) -> Dict[str, Any]:
        cs_repo = BaseRepository[AIChangeSet](AIChangeSet)
        cs = await cs_repo.get(db, change_set_id)
        if not cs:
            return {"error": "ChangeSet not found"}

        stmt = select(AIChange).where(AIChange.change_set_id == change_set_id, AIChange.status == "pending")
        res = await db.execute(stmt)
        pending_changes = res.scalars().all()

        for ch in pending_changes:
            await cls.reject_change(db, ch.id)

        await cs_repo.update(db, db_obj=cs, obj_in={"status": "rejected"})
        return {"status": "rejected", "changes_count": len(pending_changes)}

    @classmethod
    def compute_diff(cls, before_text: str, after_text: str) -> List[Dict[str, Any]]:
        """Computes granular diff segments with type: 'added', 'removed', or 'unchanged'."""
        before_words = (before_text or "").split(" ")
        after_words = (after_text or "").split(" ")

        matcher = difflib.SequenceMatcher(None, before_words, after_words)
        segments: List[Dict[str, Any]] = []

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                segments.append({"type": "unchanged", "text": " ".join(before_words[i1:i2])})
            elif tag == "delete":
                segments.append({"type": "removed", "text": " ".join(before_words[i1:i2])})
            elif tag == "insert":
                segments.append({"type": "added", "text": " ".join(after_words[j1:j2])})
            elif tag == "replace":
                segments.append({"type": "removed", "text": " ".join(before_words[i1:i2])})
                segments.append({"type": "added", "text": " ".join(after_words[j1:j2])})

        return segments


changeset_service = ChangeSetService()
