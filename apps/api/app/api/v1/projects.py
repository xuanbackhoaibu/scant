from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse
from app.repositories.project_repo import project_repo
from app.api.deps import get_current_user
from app.services.metadata.metadata_helper import metadata_helper

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    projects = await project_repo.get_by_user(db, current_user.id)
    if not projects:
        default_proj = await project_repo.create(db, obj_in={
            "user_id": current_user.id,
            "name": "Dự Án Nghiên Cứu & Trích Dẫn Mặc Định",
            "type": "research",
            "description": "Không gian nghiên cứu, quản lý tài liệu và kiểm chứng trích dẫn",
            "settings_json": {},
            "metadata_json": {},
            "topic_details_json": {},
        })
        return [ProjectResponse.model_validate(default_proj)]
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Normalize metadata supporting both new custom_fields and legacy topic_details
    meta_dict = project_in.metadata.model_dump() if project_in.metadata else None
    normalized_meta = metadata_helper.normalize_metadata(
        project_type=project_in.type,
        metadata_input=meta_dict,
        legacy_topic_details=project_in.topic_details
    )

    project_data = {
        "user_id": current_user.id,
        "name": project_in.name,
        "type": project_in.type,
        "description": project_in.description,
        "settings_json": project_in.settings or {},
        "metadata_json": normalized_meta,
        "topic_details_json": project_in.topic_details or {},
    }

    project = await project_repo.create(db, obj_in=project_data)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )

    update_data: Dict[str, Any] = {}
    if project_in.name is not None:
        update_data["name"] = project_in.name
    if project_in.type is not None:
        update_data["type"] = project_in.type
    if project_in.description is not None:
        update_data["description"] = project_in.description
    if project_in.settings is not None:
        update_data["settings_json"] = project_in.settings
    if project_in.metadata is not None:
        update_data["metadata_json"] = project_in.metadata.model_dump()
    if project_in.topic_details is not None:
        update_data["topic_details_json"] = project_in.topic_details
        if "metadata_json" not in update_data:
            update_data["metadata_json"] = metadata_helper.normalize_metadata(
                project_type=project.type,
                legacy_topic_details=project_in.topic_details
            )

    updated_project = await project_repo.update(db, db_obj=project, obj_in=update_data)
    return ProjectResponse.model_validate(updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found",
        )
    await project_repo.remove(db, id=project_id)
    return None
