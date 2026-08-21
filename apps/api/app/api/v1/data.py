from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project, UploadedFile
from app.repositories.project_repo import project_repo, file_repo
from app.api.deps import get_current_user
from app.services.data.data_engine import data_engine

router = APIRouter(prefix="/data", tags=["data"])


class AggregationRequest(BaseModel):
    file_id: str
    group_by: str
    metric_column: str
    aggregation: str = "sum"  # sum, mean, count, min, max
    top_n: int = 10


class ChartSpecRequest(BaseModel):
    file_id: str
    chart_type: str = "bar"  # bar, line, pie, donut, horizontal_bar, area
    group_by: str
    metric_column: str
    aggregation: str = "sum"
    title: Optional[str] = None


@router.get("/profile/{file_id}")
async def profile_file_dataset(
    file_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await file_repo.get(db, file_id)
    if not f:
        raise HTTPException(status_code=404, detail="File not found")

    if not Path(f.file_path).exists():
        raise HTTPException(status_code=404, detail="File path does not exist on disk")

    try:
        profile = data_engine.profile_dataset(f.file_path)
        return profile
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error analyzing dataset: {str(e)}")


@router.post("/aggregate")
async def aggregate_dataset(
    req: AggregationRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await file_repo.get(db, req.file_id)
    if not f or not Path(f.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        return data_engine.aggregate_data(
            file_path=f.file_path,
            group_by=req.group_by,
            metric_column=req.metric_column,
            aggregation=req.aggregation,
            top_n=req.top_n,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Aggregation error: {str(e)}")


@router.post("/chart-spec")
async def create_chart_specification(
    req: ChartSpecRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    f = await file_repo.get(db, req.file_id)
    if not f or not Path(f.file_path).exists():
        raise HTTPException(status_code=404, detail="File not found")

    try:
        return data_engine.build_chart_specification(
            file_path=f.file_path,
            chart_type=req.chart_type,
            group_by=req.group_by,
            metric_column=req.metric_column,
            aggregation=req.aggregation,
            title=req.title,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Chart building error: {str(e)}")
