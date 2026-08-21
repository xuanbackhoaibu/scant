from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.entities import Template, TemplateVersion
from app.repositories.base import BaseRepository


class TemplateRepository(BaseRepository[Template]):
    def __init__(self):
        super().__init__(Template)

    async def get_available(self, db: AsyncSession, user_id: Optional[str] = None) -> List[Template]:
        query = select(Template).options(selectinload(Template.versions))
        if user_id:
            query = query.where((Template.is_system == True) | (Template.is_public == True) | (Template.user_id == user_id))
        else:
            query = query.where((Template.is_system == True) | (Template.is_public == True))
        result = await db.execute(query.order_by(Template.created_at.desc()))
        return list(result.scalars().all())


template_repo = TemplateRepository()
template_version_repo = BaseRepository[TemplateVersion](TemplateVersion)
