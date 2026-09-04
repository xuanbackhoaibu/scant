from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class ImageAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    project_id: str
    report_id: Optional[str] = None
    file_name: str
    mime_type: str
    file_size: int
    width: Optional[int] = None
    height: Optional[int] = None
    source_type: str
    original_url: Optional[str] = None
    source_domain: Optional[str] = None
    source_title: Optional[str] = None
    source_page_url: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    content_url: str
    created_at: datetime


class WebImageSearchRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=200)
    license_mode: str = "all"
    max_results: int = Field(default=12, ge=1, le=24)


class WebImageResult(BaseModel):
    id: str
    thumbnailUrl: str
    imageUrl: str
    title: str
    sourcePageUrl: Optional[str] = None
    sourceDomain: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    license: Optional[str] = None
    attribution: Optional[str] = None


class WebImageSearchResponse(BaseModel):
    provider: str
    results: List[WebImageResult] = Field(default_factory=list)


class ImportWebImageRequest(BaseModel):
    project_id: str
    report_id: Optional[str] = None
    image_url: HttpUrl
    source_page_url: Optional[HttpUrl] = None
    title: Optional[str] = None
    license: Optional[str] = None
    attribution: Optional[str] = None


class ImageQuerySuggestionRequest(BaseModel):
    section_title: str = ""
    section_text: str = ""
    report_title: str = ""
    max_queries: int = Field(default=6, ge=1, le=10)
