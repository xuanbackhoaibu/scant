from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SourceCreate(BaseModel):
    project_id: str
    title: str
    url: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    source_type: str = "website"  # official_doc, paper, book, website, university, standard
    reliability_score: float = 0.8
    summary: Optional[str] = None
    content_extracted: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    url: Optional[str] = None
    authors: Optional[str] = None
    publisher: Optional[str] = None
    published_date: Optional[str] = None
    accessed_date: datetime
    source_type: str
    reliability_score: float
    summary: Optional[str] = None
    content_extracted: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CitationCreate(BaseModel):
    report_section_id: str
    source_id: str
    citation_style: str = "IEEE"
    citation_key: str
    locator: Optional[str] = None
    evidence_text: Optional[str] = None


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_section_id: str
    source_id: str
    citation_style: str
    citation_key: str
    locator: Optional[str] = None
    evidence_text: Optional[str] = None
    created_at: datetime
    source: Optional[SourceResponse] = None


class ClaimSourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_section_id: str
    source_id: str
    citation_id: Optional[str] = None
    claim_text: str
    evidence_text: str
    confidence_score: float
    verification_status: str
    created_at: datetime
    source: Optional[SourceResponse] = None
