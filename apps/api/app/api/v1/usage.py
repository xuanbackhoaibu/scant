from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from app.core.database import get_db
from app.models.entities import User, AIUsageEvent
from app.api.deps import get_current_user
from app.services.usage.quota_engine import quota_engine

router = APIRouter(prefix="/usage", tags=["usage"])


@router.get("/summary")
async def get_usage_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns aggregated monthly AI usage, cost, and document counts."""
    return await quota_engine.get_user_summary(db, current_user.id)


@router.get("/events")
async def get_usage_events(
    limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Returns recent individual AI request events."""
    stmt = (
        select(AIUsageEvent)
        .where(AIUsageEvent.user_id == current_user.id)
        .order_by(desc(AIUsageEvent.created_at))
        .limit(limit)
    )
    res = await db.execute(stmt)
    events = res.scalars().all()
    return [
        {
            "id": e.id,
            "task_type": e.task_type,
            "provider": e.provider,
            "model": e.model,
            "input_tokens": e.input_tokens,
            "output_tokens": e.output_tokens,
            "total_tokens": e.total_tokens,
            "estimated_cost_usd": e.estimated_cost_usd,
            "latency_ms": e.latency_ms,
            "status": e.status,
            "created_at": e.created_at.isoformat() if e.created_at else None,
        }
        for e in events
    ]


@router.get("/estimate-workload")
async def estimate_workload(
    job_type: str = Query("auto_create"),
    num_sections: int = Query(5),
    num_sources: int = Query(4),
    current_user: User = Depends(get_current_user),
):
    """Simulates expected token usage and cost for budget validation."""
    return quota_engine.estimate_workload(job_type, num_sections, num_sources)
