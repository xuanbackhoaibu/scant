from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class OutlineItem(BaseModel):
    id: Optional[str] = None
    title: str
    level: int = 1
    position: int = 0
    section_number: Optional[str] = None
    description: Optional[str] = None
    children: List["OutlineItem"] = Field(default_factory=list)


class ReportSectionBase(BaseModel):
    title: str
    position: int = 0
    level: int = 1
    section_number: Optional[str] = None
    parent_id: Optional[str] = None


class ReportSectionCreate(ReportSectionBase):
    content_json: Optional[Dict[str, Any]] = None
    plain_text: Optional[str] = ""


class ReportSectionUpdate(BaseModel):
    title: Optional[str] = None
    position: Optional[int] = None
    level: Optional[int] = None
    section_number: Optional[str] = None
    status: Optional[str] = None
    content_json: Optional[Dict[str, Any]] = None
    plain_text: Optional[str] = None
    word_count: Optional[int] = None
    structured_summary_json: Optional[Dict[str, Any]] = None


class ReportSectionResponse(ReportSectionBase):
    model_config = ConfigDict(from_attributes=True)

    id: str
    report_id: str
    status: str
    content_json: Dict[str, Any] = Field(default_factory=dict)
    plain_text: str = ""
    word_count: int = 0
    structured_summary_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ReportCreate(BaseModel):
    project_id: str
    template_version_id: Optional[str] = None
    title: str = Field(..., min_length=2, max_length=255)
    report_type: str = Field(default="academic")
    document_settings: Optional[Dict[str, Any]] = None
    outline: Optional[List[OutlineItem]] = None


class ReportUpdate(BaseModel):
    title: Optional[str] = None
    status: Optional[str] = None
    revision: Optional[int] = None
    document_settings_json: Optional[Dict[str, Any]] = None


class ReportResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    template_version_id: Optional[str] = None
    title: str
    report_type: str
    status: str
    revision: int
    document_settings_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ReportDetailResponse(ReportResponse):
    sections: List[ReportSectionResponse] = Field(default_factory=list)
    total_words: int = 0
    sources_count: int = 0
    citations_count: int = 0
