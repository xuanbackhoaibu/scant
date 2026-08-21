from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CustomFieldDefinition(BaseModel):
    key: str
    label: str
    type: str = "text"  # text, textarea, number, currency, percentage, date, select, multi-select, image, file
    required: bool = False
    placeholder: Optional[str] = None
    options: Optional[List[str]] = None  # for select / multi-select
    value: Any = None
    unit: Optional[str] = None  # e.g. "VNĐ", "USD", "%"


class UniversalMetadata(BaseModel):
    document_type: str = "business_report"
    document_profile: Optional[str] = "business"
    audience: Optional[str] = "Executive Board & Stakeholders"
    language: str = "vi"
    custom_fields: List[CustomFieldDefinition] = Field(default_factory=list)


class MetadataHelper:
    """Helper for managing dynamic metadata and converting legacy school fields if present."""

    DEFAULT_TYPE_FIELDS: Dict[str, List[Dict[str, Any]]] = {
        "business_report": [
            {"key": "company_name", "label": "Tên Công ty / Doanh nghiệp", "type": "text", "required": True, "value": ""},
            {"key": "department", "label": "Phòng ban / Bộ phận", "type": "text", "required": False, "value": ""},
            {"key": "author_name", "label": "Người lập báo cáo", "type": "text", "required": True, "value": ""},
            {"key": "approver_name", "label": "Người phê duyệt", "type": "text", "required": False, "value": ""},
            {"key": "report_period", "label": "Kỳ báo cáo", "type": "text", "required": False, "value": ""},
        ],
        "data_analysis": [
            {"key": "dataset_name", "label": "Tên Bộ Dữ Liệu", "type": "text", "required": True, "value": ""},
            {"key": "analyst_name", "label": "Chuyên viên phân tích (Lead Analyst)", "type": "text", "required": True, "value": ""},
            {"key": "organization", "label": "Đơn vị chủ quản", "type": "text", "required": False, "value": ""},
            {"key": "analysis_timeframe", "label": "Khung thời gian phân tích", "type": "text", "required": False, "value": ""},
        ],
        "research": [
            {"key": "lead_researcher", "label": "Chủ nhiệm đề tài / Tác giả chính", "type": "text", "required": True, "value": ""},
            {"key": "institution", "label": "Cơ quan / Tổ chức nghiên cứu", "type": "text", "required": True, "value": ""},
            {"key": "publication_year", "label": "Năm công bố", "type": "text", "required": False, "value": "2026"},
            {"key": "funding_source", "label": "Nguồn tài trợ (nếu có)", "type": "text", "required": False, "value": ""},
        ],
        "technical": [
            {"key": "system_name", "label": "Tên Hệ thống / Sản phẩm", "type": "text", "required": True, "value": ""},
            {"key": "lead_architect", "label": "Kiến trúc sư trưởng / Lead Tech", "type": "text", "required": True, "value": ""},
            {"key": "version", "label": "Phiên bản tài liệu (Version)", "type": "text", "required": True, "value": "v1.0.0"},
            {"key": "status", "label": "Trạng thái", "type": "select", "options": ["Draft", "Review", "Approved", "Production"], "value": "Draft"},
        ],
        "proposal": [
            {"key": "client_name", "label": "Khách hàng / Đối tác mục tiêu", "type": "text", "required": True, "value": ""},
            {"key": "submitting_company", "label": "Đơn vị dự thầu / Đề xuất", "type": "text", "required": True, "value": ""},
            {"key": "estimated_budget", "label": "Ngân sách ước tính", "type": "currency", "unit": "VNĐ", "required": False, "value": ""},
            {"key": "validity_period", "label": "Thời hạn hiệu lực đề xuất", "type": "date", "required": False, "value": ""},
        ],
        "financial": [
            {"key": "company_name", "label": "Tên Doanh nghiệp", "type": "text", "required": True, "value": ""},
            {"key": "fiscal_year", "label": "Năm tài chính / Quý", "type": "text", "required": True, "value": "2026"},
            {"key": "chief_accountant", "label": "Kế toán trưởng / CFO", "type": "text", "required": False, "value": ""},
            {"key": "currency_unit", "label": "Đơn vị tiền tệ", "type": "select", "options": ["VNĐ", "USD", "EUR"], "value": "VNĐ"},
        ],
        "custom": [
            {"key": "document_owner", "label": "Chủ sở hữu tài liệu", "type": "text", "required": True, "value": ""},
            {"key": "organization", "label": "Tổ chức / Doanh nghiệp", "type": "text", "required": False, "value": ""},
            {"key": "created_date", "label": "Ngày lập", "type": "date", "required": False, "value": ""},
        ],
    }

    @classmethod
    def get_default_fields_for_type(cls, project_type: str) -> List[CustomFieldDefinition]:
        type_key = project_type.lower().replace(" ", "_")
        raw_fields = cls.DEFAULT_TYPE_FIELDS.get(type_key, cls.DEFAULT_TYPE_FIELDS["custom"])
        return [CustomFieldDefinition(**f) for f in raw_fields]

    @classmethod
    def normalize_metadata(cls, project_type: str, metadata_input: Optional[Dict[str, Any]] = None, legacy_topic_details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Normalizes input into a unified UniversalMetadata dictionary with custom_fields,
        handling both new generic inputs and legacy payloads cleanly.
        """
        if metadata_input and "custom_fields" in metadata_input and metadata_input["custom_fields"]:
            # Already in universal format
            return metadata_input

        # If legacy topic_details provided, convert to custom_fields
        custom_fields: List[Dict[str, Any]] = []

        if legacy_topic_details:
            label_map = {
                "topic_name": "Tên Đề tài / Dự án",
                "company_name": "Tên Doanh nghiệp / Tổ chức",
                "organization": "Tổ chức / Đơn vị",
                "university": "Đơn vị chủ quản",
                "department": "Phòng ban / Bộ phận",
                "major": "Chuyên ngành / Lĩnh vực",
                "subject": "Chủ đề / Hạng mục",
                "author_name": "Tác giả / Người thực hiện",
                "student_name": "Người thực hiện",
                "student_id": "Mã định danh / ID",
                "instructor": "Người hướng dẫn / Cố vấn",
                "class_name": "Nhóm / Mã phân loại",
                "academic_year": "Kỳ báo cáo / Thời gian",
            }
            for k, v in legacy_topic_details.items():
                if v:
                    custom_fields.append({
                        "key": k,
                        "label": label_map.get(k, k.replace("_", " ").title()),
                        "type": "text",
                        "required": False,
                        "value": str(v),
                    })

        # If still empty, supply sensible defaults for the project type
        if not custom_fields:
            default_defs = cls.get_default_fields_for_type(project_type)
            custom_fields = [d.model_dump() for d in default_defs]

        return {
            "document_type": project_type,
            "document_profile": project_type,
            "audience": (metadata_input or {}).get("audience", "Executive Board & Stakeholders"),
            "custom_fields": custom_fields,
        }


metadata_helper = MetadataHelper()
