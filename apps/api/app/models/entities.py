import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Text, Integer, Float, Boolean, DateTime, ForeignKey, JSON
)
from sqlalchemy.orm import relationship, backref
from app.core.database import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


def get_utc_now() -> datetime:
    return datetime.now(timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(255), nullable=False)
    avatar = Column(String(500), nullable=True)
    plan = Column(String(50), default="pro", nullable=False)  # free, pro, enterprise
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    projects = relationship("Project", back_populates="user", cascade="all, delete-orphan")
    workspaces = relationship("Workspace", back_populates="user", cascade="all, delete-orphan")
    templates = relationship("Template", back_populates="user", cascade="all, delete-orphan")


class Workspace(Base):
    __tablename__ = "workspaces"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    slug = Column(String(255), nullable=False)
    settings_json = Column(JSON, default=dict, nullable=False)
    brand_kit_json = Column(JSON, default=dict, nullable=False)  # Logo, colors, fonts, default header/footer
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="workspaces")
    projects = relationship("Project", back_populates="workspace", cascade="all, delete-orphan")


class Project(Base):
    __tablename__ = "projects"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    workspace_id = Column(String(36), ForeignKey("workspaces.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    type = Column(String(50), default="business_report", nullable=False)  # business_report, data_analysis, research, technical, proposal, financial, custom
    description = Column(Text, nullable=True)
    settings_json = Column(JSON, default=dict, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)  # Universal custom fields: [{key, label, type, value, required}]
    topic_details_json = Column(JSON, default=dict, nullable=False)  # Backward-compatible legacy alias
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user = relationship("User", back_populates="projects")
    workspace = relationship("Workspace", back_populates="projects")
    files = relationship("UploadedFile", back_populates="project", cascade="all, delete-orphan")
    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    reports = relationship("Report", back_populates="project", cascade="all, delete-orphan")
    sources = relationship("Source", back_populates="project", cascade="all, delete-orphan")
    research_jobs = relationship("ResearchJob", back_populates="project", cascade="all, delete-orphan")
    datasets = relationship("Dataset", back_populates="project", cascade="all, delete-orphan")


class UploadedFile(Base):
    __tablename__ = "uploaded_files"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_name = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)  # pdf, docx, xlsx, zip, image, text
    mime_type = Column(String(100), nullable=False)
    file_size = Column(Integer, nullable=False)
    file_path = Column(String(500), nullable=False)
    file_hash = Column(String(64), nullable=False)  # SHA256
    is_parsed = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="files")
    documents = relationship("Document", back_populates="uploaded_file", cascade="all, delete-orphan")


