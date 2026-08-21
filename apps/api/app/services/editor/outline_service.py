import json
from typing import Any, Dict, List, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType
from app.schemas.ai import (
    AnalyzeIntentRequest, AnalyzeIntentResponse,
    OutlineGenerationRequest, OutlineGenerationResponse
)
from app.schemas.report import OutlineItem
from app.services.metadata.metadata_helper import metadata_helper


class OutlineService:
    """Universal Document & Outline Architect Service supporting all business, technical, research and financial profiles."""

    @staticmethod
    async def analyze_intent(req: AnalyzeIntentRequest) -> AnalyzeIntentResponse:
        system_prompt = (
            "Bạn là một Principal Enterprise Document Architect & AI Strategy Consultant. "
            "Nhiệm vụ của bạn là nhận mô tả ý tưởng của người dùng, phân tích sâu sắc mục tiêu, "
            "tự động suy luận loại tài liệu phù hợp nhất (business_report, data_analysis, research, technical, proposal, financial, market_research, custom), "
            "đối tượng độc giả mục tiêu (audience), các chủ đề then chốt, yêu cầu dữ liệu và đề xuất các trường metadata tùy biến. "
            "Bắt buộc trả về kết quả dưới định dạng JSON với các khóa: "
            "suggested_title, suggested_type, objective, target_audience, key_themes (array), "
            "suggested_custom_fields (array of {key, label, type, required, value}), data_requirements, research_requirements."
        )

        user_prompt = f"""
Ý TƯỞNG CỦA NGƯỜI DÙNG:
"{req.user_prompt}"

DANH MỤC BAN ĐẦU (NẾU CÓ): {req.selected_type or "Tự động phân loại"}

Hãy phân tích và trả về JSON cấu trúc theo đúng format yêu cầu.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.INTENT_DETECTION,
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.3,
            )
        )

        raw_text = ai_res.text or "{}"
        try:
            data = json.loads(raw_text)
        except Exception:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        suggested_type = data.get("suggested_type", req.selected_type or "business_report")
        default_fields = [f.model_dump() for f in metadata_helper.get_default_fields_for_type(suggested_type)]

        return AnalyzeIntentResponse(
            suggested_title=data.get("suggested_title", req.user_prompt[:80]),
            suggested_type=suggested_type,
            objective=data.get("objective", "Xây dựng tài liệu báo cáo toàn diện và chuyên nghiệp."),
            target_audience=data.get("target_audience", "Hội đồng Quản trị, Ban Lãnh đạo & Đối tác"),
            key_themes=data.get("key_themes", ["Tổng quan bối cảnh", "Phân tích thực trạng", "Đề xuất giải pháp & Lộ trình"]),
            suggested_custom_fields=data.get("suggested_custom_fields") or default_fields,
            data_requirements=data.get("data_requirements", "Bảng số liệu thống kê, biểu đồ tài chính hoặc KPI liên quan."),
            research_requirements=data.get("research_requirements", "Tài liệu kỹ thuật chính thức, tiêu chuẩn ngành hoặc báo cáo thị trường uy tín.")
        )

    @staticmethod
    async def generate_outline(req: OutlineGenerationRequest) -> OutlineGenerationResponse:
        system_prompt = (
            "Bạn là một Principal Document Architect & Strategy Consultant. "
            "Nhiệm vụ của bạn là xây dựng cấu trúc đề cương tài liệu chuyên sâu, chuẩn mực và logic cho mọi loại tài liệu "
            "(Business Report, Data Analysis, Technical Documentation, Proposal, Financial Report, Market Research). "
            "Bắt buộc trả về kết quả dưới định dạng JSON với các khóa: "
            "project_understanding, objectives (array), scope, suggested_methodology, outline (array of objects with title, level, position, children)."
        )

        user_prompt = f"""
LOẠI TÀI LIỆU: {req.project_type.upper()}
TIÊU ĐỀ: {req.topic_name}
MÔ TẢ CHI TIẾT: {req.topic_description or "Chưa có mô tả chi tiết."}
ĐỐI TƯỢNG ĐỘC GIẢ: {req.audience or "Ban Lãnh đạo & Các bên liên quan"}
YÊU CẦU ĐẶC THÙ: {req.requirements_text or "Theo chuẩn mực chuyên nghiệp cao nhất."}
SỐ LƯỢNG MỤC CHÍNH MỤC TIÊU: {req.target_chapters_count} phần.

Hãy tạo cấu trúc đề cương hoàn chỉnh với các phần chính (Level 1) và tiểu mục con (Level 2).
Đảm bảo tính bao quát: Tóm tắt điều hành (Executive Summary), Bối cảnh & Thực trạng, Phân tích chuyên sâu / Dữ liệu, Đề xuất chiến lược / Kế hoạch triển khai, Rủi ro & Kết luận.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.OUTLINE,
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.3,
            )
        )

        raw_text = ai_res.text or "{}"
        try:
            data = json.loads(raw_text)
        except Exception:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        raw_outline = data.get("outline", [])
        parsed_outline: List[OutlineItem] = []

        for item in raw_outline:
            children = [
                OutlineItem(
                    title=c.get("title", ""),
                    level=c.get("level", 2),
                    position=c.get("position", idx + 1),
                    section_number=c.get("section_number", ""),
                    description=c.get("description", ""),
                    children=[]
                )
                for idx, c in enumerate(item.get("children", []))
            ]

            parsed_outline.append(
                OutlineItem(
                    title=item.get("title", ""),
                    level=item.get("level", 1),
                    position=item.get("position", len(parsed_outline) + 1),
                    section_number=item.get("section_number", ""),
                    description=item.get("description", ""),
                    children=children
                )
            )

        return OutlineGenerationResponse(
            project_understanding=data.get("project_understanding", "Phân tích tài liệu hoàn tất."),
            objectives=data.get("objectives", ["Đánh giá toàn diện bối cảnh", "Cung cấp phân tích dựa trên dữ liệu", "Đề xuất lộ trình hành động"]),
            scope=data.get("scope", "Phạm vi tài liệu bao quát các khía cạnh phân tích chiến lược và dữ liệu."),
            suggested_methodology=data.get("suggested_methodology", "Phân tích định lượng kết hợp khung đánh giá tiêu chuẩn."),
            outline=parsed_outline
        )


outline_service = OutlineService()
