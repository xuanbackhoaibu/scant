import json
import re
from typing import Any, Dict, List, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType
from app.schemas.ai import (
    AnalyzeIntentRequest, AnalyzeIntentResponse,
    OutlineGenerationRequest, OutlineGenerationResponse
)
from app.schemas.report import OutlineItem
from app.services.metadata.metadata_helper import metadata_helper


def _safe_parse_json(raw_text: str) -> Dict[str, Any]:
    if not raw_text or not raw_text.strip():
        return {}
    
    clean = raw_text.strip()
    if "```json" in clean:
        clean = clean.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in clean:
        clean = clean.split("```", 1)[1].split("```", 1)[0].strip()

    try:
        return json.loads(clean)
    except Exception:
        pass

    # Try extracting outermost JSON object
    start = clean.find("{")
    end = clean.rfind("}")
    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(clean[start:end+1])
        except Exception:
            pass

    # Try fixing unclosed brackets
    if start != -1:
        fragment = clean[start:]
        # Remove trailing comma if any
        fragment = re.sub(r",\s*$", "", fragment)
        open_curly = fragment.count("{") - fragment.count("}")
        open_square = fragment.count("[") - fragment.count("]")
        repaired = fragment + ("]" * max(0, open_square)) + ("}" * max(0, open_curly))
        try:
            return json.loads(repaired)
        except Exception:
            pass

    return {}


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

        data = _safe_parse_json(ai_res.text or "{}")

        suggested_type = data.get("suggested_type", req.selected_type or "business_report")
        default_fields = [f.model_dump() for f in metadata_helper.get_default_fields_for_type(suggested_type)]

        def _to_str(val: Any, default: str = "") -> str:
            if val is None:
                return default
            if isinstance(val, list):
                return "\n".join([str(x) for x in val if str(x).strip()])
            return str(val)

        def _to_list_str(val: Any, default: Optional[List[str]] = None) -> List[str]:
            if val is None:
                return default or []
            if isinstance(val, list):
                return [str(x) for x in val]
            return [str(val)]

        return AnalyzeIntentResponse(
            suggested_title=_to_str(data.get("suggested_title"), req.user_prompt[:80]),
            suggested_type=_to_str(suggested_type, "business_report"),
            objective=_to_str(data.get("objective"), "Xây dựng tài liệu báo cáo toàn diện và chuyên nghiệp."),
            target_audience=_to_str(data.get("target_audience"), "Hội đồng Quản trị, Ban Lãnh đạo & Đối tác"),
            key_themes=_to_list_str(data.get("key_themes"), ["Tổng quan bối cảnh", "Phân tích thực trạng", "Đề xuất giải pháp & Lộ trình"]),
            suggested_custom_fields=data.get("suggested_custom_fields") if isinstance(data.get("suggested_custom_fields"), list) else default_fields,
            data_requirements=_to_str(data.get("data_requirements"), "Bảng số liệu thống kê, biểu đồ tài chính hoặc KPI liên quan."),
            research_requirements=_to_str(data.get("research_requirements"), "Tài liệu kỹ thuật chính thức, tiêu chuẩn ngành hoặc báo cáo thị trường uy tín.")
        )

    @staticmethod
    async def generate_outline(req: OutlineGenerationRequest) -> OutlineGenerationResponse:
        dataset_outline = OutlineService._dataset_outline_from_requirements(req)
        if dataset_outline:
            return dataset_outline

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

        data = _safe_parse_json(ai_res.text or "{}")

        raw_outline = data.get("outline", [])
        parsed_outline: List[OutlineItem] = []

        if not raw_outline:
            # High-quality structural fallback outline if LLM json was unparseable
            raw_outline = [
                {"title": "1. Tóm Tắt Điều Hành (Executive Summary)", "children": [{"title": "1.1. Mục tiêu và bối cảnh cốt lõi"}, {"title": "1.2. Các phát hiện và kết luận then chốt"}]},
                {"title": "2. Tổng Quan Bối Cảnh & Thực Trạng", "children": [{"title": "2.1. Cơ sở lý luận và tiêu chuẩn ngành"}, {"title": "2.2. Đánh giá hiện trạng thực tế"}]},
                {"title": "3. Phân Tích Chuyên Sâu & Đối Soát Dữ Liệu", "children": [{"title": "3.1. Thu thập và xử lý số liệu"}, {"title": "3.2. Đánh giá định lượng và mô hình"}]},
                {"title": "4. Đề Xuất Chiến Lược & Kế Hoạch Triển Khai", "children": [{"title": "4.1. Khung giải pháp trọng tâm"}, {"title": "4.2. Lộ trình thực thi và phân bổ nguồn lực"}]},
                {"title": "5. Quản Trị Rủi Ro & Kết Luận", "children": [{"title": "5.1. Nhận diện rủi ro và biện pháp giảm thiểu"}, {"title": "5.2. Kết luận và kiến nghị"}]},
            ]

        def _safe_int(val, default):
            try:
                if val is None:
                    return default
                return int(float(val))
            except Exception:
                return default

        for item_idx, item in enumerate(raw_outline):
            children = [
                OutlineItem(
                    title=c.get("title", ""),
                    level=_safe_int(c.get("level"), 2),
                    position=_safe_int(c.get("position"), idx + 1),
                    section_number=str(c.get("section_number", "")),
                    description=c.get("description", ""),
                    children=[]
                )
                for idx, c in enumerate(item.get("children", []))
            ]

            parsed_outline.append(
                OutlineItem(
                    title=item.get("title", ""),
                    level=_safe_int(item.get("level"), 1),
                    position=_safe_int(item.get("position"), item_idx + 1),
                    section_number=str(item.get("section_number", "")),
                    description=item.get("description", ""),
                    children=children
                )
            )

        return OutlineGenerationResponse(
            project_understanding=data.get("project_understanding", f"Phân tích hoàn tất cho đề tài: {req.topic_name}."),
            objectives=data.get("objectives", ["Đánh giá toàn diện bối cảnh", "Cung cấp phân tích dựa trên dữ liệu", "Đề xuất lộ trình hành động"]),
            scope=data.get("scope", "Phạm vi tài liệu bao quát các khía cạnh phân tích chiến lược và dữ liệu."),
            suggested_methodology=data.get("suggested_methodology", "Phân tích định lượng kết hợp khung đánh giá tiêu chuẩn."),
            outline=parsed_outline
        )

    @staticmethod
    def _dataset_outline_from_requirements(req: OutlineGenerationRequest) -> Optional[OutlineGenerationResponse]:
        text = f"{req.project_type} {req.topic_name} {req.topic_description or ''} {req.requirements_text or ''}".lower()
        if "data_analysis" not in text:
            return None

        is_payroll = any(k in text for k in ["lương", "luong", "salary", "thực lĩnh", "thu nhập"]) and any(
            k in text for k in ["nhân viên", "nhan vien", "employee", "phòng ban", "phong ban", "department"]
        )
        if not is_payroll:
            return None

        outline = [
            OutlineItem(
                title="CHƯƠNG 1: TỔNG QUAN DỮ LIỆU BẢNG LƯƠNG",
                level=1,
                position=1,
                children=[
                    OutlineItem(title="1.1 Phạm vi file dữ liệu và cấu trúc bảng lương", level=2, position=1, children=[]),
                    OutlineItem(title="1.2 Các chỉ tiêu lương, thuế và ngày công cần phân tích", level=2, position=2, children=[]),
                ],
            ),
            OutlineItem(
                title="CHƯƠNG 2: PHÂN TÍCH LƯƠNG THEO PHÒNG BAN VÀ CHỨC VỤ",
                level=1,
                position=2,
                children=[
                    OutlineItem(title="2.1 Thống kê tổng lương và lương trung bình theo phòng ban", level=2, position=1, children=[]),
                    OutlineItem(title="2.2 So sánh thực lĩnh, thuế TNCN và phụ cấp theo nhóm nhân sự", level=2, position=2, children=[]),
                ],
            ),
            OutlineItem(
                title="CHƯƠNG 3: NHẬN XÉT KPI VÀ KẾT LUẬN",
                level=1,
                position=3,
                children=[
                    OutlineItem(title="3.1 Các điểm nổi bật và bất thường trong dữ liệu lương", level=2, position=1, children=[]),
                    OutlineItem(title="3.2 Kết luận và khuyến nghị quản trị tiền lương", level=2, position=2, children=[]),
                ],
            ),
        ]

        return OutlineGenerationResponse(
            project_understanding="Báo cáo tập trung phân tích dữ liệu bảng lương đã tải lên, chỉ sử dụng số liệu kiểm định từ Excel/CSV.",
            objectives=[
                "Tổng hợp cấu trúc và chất lượng dữ liệu bảng lương.",
                "Phân tích lương, thuế, ngày công và thực lĩnh theo phòng ban/chức vụ.",
                "Rút ra nhận xét KPI và khuyến nghị quản trị tiền lương.",
            ],
            scope="Phạm vi giới hạn trong dữ liệu bảng lương, phòng ban, chức vụ, ngày công, thuế và thực lĩnh có trong file.",
            suggested_methodology="Phân tích thống kê mô tả và đối chiếu theo nhóm từ dữ liệu đã kiểm định.",
            outline=outline,
        )


outline_service = OutlineService()
