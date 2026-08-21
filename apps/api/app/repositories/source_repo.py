from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.entities import Source, Citation, ClaimSource, Template, TemplateVersion
from app.repositories.base import BaseRepository


class SourceRepository(BaseRepository[Source]):
    def __init__(self):
        super().__init__(Source)

    async def get_by_project(self, db: AsyncSession, project_id: str) -> List[Source]:
        result = await db.execute(
            select(Source)
            .where(Source.project_id == project_id)
            .order_by(Source.created_at.desc())
        )
        return list(result.scalars().all())


class CitationRepository(BaseRepository[Citation]):
    def __init__(self):
        super().__init__(Citation)

    async def get_by_section(self, db: AsyncSession, section_id: str) -> List[Citation]:
        result = await db.execute(
            select(Citation)
            .where(Citation.report_section_id == section_id)
            .options(selectinload(Citation.source))
        )
        return list(result.scalars().all())


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


source_repo = SourceRepository()
citation_repo = CitationRepository()
claim_source_repo = BaseRepository[ClaimSource](ClaimSource)
template_repo = TemplateRepository()
template_version_repo = BaseRepository[TemplateVersion](TemplateVersion)
