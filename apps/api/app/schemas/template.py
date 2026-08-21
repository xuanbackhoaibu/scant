from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class TemplateVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    template_id: str
    version_number: int
    styles_json: Dict[str, Any] = Field(default_factory=dict)
    placeholders_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime


class TemplateCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    category: str = Field(default="academic")
    description: Optional[str] = None
    organization: Optional[str] = None
    styles: Optional[Dict[str, Any]] = None
    placeholders: Optional[Dict[str, Any]] = None


class TemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    user_id: Optional[str] = None
    name: str
    category: str
    description: Optional[str] = None
    is_system: bool
    is_public: bool
    organization: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    latest_version: Optional[TemplateVersionResponse] = None
