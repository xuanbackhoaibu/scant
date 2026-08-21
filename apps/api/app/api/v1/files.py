import hashlib
import os
import shutil
from pathlib import Path
from typing import List
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.core.database import get_db
from app.models.entities import User, Project, UploadedFile, Document
from app.repositories.project_repo import project_repo, file_repo, document_repo
from app.schemas.project import FileSummary
from app.api.deps import get_current_user
from app.services.documents.pdf_parser import pdf_parser
from app.services.documents.docx_parser import docx_parser
from app.services.documents.excel_parser import excel_parser

router = APIRouter(prefix="/files", tags=["files"])

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc", ".xlsx", ".xls", ".csv", ".txt", ".md", ".zip", ".png", ".jpg"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


@router.post("/upload", response_model=FileSummary)
async def upload_file(
    project_id: str = Form(...),
    document_type: str = Form("reference"),  # requirement, rubric, reference, source_code
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    filename = file.filename or "uploaded_file"
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file extension: {ext}. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Read contents and calculate SHA256
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File exceeds 50MB limit")

    file_hash = hashlib.sha256(contents).hexdigest()

    # Save to disk
    stored_filename = f"{project_id}_{file_hash[:12]}_{filename}"
    file_path = settings.UPLOAD_DIR / stored_filename
    with open(file_path, "wb") as f:
        f.write(contents)

    # Detect file type category
    file_type_cat = "pdf" if ext == ".pdf" else "docx" if ext in [".docx", ".doc"] else "excel" if ext in [".xlsx", ".xls", ".csv"] else "zip" if ext == ".zip" else "text"

    # Create UploadedFile record
    uploaded_file = await file_repo.create(db, obj_in={
        "project_id": project_id,
        "filename": stored_filename,
        "original_name": filename,
        "file_type": file_type_cat,
        "mime_type": file.content_type or "application/octet-stream",
        "file_size": len(contents),
        "file_path": str(file_path),
        "file_hash": file_hash,
        "is_parsed": False,
        "metadata_json": {}
    })

    # Auto parse text content into Knowledge Base Document
    try:
        content_text = ""
        metadata = {}
        if file_type_cat == "pdf":
            parsed = pdf_parser.extract_text_and_metadata(str(file_path))
            content_text = parsed["full_text"]
            metadata = parsed["metadata"]
        elif file_type_cat == "docx":
            parsed = docx_parser.extract_document(str(file_path))
            content_text = parsed["full_text"]
            metadata = {"headings_count": len(parsed["headings"]), "tables_count": parsed["tables_count"]}
        elif file_type_cat == "text":
            content_text = contents.decode("utf-8", errors="ignore")

        if content_text:
            await document_repo.create(db, obj_in={
                "project_id": project_id,
                "file_id": uploaded_file.id,
                "title": filename,
                "content_text": content_text,
                "content_json": {},
                "document_type": document_type,
                "token_count": len(content_text) // 4,
            })
            await file_repo.update(db, db_obj=uploaded_file, obj_in={"is_parsed": True, "metadata_json": metadata})
    except Exception as e:
        # File uploaded, parsing error handled gracefully
        pass

    return FileSummary.model_validate(uploaded_file)


@router.get("/project/{project_id}", response_model=List[FileSummary])
async def list_project_files(
    project_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    project = await project_repo.get(db, project_id)
    if not project or project.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Project not found")

    files = await file_repo.get_multi(db, project_id=project_id)
    return [FileSummary.model_validate(f) for f in files]
