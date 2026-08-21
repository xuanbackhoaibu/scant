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


@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    current_user: User = Depends(get_current_user_optional),
    db: AsyncSession = Depends(get_db),
):
    user_id = current_user.id if current_user else None
    templates = await template_repo.get_available(db, user_id=user_id)
    
    responses = []
    for t in templates:
        latest_ver = t.versions[0] if t.versions else None
        res = TemplateResponse(
            id=t.id,
            user_id=t.user_id,
            name=t.name,
            category=t.category,
            description=t.description,
            is_system=t.is_system,
            is_public=t.is_public,
            organization=t.organization,
            created_at=t.created_at,
            updated_at=t.updated_at,
            latest_version=TemplateVersionResponse.model_validate(latest_ver) if latest_ver else None
        )
        responses.append(res)

    return responses


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
