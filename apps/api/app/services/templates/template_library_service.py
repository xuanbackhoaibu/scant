from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from app.models.entities import Template, TemplateVersion, User
from app.repositories.base import BaseRepository
from app.services.templates.external_template_catalog import list_external_templates


class TemplateLibraryService:
    """
    Template Library & Marketplace Service (Phase U15).
    Supports My Templates, Workspace Templates, Public Marketplace, duplicate, and publishing.
    """

    @classmethod
    async def list_templates(
        cls,
        db: AsyncSession,
        current_user_id: Optional[str] = None,
        scope: str = "public",  # my, workspace, public, all
        category: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stmt = select(Template)

        conditions = []

        if scope == "my" and current_user_id:
            conditions.append(Template.user_id == current_user_id)
        elif scope == "public":
            conditions.append(or_(Template.visibility == "public", Template.is_public == True, Template.is_system == True))
        elif scope == "workspace":
            conditions.append(Template.visibility == "workspace")
        else:
            # All accessible
            if current_user_id:
                conditions.append(or_(
                    Template.user_id == current_user_id,
                    Template.visibility.in_(["public", "workspace"]),
                    Template.is_public == True,
                    Template.is_system == True
                ))
            else:
                conditions.append(or_(Template.visibility == "public", Template.is_public == True, Template.is_system == True))

        if category and category.lower() != "all":
            conditions.append(Template.category == category.lower())

        if search:
            search_pattern = f"%{search}%"
            conditions.append(or_(
                Template.name.ilike(search_pattern),
                Template.description.ilike(search_pattern),
            ))

        if conditions:
            stmt = stmt.where(and_(*conditions))

        stmt = stmt.order_by(Template.usage_count.desc(), Template.created_at.desc())
        res = await db.execute(stmt)
        templates = res.scalars().all()

        output = []
        for t in templates:
            output.append({
                "id": t.id,
                "user_id": t.user_id,
                "name": t.name,
                "category": t.category,
                "description": t.description,
                "thumbnail_url": t.thumbnail_url,
                "visibility": t.visibility,
                "author_name": t.author_name,
                "usage_count": t.usage_count,
                "rating": t.rating,
                "tags": t.tags_json or [],
                "is_system": t.is_system,
                "is_public": t.is_public,
                "created_at": t.created_at,
            })

        if scope in ["public", "all"]:
            existing_ids = {item["id"] for item in output}
            output.extend(
                item
                for item in list_external_templates(category=category, search=search)
                if item["id"] not in existing_ids
            )

        return output

    @classmethod
    async def duplicate_template(
        cls,
        db: AsyncSession,
        template_id: str,
        user_id: str,
        user_name: str
    ) -> Dict[str, Any]:
        tpl_repo = BaseRepository[Template](Template)
        tpl = await tpl_repo.get(db, template_id)
        if not tpl:
            return {"error": "Template not found"}

        # Clone
        cloned = await tpl_repo.create(db, obj_in={
            "user_id": user_id,
            "name": f"{tpl.name} (Bản sao)",
            "category": tpl.category,
            "description": tpl.description,
            "thumbnail_url": tpl.thumbnail_url,
            "visibility": "my",
            "author_name": user_name,
            "usage_count": 0,
            "rating": 5.0,
            "tags_json": tpl.tags_json or [],
            "schema_json": tpl.schema_json or {},
            "is_system": False,
            "is_public": False,
        })

        return {"status": "success", "cloned_id": cloned.id, "name": cloned.name}

    @classmethod
    async def toggle_publish(
        cls,
        db: AsyncSession,
        template_id: str,
        user_id: str,
        publish: bool
    ) -> Dict[str, Any]:
        tpl_repo = BaseRepository[Template](Template)
        tpl = await tpl_repo.get(db, template_id)
        if not tpl or tpl.user_id != user_id:
            return {"error": "Not authorized to modify this template"}

        await tpl_repo.update(db, db_obj=tpl, obj_in={
            "visibility": "public" if publish else "my",
            "is_public": publish,
        })

        return {"status": "success", "visibility": "public" if publish else "my"}

    @classmethod
    async def record_usage(cls, db: AsyncSession, template_id: str) -> None:
        tpl_repo = BaseRepository[Template](Template)
        tpl = await tpl_repo.get(db, template_id)
        if tpl:
            await tpl_repo.update(db, db_obj=tpl, obj_in={"usage_count": tpl.usage_count + 1})


template_library_service = TemplateLibraryService()
