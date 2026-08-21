from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.models.entities import Project, UploadedFile, Document
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self):
        super().__init__(Project)

    async def get_by_user(self, db: AsyncSession, user_id: str) -> List[Project]:
        result = await db.execute(
            select(Project)
            .where(Project.user_id == user_id)
            .order_by(Project.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_with_details(self, db: AsyncSession, project_id: str) -> Optional[Project]:
        result = await db.execute(
            select(Project)
            .where(Project.id == project_id)
            .options(
                selectinload(Project.files),
                selectinload(Project.reports),
                selectinload(Project.sources)
            )
        )
        return result.scalars().first()


project_repo = ProjectRepository()
file_repo = BaseRepository[UploadedFile](UploadedFile)
document_repo = BaseRepository[Document](Document)
