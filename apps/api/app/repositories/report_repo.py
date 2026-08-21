from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.entities import Report, ReportSection, ReportVersion
from app.repositories.base import BaseRepository


class ReportRepository(BaseRepository[Report]):
    def __init__(self):
        super().__init__(Report)

    async def get_with_sections(self, db: AsyncSession, report_id: str) -> Optional[Report]:
        result = await db.execute(
            select(Report)
            .where(Report.id == report_id)
            .options(
                selectinload(Report.sections)
            )
        )
        return result.scalars().first()

    async def get_by_project(self, db: AsyncSession, project_id: str) -> List[Report]:
        result = await db.execute(
            select(Report)
            .where(Report.project_id == project_id)
            .order_by(Report.created_at.desc())
        )
        return list(result.scalars().all())


class ReportSectionRepository(BaseRepository[ReportSection]):
    def __init__(self):
        super().__init__(ReportSection)

    async def get_by_report(self, db: AsyncSession, report_id: str) -> List[ReportSection]:
        result = await db.execute(
            select(ReportSection)
            .where(ReportSection.report_id == report_id)
            .order_by(ReportSection.position.asc())
        )
        return list(result.scalars().all())


report_repo = ReportRepository()
section_repo = ReportSectionRepository()
report_version_repo = BaseRepository[ReportVersion](ReportVersion)
