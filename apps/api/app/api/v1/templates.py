import hashlib
from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Template, TemplateVersion
from app.repositories.template_repo import template_repo, template_version_repo
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateVersionResponse
from app.api.deps import get_current_user, get_current_user_optional
from app.services.templates.docx_template_analyzer import template_analyzer
from app.services.templates.template_reverse_engineering_service import template_reverse_engineer

router = APIRouter(prefix="/templates", tags=["templates"])


@router.get("")
async def list_templates(
    scope: str = "public",  # my, workspace, public, all
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    from app.services.templates.template_library_service import template_library_service
    user_id = current_user.id if current_user else None
    return await template_library_service.list_templates(
        db=db,
        current_user_id=user_id,
        scope=scope,
        category=category,
        search=search,
    )


@router.post("/{template_id}/duplicate")
async def duplicate_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.templates.template_library_service import template_library_service
    return await template_library_service.duplicate_template(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        user_name=current_user.name
    )


@router.post("/{template_id}/publish")
async def publish_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.templates.template_library_service import template_library_service
    return await template_library_service.toggle_publish(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        publish=True
    )


@router.post("/{template_id}/unpublish")
async def unpublish_template(
    template_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    from app.services.templates.template_library_service import template_library_service
    return await template_library_service.toggle_publish(
        db=db,
        template_id=template_id,
        user_id=current_user.id,
        publish=False
    )


@router.post("/{template_id}/use")
async def use_template(
    template_id: str,
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    from app.services.templates.template_library_service import template_library_service
    await template_library_service.record_usage(db, template_id)
    return {"status": "success", "template_id": template_id}



@router.post("/reverse-engineer")
async def reverse_engineer_template(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """Decomposes an uploaded DOCX or PDF template into dynamic schema, fields, and styles."""
    filename = file.filename or "template.docx"
    ext = Path(filename).suffix.lower()
    if ext not in [".docx", ".doc", ".pdf"]:
        raise HTTPException(status_code=400, detail="Only .docx and .pdf files are supported")

    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()
    stored_filename = f"tpl_rev_{file_hash[:12]}_{filename}"
    file_path = settings.TEMPLATE_DIR / stored_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    if ext in [".docx", ".doc"]:
        schema = await template_reverse_engineer.reverse_engineer_docx(str(file_path))
    else:
        schema = await template_reverse_engineer.reverse_engineer_pdf(str(file_path))

    schema["stored_file_path"] = str(file_path)
    schema["original_filename"] = filename
    return schema


@router.post("/upload-docx", response_model=TemplateResponse)
async def upload_docx_template(
    name: str = Form(...),
    category: str = Form("business"),
    organization: str = Form(None),
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    filename = file.filename or "template.docx"
    ext = Path(filename).suffix.lower()
    if ext not in [".docx", ".doc"]:
        raise HTTPException(status_code=400, detail="Only .docx template files are supported")

    contents = await file.read()
    file_hash = hashlib.sha256(contents).hexdigest()
    stored_filename = f"tpl_{file_hash[:12]}_{filename}"
    file_path = settings.TEMPLATE_DIR / stored_filename

    with open(file_path, "wb") as f:
        f.write(contents)

    # Reverse engineer schema
    schema = await template_reverse_engineer.reverse_engineer_docx(str(file_path))

    template = await template_repo.create(db, obj_in={
        "user_id": current_user.id,
        "name": name,
        "category": category,
        "description": f"Mẫu văn bản trích xuất từ file {filename}",
        "is_system": False,
        "is_public": False,
        "organization": organization,
        "schema_json": schema,
    })

    version = await template_version_repo.create(db, obj_in={
        "template_id": template.id,
        "version_number": 1,
        "styles_json": schema.get("styles", {}),
        "placeholders_json": {
            "explicit": schema.get("explicit_placeholders", []),
            "detected": schema.get("fields", []),
        },
        "schema_json": schema,
        "file_path": str(file_path),
    })

    return TemplateResponse(
        id=template.id,
        user_id=template.user_id,
        name=template.name,
        category=template.category,
        description=template.description,
        is_system=template.is_system,
        is_public=template.is_public,
        organization=template.organization,
        created_at=template.created_at,
        updated_at=template.updated_at,
        latest_version=TemplateVersionResponse.model_validate(version)
    )
