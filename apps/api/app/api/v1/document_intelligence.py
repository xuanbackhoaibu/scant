from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from app.models.entities import User
from app.api.deps import get_current_user
from app.services.documents.intelligence.document_intelligence_engine import document_intelligence_engine
from app.services.documents.intelligence.types import DocumentIntelligenceTree

router = APIRouter(prefix="/document-intelligence", tags=["document-intelligence"])


class VisualQueryRequest(BaseModel):
    document_tree: Dict[str, Any]
    question: str


@router.post("/analyze")
async def analyze_document_multimodal(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    """Parses document into multimodal Layout Block Tree (PDF, DOCX, Images, Scans, Charts)."""
    file_bytes = await file.read()
    filename = file.filename or "uploaded_doc"
    tree = await document_intelligence_engine.analyze_document(file_bytes=file_bytes, filename=filename)
    return tree.model_dump()


@router.post("/query-visual")
async def query_document_visual(
    req: VisualQueryRequest,
    current_user: User = Depends(get_current_user),
):
    """Allows AI reasoning over extracted charts, diagrams, tables, and visual blocks."""
    tree = DocumentIntelligenceTree.model_validate(req.document_tree)
    return await document_intelligence_engine.query_visual_content(tree=tree, question=req.question)
