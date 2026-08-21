from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Workspace
from app.api.deps import get_current_user

router = APIRouter(prefix="/brand-kit", tags=["brand-kit"])


class BrandKitPayload(BaseModel):
    primary_color: str = "#1E3A8A"
    secondary_color: str = "#0D9488"
    primary_font: str = "Inter"
    heading_font: str = "Inter"
    header_text: str = "DOANH NGHIỆP • BÁO CÁO CHIẾN LƯỢC"
    confidentiality_notice: str = "STRICTLY CONFIDENTIAL"
    logo_url: Optional[str] = None
    custom_colors: Dict[str, str] = Field(default_factory=dict)


@router.get("")
async def get_current_brand_kit(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieves current workspace brand kit from database."""
    stmt = select(Workspace).where(Workspace.user_id == current_user.id)
    res = await db.execute(stmt)
    ws = res.scalars().first()
    if not ws:
        return BrandKitPayload().model_dump()
    return ws.brand_kit_json or BrandKitPayload().model_dump()


@router.put("")
async def update_brand_kit(
    payload: BrandKitPayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Persists updated Brand Kit settings into workspace in database."""
    stmt = select(Workspace).where(Workspace.user_id == current_user.id)
    res = await db.execute(stmt)
    ws = res.scalars().first()
    if not ws:
        # Create workspace if missing
        ws = Workspace(
            user_id=current_user.id,
            name=f"{current_user.name}'s Workspace",
            slug=f"ws-{current_user.id[:8]}",
            brand_kit_json=payload.model_dump(),
        )
        db.add(ws)
    else:
        ws.brand_kit_json = payload.model_dump()

    await db.commit()
    await db.refresh(ws)
    return ws.brand_kit_json
