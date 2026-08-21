from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, Project
from app.repositories.project_repo import project_repo
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse, FileSummary
from app.api.deps import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    projects = await project_repo.get_by_user(db, current_user.id)
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await project_repo.create(db, obj_in={
        "user_id": current_user.id,
        "name": project_in.name,
        "type": project_in.type,
        "description": project_in.description,
        "settings_json": project_in.settings,
        "topic_details_json": project_in.topic_details,
    })
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await project_repo.get_with_details(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    files_summary = [FileSummary.model_validate(f) for f in project.files]
    
    return ProjectDetailResponse(
        id=project.id,
        user_id=project.user_id,
        workspace_id=project.workspace_id,
        name=project.name,
        type=project.type,
        description=project.description,
        settings_json=project.settings_json,
        topic_details_json=project.topic_details_json,
        created_at=project.created_at,
        updated_at=project.updated_at,
        files=files_summary,
        reports_count=len(project.reports),
        sources_count=len(project.sources),
    )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project_in: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    update_data = {}
    if project_in.name is not None:
        update_data["name"] = project_in.name
    if project_in.description is not None:
        update_data["description"] = project_in.description
    if project_in.settings is not None:
        update_data["settings_json"] = project_in.settings
    if project_in.topic_details is not None:
        update_data["topic_details_json"] = project_in.topic_details

    updated_project = await project_repo.update(db, db_obj=project, obj_in=update_data)
    return ProjectResponse.model_validate(updated_project)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    await project_repo.remove(db, id=project_id)
    return None
