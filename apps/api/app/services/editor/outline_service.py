import json
from typing import Any, Dict, List, Optional
from app.services.ai.provider_factory import ai_factory
from app.schemas.ai import OutlineGenerationRequest, OutlineGenerationResponse
from app.schemas.report import OutlineItem


class OutlineService:
    """Service for generating and structuring academic report outlines."""

    @staticmethod
    async def generate_outline(req: OutlineGenerationRequest) -> OutlineGenerationResponse:
        provider = ai_factory.get_provider()

        system_prompt = (
            "Bạn là một Principal Academic Advisor và Senior Technical Architect. "
            "Nhiệm vụ của bạn là phân tích yêu cầu đề tài bài tập lớn/đồ án, "
            "tạo ra Project Understanding, Research Questions, Objectives, Scope, Suggested Methodology, "
            "và đề xuất Cấu trúc Đề Cương (Outline) phân cấp chi tiết theo chuẩn học thuật các trường Đại học (ĐH Bách Khoa, FPT, KHTN, UIT). "
            "Bắt buộc trả về kết quả dưới định dạng JSON với các khóa: "
            "project_understanding, objectives (array of strings), scope, suggested_methodology, outline (array of objects)."
        )

        user_prompt = f"""
Hãy phân tích đề tài sau và tạo cấu trúc đề cương chi tiết:
- Tên đề tài: {req.topic_name}
- Mô tả đề tài: {req.topic_description or "Chưa có mô tả"}
- Môn học: {req.subject or "Công nghệ phần mềm / Lập trình nâng cao"}
- Chuyên ngành: {req.major or "Công nghệ thông tin"}
- Yêu cầu bổ sung trích từ đề bài: {req.requirements_text or "Không có"}
- Số chương mục tiêu: {req.target_chapters_count} chương.

Yêu cầu cấu trúc outline trả về:
1. Mở đầu / Bối cảnh đề tài
2. Chương 1: Tổng quan đề tài (1.1, 1.2, 1.3, 1.4)
3. Chương 2: Cơ sở lý thuyết & Công nghệ liên quan (2.1, 2.2, 2.3, 2.4)
4. Chương 3: Phân tích và Thiết kế hệ thống (3.1 Yêu cầu, 3.2 Use Case, 3.3 Database ERD, 3.4 Kiến trúc)
5. Chương 4: Hiện thực hóa & Kết quả phát triển (4.1 Module chính, 4.2 Triển khai mã nguồn, 4.3 Giao diện)
6. Chương 5: Kiểm thử và Đánh giá hệ thống (5.1 Kịch bản test, 5.2 Kết quả kiểm thử)
7. Chương 6: Kết luận và Hướng phát triển (6.1 Kết quả đạt được, 6.2 Hạn chế & Hướng phát triển)
8. Tài liệu tham khảo chuẩn IEEE

Trả về kết quả JSON hợp lệ 100%.
"""

        res = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json",
            temperature=0.4
        )

        raw_text = res.get("text", "{}")
        try:
            data = json.loads(raw_text)
        except Exception:
            # Fallback if json parsing fails
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
            project_understanding=data.get("project_understanding", "Phân tích đề tài hoàn tất."),
            objectives=data.get("objectives", ["Nghiên cứu cơ sở lý thuyết", "Xây dựng hệ thống hoàn chỉnh"]),
            scope=data.get("scope", "Phạm vi chức năng và kiểm thử đề tài."),
            suggested_methodology=data.get("suggested_methodology", "Nghiên cứu thực nghiệm kết hợp Agile."),
            outline=parsed_outline
        )


outline_service = OutlineService()
