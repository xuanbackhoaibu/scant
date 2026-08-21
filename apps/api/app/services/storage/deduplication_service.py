import hashlib
from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.entities import UploadedFile


class DeduplicationService:
    """
    SHA-256 File Deduplication Service (Phase U21).
    Detects duplicate file uploads to reuse existing stored objects and optimize storage quota.
    """

    @staticmethod
    def compute_sha256(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    async def find_existing_file_by_hash(
        db: AsyncSession,
        checksum: str,
        user_id: Optional[str] = None
    ) -> Optional[UploadedFile]:
        stmt = select(UploadedFile).where(UploadedFile.file_hash == checksum)
        if user_id:
            stmt = stmt.where(UploadedFile.user_id == user_id)
        res = await db.execute(stmt)
        return res.scalar_one_or_none()


deduplication_service = DeduplicationService()
