from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.report import OutlineItem


class OutlineGenerationRequest(BaseModel):
    project_id: str
    topic_name: str
    topic_description: Optional[str] = None
    subject: Optional[str] = None
    major: Optional[str] = None
    requirements_text: Optional[str] = None
    target_chapters_count: int = 5
    language: str = "vi"


class OutlineGenerationResponse(BaseModel):
    project_understanding: str
    objectives: List[str]
    scope: str
    suggested_methodology: str
    outline: List[OutlineItem]


class SectionDraftRequest(BaseModel):
    project_id: str
    report_id: str
    section_id: str
    instruction: Optional[str] = None  # e.g. "Viết sâu về cơ chế Middleware trong ASP.NET Core"
    tone: str = "academic"  # academic, professional, technical
    include_citations: bool = True
    max_tokens: int = 2500


class SectionEditRequest(BaseModel):
    project_id: str
    report_id: str
    section_id: str
    selected_text: str
    action: str  # rewrite, expand, shorten, academic, explain_more, add_example, fix_grammar
    custom_instruction: Optional[str] = None


class AICompletionResponse(BaseModel):
    text: str
    html_content: Optional[str] = None
    tiptap_json: Optional[Dict[str, Any]] = None
    citations_used: List[Dict[str, Any]] = Field(default_factory=list)
    claims_verified: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0


class ReportQualityCheckResponse(BaseModel):
    overall_score: int  # 0 - 100
    is_ready_to_export: bool
    summary: str
    checks: List[Dict[str, Any]]  # name, status (pass, warning, fail), message, suggestion
    missing_citations: List[str] = Field(default_factory=list)
    missing_figures: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