class Document(Base):
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    file_id = Column(String(36), ForeignKey("uploaded_files.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    content_text = Column(Text, nullable=False)
    content_json = Column(JSON, default=dict, nullable=False)
    document_type = Column(String(50), default="reference", nullable=False)  # requirement, rubric, reference, source_code, note
    token_count = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="documents")
    uploaded_file = relationship("UploadedFile", back_populates="documents")


class Template(Base):
    __tablename__ = "templates"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), default="business", nullable=False)  # business, financial, technical, research, data, proposal, marketing, operations, custom
    description = Column(Text, nullable=True)
    thumbnail_url = Column(String(1024), nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    is_public = Column(Boolean, default=False, nullable=False)
    visibility = Column(String(50), default="public", nullable=False)  # my, workspace, public
    author_name = Column(String(255), default="AI Studio Official", nullable=False)
    usage_count = Column(Integer, default=0, nullable=False)
    rating = Column(Float, default=5.0, nullable=False)
    tags_json = Column(JSON, default=list, nullable=False)
    organization = Column(String(255), nullable=True)  # Company or Organization Name
    schema_json = Column(JSON, default=dict, nullable=False)  # Reverse-engineered document schema & dynamic fields
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    user = relationship("User", back_populates="templates")
    versions = relationship("TemplateVersion", back_populates="template", cascade="all, delete-orphan")


class TemplateVersion(Base):
    __tablename__ = "template_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    template_id = Column(String(36), ForeignKey("templates.id", ondelete="CASCADE"), nullable=False)
    version_number = Column(Integer, default=1, nullable=False)
    file_path = Column(String(1024), nullable=True)
    styles_json = Column(JSON, default=dict, nullable=False)  # margins, font, spacing, colors
    placeholders_json = Column(JSON, default=dict, nullable=False)  # detected placeholders
    schema_json = Column(JSON, default=dict, nullable=False)  # reverse engineered structure
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    template = relationship("Template", back_populates="versions")
    reports = relationship("Report", back_populates="template_version")


class Report(Base):
    __tablename__ = "reports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    template_version_id = Column(String(36), ForeignKey("template_versions.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False)
    report_type = Column(String(50), default="business_report", nullable=False)
    quality_profile = Column(String(50), default="business", nullable=False)  # business, technical, research, financial, data_analysis, custom
    status = Column(String(50), default="draft", nullable=False)
    revision = Column(Integer, default=1, nullable=False)
    document_settings_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="reports")
    template_version = relationship("TemplateVersion", back_populates="reports")
    sections = relationship("ReportSection", back_populates="report", cascade="all, delete-orphan", order_by="ReportSection.position")
    versions = relationship("ReportVersion", back_populates="report", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="report", cascade="all, delete-orphan")
    exports = relationship("ExportRecord", back_populates="report", cascade="all, delete-orphan")


