from typing import Any, Dict
from fastapi import APIRouter
from app.services.observability.metrics_collector import metrics_collector

router = APIRouter(prefix="/metrics", tags=["observability"])


@router.get("")
async def get_system_metrics():
    """Returns aggregated latency, throughput, and system performance metrics."""
    return metrics_collector.get_summary()
