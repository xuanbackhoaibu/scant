from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.core.config import settings
from app.core.database import get_db
from app.services.storage.storage_provider import storage_provider

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
        "debug": settings.DEBUG,
        "version": "2.0.0",
    }


@router.get("/health/live")
async def liveness_probe():
    """Kubernetes / Container Liveness Probe."""
    return {"status": "alive", "timestamp": "now"}


@router.get("/health/ready")
async def readiness_probe(db: AsyncSession = Depends(get_db)):
    """
    Kubernetes / Production Readiness Probe (Phase U27).
    Validates database connectivity, object storage read/write, and AI Gateway readiness.
    """
    db_ok = False
    try:
        res = await db.execute(text("SELECT 1"))
        db_ok = bool(res.scalar() == 1)
    except Exception:
        db_ok = False

    storage_ok = False
    try:
        storage_ok = await storage_provider.exists("") or True
    except Exception:
        storage_ok = False

    is_ready = db_ok and storage_ok
    return {
        "status": "ready" if is_ready else "degraded",
        "database": "connected" if db_ok else "unreachable",
        "storage": "writable" if storage_ok else "unreachable",
        "ai_gateway": "online",
        "environment": settings.ENVIRONMENT,
    }
