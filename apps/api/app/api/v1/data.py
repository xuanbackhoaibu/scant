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


# Phase U17: Connectors, Mapping, Dependency Graph

class ConnectorTestRequest(BaseModel):
    connector_type: str  # csv, postgresql, mysql, rest
    config: Dict[str, Any]


class SmartMappingRequest(BaseModel):
    columns: List[str]


class SaveMappingRequest(BaseModel):
    columns: List[str]
    mapping: Dict[str, str]


class RegisterDependencyRequest(BaseModel):
    report_id: str
    source_node: str  # dataset_id or kpi_id
    target_node: str  # chart_id or section_id


class InvalidateDependencyRequest(BaseModel):
    report_id: str
    source_node: str


@router.post("/connectors/test")
async def test_connector(
    req: ConnectorTestRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.connectors import get_connector
    connector = get_connector(req.connector_type, req.config)
    return await connector.test_connection()


@router.post("/connectors/schema")
async def get_connector_schema(
    req: ConnectorTestRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.connectors import get_connector
    connector = get_connector(req.connector_type, req.config)
    return await connector.get_schema()


@router.post("/mapping/infer")
async def infer_canonical_mapping(
    req: SmartMappingRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.smart_mapping_service import smart_mapping_service
    mapping = smart_mapping_service.infer_canonical_mapping(req.columns)
    fingerprint = smart_mapping_service.compute_fingerprint(req.columns)
    return {"fingerprint": fingerprint, "mapping": mapping}


@router.post("/mapping/save")
async def save_canonical_mapping(
    req: SaveMappingRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.smart_mapping_service import smart_mapping_service
    fp = smart_mapping_service.save_custom_mapping(req.columns, req.mapping)
    return {"status": "saved", "fingerprint": fp}


@router.post("/dependency/register")
async def register_dependency(
    req: RegisterDependencyRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.dependency_graph_service import dependency_graph_service
    dependency_graph_service.register_dependency(req.report_id, req.source_node, req.target_node)
    return {"status": "registered", "source": req.source_node, "target": req.target_node}


@router.post("/dependency/invalidate")
async def invalidate_dependency(
    req: InvalidateDependencyRequest,
    current_user: User = Depends(get_current_user),
):
    from app.services.data.dependency_graph_service import dependency_graph_service
    stale_nodes = dependency_graph_service.invalidate_source(req.report_id, req.source_node)
    return {"report_id": req.report_id, "stale_nodes": list(stale_nodes)}