class ReportSection(Base):
    __tablename__ = "report_sections"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("report_sections.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(255), nullable=False)
    position = Column(Integer, default=0, nullable=False)
    level = Column(Integer, default=1, nullable=False)  # 1 for Chapter, 2 for Subchapter, 3 for Subsection
    section_number = Column(String(50), nullable=True)  # e.g. "1.1", "2.3.1"
    status = Column(String(50), default="empty", nullable=False)  # empty, planned, researching, drafting, draft, review_needed, approved
    content_json = Column(JSON, default=dict, nullable=False)  # Tiptap ProseMirror document JSON
    plain_text = Column(Text, default="", nullable=False)
    word_count = Column(Integer, default=0, nullable=False)
    structured_summary_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    report = relationship("Report", back_populates="sections")
    parent = relationship("ReportSection", remote_side=[id], backref="children")
    citations = relationship("Citation", back_populates="section", cascade="all, delete-orphan")
    claim_sources = relationship("ClaimSource", back_populates="section", cascade="all, delete-orphan")


class ReportVersion(Base):
    __tablename__ = "report_versions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    revision = Column(Integer, nullable=False)
    snapshot_json = Column(JSON, nullable=False)
    change_description = Column(String(255), nullable=True)
    created_by = Column(String(36), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    report = relationship("Report", back_populates="versions")


class Source(Base):
    __tablename__ = "sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=True)
    authors = Column(String(500), nullable=True)
    publisher = Column(String(255), nullable=True)
    published_date = Column(String(50), nullable=True)
    accessed_date = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    source_type = Column(String(50), default="website", nullable=False)  # official_doc, paper, book, website, university, standard, uploaded
    reliability_score = Column(Float, default=0.8, nullable=False)  # 0.0 to 1.0
    summary = Column(Text, nullable=True)
    content_extracted = Column(Text, nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    content_hash = Column(String(64), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="sources")
    citations = relationship("Citation", back_populates="source", cascade="all, delete-orphan")
    claim_sources = relationship("ClaimSource", back_populates="source", cascade="all, delete-orphan")


class Citation(Base):
    __tablename__ = "citations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_section_id = Column(String(36), ForeignKey("report_sections.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    citation_style = Column(String(50), default="IEEE", nullable=False)  # IEEE, APA, Harvard, MLA, Vancouver
    citation_key = Column(String(50), nullable=False)  # e.g. "[1]", "(Smith, 2024)"
    locator = Column(String(100), nullable=True)  # e.g. "p. 45" or "Section 3"
    evidence_text = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    section = relationship("ReportSection", back_populates="citations")
    source = relationship("Source", back_populates="citations")


class ClaimSource(Base):
    """Anti-Hallucination Claim to Evidence verification mapping."""
    __tablename__ = "claim_sources"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_section_id = Column(String(36), ForeignKey("report_sections.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    citation_id = Column(String(36), ForeignKey("citations.id", ondelete="SET NULL"), nullable=True)
    claim_text = Column(Text, nullable=False)
    evidence_text = Column(Text, nullable=False)
    confidence_score = Column(Float, default=1.0, nullable=False)
    verification_status = Column(String(50), default="verified", nullable=False)  # verified, needs_review, unverified
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    section = relationship("ReportSection", back_populates="claim_sources")
    source = relationship("Source", back_populates="claim_sources")


class ResearchJob(Base):
    __tablename__ = "research_jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    query = Column(String(500), nullable=False)
    mode = Column(String(50), default="standard", nullable=False)  # quick (5 sources), standard (10-20), deep (30+)
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    progress_percent = Column(Integer, default=0, nullable=False)
    status_message = Column(String(255), default="Initializing...", nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="research_jobs")
    results = relationship("ResearchResult", back_populates="job", cascade="all, delete-orphan")


class ResearchResult(Base):
    __tablename__ = "research_results"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    job_id = Column(String(36), ForeignKey("research_jobs.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(String(36), ForeignKey("sources.id", ondelete="CASCADE"), nullable=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False)
    snippet = Column(Text, nullable=True)
    rank_score = Column(Float, default=0.0, nullable=False)
    relevance_score = Column(Float, default=0.0, nullable=False)
    is_selected = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    job = relationship("ResearchJob", back_populates="results")


class AIGeneration(Base):
    __tablename__ = "ai_generations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    report_section_id = Column(String(36), ForeignKey("report_sections.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(50), nullable=False)  # gemini, openai, claude, ollama
    model = Column(String(100), nullable=False)
    purpose = Column(String(100), nullable=False)  # outline, section_draft, rewrite, summarize, citation_check
    prompt_summary = Column(Text, nullable=True)
    input_tokens = Column(Integer, default=0, nullable=False)
    output_tokens = Column(Integer, default=0, nullable=False)
    latency_ms = Column(Integer, default=0, nullable=False)
    cost_estimate = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class ProjectMember(Base):
    __tablename__ = "project_members"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    invited_email = Column(String(255), nullable=True)
    role = Column(String(50), default="editor", nullable=False)  # owner, editor, commenter, viewer
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    project = relationship("Project", backref="members")
    user = relationship("User")


class Comment(Base):
    __tablename__ = "comments"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    report_section_id = Column(String(36), ForeignKey("report_sections.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    parent_id = Column(String(36), ForeignKey("comments.id", ondelete="CASCADE"), nullable=True)
    selected_text = Column(Text, nullable=True)
    comment_text = Column(Text, nullable=False)
    status = Column(String(50), default="open", nullable=False)  # open, resolved
    mentions_json = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    report = relationship("Report", back_populates="comments")
    replies = relationship("Comment", backref=backref("parent", remote_side=[id]), cascade="all, delete-orphan")
    user = relationship("User")


class ExportRecord(Base):
    __tablename__ = "exports"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    export_format = Column(String(20), nullable=False)  # docx, pdf, html, md
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, default=0, nullable=False)
    settings_json = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="completed", nullable=False)  # processing, completed, failed
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    report = relationship("Report", back_populates="exports")


class Job(Base):
    __tablename__ = "jobs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), nullable=True)
    job_type = Column(String(50), default="generation", nullable=False)  # file_parsing, ocr, research, generation, export
    status = Column(String(50), default="pending", nullable=False)  # pending, running, completed, failed, cancelled
    status_message = Column(String(500), nullable=True)
    progress_percent = Column(Integer, default=0, nullable=False)
    payload_json = Column(JSON, default=dict, nullable=False)
    result_json = Column(JSON, default=dict, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), nullable=True)
    action = Column(String(100), nullable=False)
    resource_type = Column(String(50), nullable=False)
    resource_id = Column(String(36), nullable=True)
    details_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)


class Dataset(Base):
    __tablename__ = "datasets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    row_count = Column(Integer, default=0, nullable=False)
    column_count = Column(Integer, default=0, nullable=False)
    raw_data_path = Column(String(500), nullable=True)
    metadata_json = Column(JSON, default=dict, nullable=False)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    project = relationship("Project", back_populates="datasets")
    columns = relationship("DatasetColumn", back_populates="dataset", cascade="all, delete-orphan")


class DatasetColumn(Base):
    __tablename__ = "dataset_columns"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False)
    column_name = Column(String(255), nullable=False)
    data_type = Column(String(50), default="string", nullable=False)  # string, number, date, boolean
    is_numeric = Column(Boolean, default=False, nullable=False)
    sample_values_json = Column(JSON, default=list, nullable=False)
    stats_json = Column(JSON, default=dict, nullable=False)  # min, max, mean, null_count
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    dataset = relationship("Dataset", back_populates="columns")


class AIChangeSet(Base):
    __tablename__ = "ai_change_sets"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    report_id = Column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(50), default="pending", nullable=False)  # pending, accepted, rejected, partially_accepted
    summary = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)

    changes = relationship("AIChange", back_populates="change_set", cascade="all, delete-orphan")


class AIChange(Base):
    __tablename__ = "ai_changes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    change_set_id = Column(String(36), ForeignKey("ai_change_sets.id", ondelete="CASCADE"), nullable=False)
    section_id = Column(String(36), ForeignKey("report_sections.id", ondelete="CASCADE"), nullable=False)
    change_type = Column(String(50), default="replace", nullable=False)  # insert, replace, rewrite, delete
    description = Column(String(500), nullable=True)
    before_text = Column(Text, nullable=True)
    after_text = Column(Text, nullable=True)
    before_json = Column(JSON, default=dict, nullable=False)
    after_json = Column(JSON, default=dict, nullable=False)
    status = Column(String(50), default="pending", nullable=False)  # pending, accepted, rejected
    change_set = relationship("AIChangeSet", back_populates="changes")


class Automation(Base):
    __tablename__ = "automations"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    name = Column(String(255), nullable=False)
    trigger_type = Column(String(50), default="manual", nullable=False)  # manual, schedule, data_refresh
    cron_expression = Column(String(100), nullable=True)  # e.g. "0 8 * * 1"
    data_source_id = Column(String(36), nullable=True)
    template_id = Column(String(36), nullable=True)
    report_title_pattern = Column(String(255), default="Báo cáo Tự động {date}", nullable=False)
    export_formats_json = Column(JSON, default=list, nullable=False)  # ["docx", "pdf"]
    is_active = Column(Boolean, default=True, nullable=False)
    last_run_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now, nullable=False)

    project = relationship("Project", backref="automations")
    runs = relationship("AutomationRun", back_populates="automation", cascade="all, delete-orphan")


class AutomationRun(Base):
    __tablename__ = "automation_runs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    automation_id = Column(String(36), ForeignKey("automations.id", ondelete="CASCADE"), nullable=False)
    report_id = Column(String(36), nullable=True)
    status = Column(String(50), default="queued", nullable=False)  # queued, running, completed, failed, cancelled
    trigger_source = Column(String(50), default="manual", nullable=False)
    retry_count = Column(Integer, default=0, nullable=False)
    log_messages_json = Column(JSON, default=list, nullable=False)
    error_message = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), default=get_utc_now, nullable=False)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    automation = relationship("Automation", back_populates="runs")


