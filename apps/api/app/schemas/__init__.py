from app.schemas.auth import UserRegister, UserLogin, UserResponse, TokenResponse
from app.schemas.project import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectDetailResponse, TopicDetails
from app.schemas.template import TemplateCreate, TemplateResponse, TemplateVersionResponse
from app.schemas.report import (
    ReportCreate, ReportUpdate, ReportResponse, ReportDetailResponse,
    ReportSectionCreate, ReportSectionUpdate, ReportSectionResponse, OutlineItem
)
from app.schemas.source import SourceCreate, SourceResponse, CitationResponse, ClaimSourceResponse
from app.schemas.ai import (
    OutlineGenerationRequest, OutlineGenerationResponse,
    SectionDraftRequest, SectionEditRequest, AICompletionResponse,
    ReportQualityCheckResponse
)
from app.schemas.export import ExportRequest, ExportResponse

__all__ = [
    "UserRegister", "UserLogin", "UserResponse", "TokenResponse",
    "ProjectCreate", "ProjectUpdate", "ProjectResponse", "ProjectDetailResponse", "TopicDetails",
    "TemplateCreate", "TemplateResponse", "TemplateVersionResponse",
    "ReportCreate", "ReportUpdate", "ReportResponse", "ReportDetailResponse",
    "ReportSectionCreate", "ReportSectionUpdate", "ReportSectionResponse", "OutlineItem",
    "SourceCreate", "SourceResponse", "CitationResponse", "ClaimSourceResponse",
    "OutlineGenerationRequest", "OutlineGenerationResponse",
    "SectionDraftRequest", "SectionEditRequest", "AICompletionResponse", "ReportQualityCheckResponse",
    "ExportRequest", "ExportResponse"
]
