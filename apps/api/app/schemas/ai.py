from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.report import OutlineItem


class AnalyzeIntentRequest(BaseModel):
    user_prompt: str
    selected_type: Optional[str] = None  # optional initial category


class AnalyzeIntentResponse(BaseModel):
    suggested_title: str
    suggested_type: str  # business_report, data_analysis, research, technical, proposal, financial, market_research, custom
    objective: str
    target_audience: str
    key_themes: List[str] = Field(default_factory=list)
    suggested_custom_fields: List[Dict[str, Any]] = Field(default_factory=list)
    data_requirements: Optional[str] = None
    research_requirements: Optional[str] = None


class OutlineGenerationRequest(BaseModel):
    project_id: str
    topic_name: str
    project_type: str = "business_report"
    topic_description: Optional[str] = None
    audience: Optional[str] = "Executive Board & Stakeholders"
    subject: Optional[str] = None
    major: Optional[str] = None
    requirements_text: Optional[str] = None
    target_chapters_count: int = 5
    custom_metadata: Optional[Dict[str, Any]] = None


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
    instruction: Optional[str] = None
    tone: str = "professional"  # professional, academic, executive, technical, concise


class SectionEditRequest(BaseModel):
    project_id: str
    selected_text: str
    action: str  # rewrite, professional, expand, shorten, fix_grammar, convert_table, translate
    custom_instruction: Optional[str] = None


class CopilotMessageRequest(BaseModel):
    project_id: str
    report_id: Optional[str] = None
    section_id: Optional[str] = None
    message: str
    selected_text: Optional[str] = None
    context_data: Optional[Dict[str, Any]] = None


class CopilotMessageResponse(BaseModel):
    reply: str
    action_type: Optional[str] = None  # text_insert, outline_modify, data_visualize, fact_check
    payload: Optional[Dict[str, Any]] = None


class AICompletionResponse(BaseModel):
    text: str
    tiptap_json: Optional[Dict[str, Any]] = None
    claims_verified: List[Dict[str, Any]] = Field(default_factory=list)
    tokens_used: int = 0


class QualityCheckItem(BaseModel):
    name: str
    status: str  # pass, warning, fail
    message: str
    suggestion: Optional[str] = None


class ReportQualityCheckResponse(BaseModel):
    overall_score: int
    is_ready_to_export: bool
    summary: str
    checks: List[QualityCheckItem]
    missing_sections: List[str] = Field(default_factory=list)
    missing_figures: List[str] = Field(default_factory=list)
    unsupported_claims: List[str] = Field(default_factory=list)
