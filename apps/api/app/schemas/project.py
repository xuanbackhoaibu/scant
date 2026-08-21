from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicDetails(BaseModel):
    topic_name: Optional[str] = None
    subject: Optional[str] = None
    major: Optional[str] = None
    university: Optional[str] = None
    instructor: Optional[str] = None
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    class_name: Optional[str] = None
    academic_year: Optional[str] = None
    description: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    type: str = Field(default="academic")  # academic, data, template_based, auto
    description: Optional[str] = None
    settings: Dict[str, Any] = Field(default_factory=dict)
    topic_details: Dict[str, Any] = Field(default_factory=dict)


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
    topic_details: Optional[Dict[str, Any]] = None


class ProjectResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: str
    workspace_id: Optional[str] = None
    name: str
    type: str
    description: Optional[str] = None
    settings_json: Dict[str, Any] = Field(default_factory=dict)
    topic_details_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime


class FileSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    original_name: str
    file_type: str
    file_size: int
    is_parsed: bool
    created_at: datetime


class ProjectDetailResponse(ProjectResponse):
    files: List[FileSummary] = Field(default_factory=list)
    reports_count: int = 0
    sources_count: int = 0
