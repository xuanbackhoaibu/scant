from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class SourceCreate(BaseModel):
    project_id: str
    title: str
    subtitle: Optional[str] = None
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    authors: Optional[str] = None
    organization: Optional[str] = None
    publisher: Optional[str] = None
    publication_name: Optional[str] = None
    publication_year: Optional[int] = None
    published_date: Optional[str] = None
    doi: Optional[str] = None
    source_type: str = "WEB_ARTICLE"
    provider: Optional[str] = "manual"
    reliability_score: float = 0.8
    summary: Optional[str] = None
    content_extracted: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class SourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    title: str
    subtitle: Optional[str] = None
    url: Optional[str] = None
    canonical_url: Optional[str] = None
    authors: Optional[str] = None
    organization: Optional[str] = None
    publisher: Optional[str] = None
    publication_name: Optional[str] = None
    publication_year: Optional[int] = None
    published_date: Optional[str] = None
    doi: Optional[str] = None
    accessed_date: datetime
    source_type: str
    provider: Optional[str] = None
    language: str = "vi"
    abstract: Optional[str] = None
    reliability_score: float = 0.8
    summary: Optional[str] = None
    content_extracted: Optional[str] = None
    access_status: str = "open"
    verification_status: str = "UNVERIFIED"
    verification_score: int = 0
    verification_details_json: Dict[str, Any] = Field(default_factory=dict)
    domain_trust: str = "UNKNOWN"
    file_id: Optional[str] = None
    dataset_id: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: Optional[datetime] = None
    evidence_count: int = 0
    citation_count: int = 0


class EvidenceCreate(BaseModel):
    evidence_type: str = "WEB_TEXT"  # WEB_TEXT, PDF_TEXT, DOCX_TEXT, EXCEL_RANGE, MANUAL_SELECTION
    quote: str
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    paragraph_index: Optional[int] = None
    sheet_name: Optional[str] = None
    cell_range: Optional[str] = None
    operation: Optional[str] = "COUNT"
    source_url: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class EvidenceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    source_id: str
    project_id: str
    evidence_type: str
    quote: str
    normalized_text: Optional[str] = None
    page_number: Optional[int] = None
    section_title: Optional[str] = None
    paragraph_index: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    sheet_name: Optional[str] = None
    cell_range: Optional[str] = None
    operation: Optional[str] = None
    calculation_result: Optional[str] = None
    source_url: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class CitationCreate(BaseModel):
    report_id: Optional[str] = None
    report_section_id: str
    source_id: str
    evidence_id: Optional[str] = None
    claim_id: Optional[str] = None
    citation_style: str = "IEEE"
    locator: Optional[str] = None
    evidence_text: Optional[str] = None


class CitationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: Optional[str] = None
    report_section_id: str
    source_id: str
    evidence_id: Optional[str] = None
    claim_id: Optional[str] = None
    citation_number: int = 1
    citation_style: str = "IEEE"
    citation_key: str
    locator: Optional[str] = None
    evidence_text: Optional[str] = None
    verification_status: str = "VERIFIED"
    support_level: str = "STRONG"
    created_at: datetime
    source: Optional[SourceResponse] = None
    evidence: Optional[EvidenceResponse] = None


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


class SourceSearchRequest(BaseModel):
    query: str
    providers: Optional[List[str]] = None
    sort_by: Optional[str] = "RELEVANCE"
    limit: Optional[int] = 10


class SourceImportRequest(BaseModel):
    sources: List[Dict[str, Any]]


class SourceUrlRequest(BaseModel):
    url: str
    title: Optional[str] = None
    notes: Optional[str] = None


class CitationSupportVerifyRequest(BaseModel):
    claim_text: str
    evidence_text: str
