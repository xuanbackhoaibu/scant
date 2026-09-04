from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class CustomFieldSchema(BaseModel):
    key: str
    label: str
    type: str = "text"
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None
    value: Any = None
    unit: Optional[str] = None


class MetadataSchema(BaseModel):
    document_type: Optional[str] = "business_report"
    document_profile: Optional[str] = "business"
    audience: Optional[str] = "Executive Board & Stakeholders"
    language: Optional[str] = "vi"
    custom_fields: List[CustomFieldSchema] = Field(default_factory=list)


# Backward-compatibility legacy DTO
class TopicDetails(BaseModel):
    topic_name: Optional[str] = None
    company_name: Optional[str] = None
    organization: Optional[str] = None
    department: Optional[str] = None
    subject: Optional[str] = None
    major: Optional[str] = None
    university: Optional[str] = None
    instructor: Optional[str] = None
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    class_name: Optional[str] = None
    academic_year: Optional[str] = None
    lead_author: Optional[str] = None


class ProjectBase(BaseModel):
    name: str
    type: str = "business_report"  # business_report, data_analysis, research, technical, proposal, financial, custom
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[MetadataSchema] = None
    topic_details: Optional[Dict[str, Any]] = None  # Legacy support


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    metadata: Optional[MetadataSchema] = None
    topic_details: Optional[Dict[str, Any]] = None


class FileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_name: str
    file_type: str
    file_size: int
    is_parsed: bool = False
    file_hash: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    workspace_id: Optional[str] = None
    name: str
    type: str
    description: Optional[str] = None
    settings_json: Dict[str, Any]
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    topic_details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class ProjectDetailResponse(ProjectResponse):
    files: List[FileSummary] = Field(default_factory=list)
    reports: List[Any] = Field(default_factory=list)
    sources: List[Any] = Field(default_factory=list)
