from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class DocumentDesignPreset(BaseModel):
    preset_key: str
    name: str
    description: str
    primary_font: str = "Inter"
    heading_font: str = "Inter"
    primary_color: str = "#1e293b"
    accent_color: str = "#4f46e5"
    line_height: float = 1.6
    heading_hierarchy: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    table_style: str = "modern_clean"  # "modern_clean" | "striped" | "bordered"
    chart_palette: List[str] = Field(default_factory=list)
    cover_style: str = "modern_corporate"  # "modern_corporate" | "minimal_clean" | "formal_classic"


DESIGN_PRESETS: Dict[str, DocumentDesignPreset] = {
    "corporate": DocumentDesignPreset(
        preset_key="corporate",
        name="Corporate Standard",
        description="Phong cách doanh nghiệp chuẩn mực, thanh lịch và uy tín.",
        primary_font="Arial",
        heading_font="Arial",
        primary_color="#0f172a",
        accent_color="#2563eb",
        line_height=1.5,
        table_style="striped",
        chart_palette=["#2563eb", "#38bdf8", "#64748b", "#0f172a"],
        cover_style="modern_corporate",
    ),
    "consulting": DocumentDesignPreset(
        preset_key="consulting",
        name="Management Consulting",
        description="Định dạng chuẩn các công ty tư vấn chiến lược hàng đầu (McKinsey, BCG, Bain).",
        primary_font="Calibri",
        heading_font="Calibri",
        primary_color="#1e1b4b",
        accent_color="#4338ca",
        line_height=1.6,
        table_style="modern_clean",
        chart_palette=["#4338ca", "#06b6d4", "#10b981", "#f59e0b"],
        cover_style="modern_corporate",
    ),
    "minimal": DocumentDesignPreset(
        preset_key="minimal",
        name="Minimal Clean",
        description="Thiết kế tối giản hiện đại, chú trọng khoảng trắng và sự tập trung nội dung.",
        primary_font="Inter",
        heading_font="Inter",
        primary_color="#18181b",
        accent_color="#71717a",
        line_height=1.7,
        table_style="modern_clean",
        chart_palette=["#18181b", "#52525b", "#a1a1aa", "#d4d4d8"],
        cover_style="minimal_clean",
    ),
    "technical": DocumentDesignPreset(
        preset_key="technical",
        name="Technical & Engineering",
        description="Dành cho tài liệu kỹ thuật, kiến trúc phần mềm và hướng dẫn triển khai.",
        primary_font="Roboto",
        heading_font="Roboto",
        primary_color="#0f172a",
        accent_color="#0284c7",
        line_height=1.6,
        table_style="bordered",
        chart_palette=["#0284c7", "#0d9488", "#e11d48", "#64748b"],
        cover_style="formal_classic",
    ),
    "financial": DocumentDesignPreset(
        preset_key="financial",
        name="Financial & Audit",
        description="Tối ưu cho báo cáo tài chính, kiểm toán, ngân hàng và phân tích rủi ro.",
        primary_font="Times New Roman",
        heading_font="Times New Roman",
        primary_color="#064e3b",
        accent_color="#059669",
        line_height=1.5,
        table_style="bordered",
        chart_palette=["#059669", "#10b981", "#6ee7b7", "#064e3b"],
        cover_style="formal_classic",
    ),
    "research": DocumentDesignPreset(
        preset_key="research",
        name="Deep Research",
        description="Định dạng bài báo nghiên cứu khoa học, phân tích thị trường độc lập.",
        primary_font="Merriweather",
        heading_font="Merriweather",
        primary_color="#1e293b",
        accent_color="#9333ea",
        line_height=1.8,
        table_style="modern_clean",
        chart_palette=["#9333ea", "#c084fc", "#64748b", "#3b82f6"],
        cover_style="minimal_clean",
    ),
    "modern": DocumentDesignPreset(
        preset_key="modern",
        name="Modern Editorial",
        description="Phong cách tạp chí kinh doanh và xuất bản nội dung cao cấp.",
        primary_font="Plus Jakarta Sans",
        heading_font="Plus Jakarta Sans",
        primary_color="#09090b",
        accent_color="#e11d48",
        line_height=1.65,
        table_style="modern_clean",
        chart_palette=["#e11d48", "#f43f5e", "#fb7185", "#09090b"],
        cover_style="modern_corporate",
    ),
}


class DocumentDesignerEngine:
    """
    AI Document Designer Engine (Phase U35).
    Generates intelligent layout styling, typography hierarchies, and merges custom Workspace Brand Kits.
    """

    @staticmethod
    def get_preset(preset_key: str) -> DocumentDesignPreset:
        return DESIGN_PRESETS.get(preset_key.lower(), DESIGN_PRESETS["corporate"])

    @staticmethod
    def apply_brand_kit_override(
        preset: DocumentDesignPreset,
        brand_kit: Optional[Dict[str, Any]] = None
    ) -> DocumentDesignPreset:
        if not brand_kit:
            return preset

        # Deep copy/clone preset with brand kit overrides
        merged = preset.model_copy(deep=True)
        if "primary_color" in brand_kit and brand_kit["primary_color"]:
            merged.primary_color = brand_kit["primary_color"]
        if "accent_color" in brand_kit and brand_kit["accent_color"]:
            merged.accent_color = brand_kit["accent_color"]
        if "primary_font" in brand_kit and brand_kit["primary_font"]:
            merged.primary_font = brand_kit["primary_font"]
        if "heading_font" in brand_kit and brand_kit["heading_font"]:
            merged.heading_font = brand_kit["heading_font"]
        if "chart_palette" in brand_kit and brand_kit["chart_palette"]:
            merged.chart_palette = brand_kit["chart_palette"]

        return merged

    async def recommend_design_for_report(
        self,
        report_title: str,
        user_intent: str,
        brand_kit: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        prompt = f"""Bạn là Principal Document Design Consultant.
Đề tài báo cáo: "{report_title}"
Mong muốn người dùng: "{user_intent}"

Các phong cách thiết kế có sẵn: {list(DESIGN_PRESETS.keys())}
Hãy đề xuất phong cách phù hợp nhất và giải thích lý do lựa chọn.
"""
        req = AIRequest(
            task_type=AITaskType.CLASSIFICATION,
            prompt=prompt,
        )
        resp = await ai_gateway.execute(req)

        # Default to consulting/corporate
        chosen_key = "consulting"
        for k in DESIGN_PRESETS.keys():
            if k in resp.text.lower():
                chosen_key = k
                break

        base_preset = self.get_preset(chosen_key)
        final_preset = self.apply_brand_kit_override(base_preset, brand_kit)

        return {
            "recommended_preset_key": chosen_key,
            "design_specs": final_preset.model_dump(),
            "ai_reasoning": resp.text,
            "brand_kit_applied": bool(brand_kit),
        }


document_designer_engine = DocumentDesignerEngine()
