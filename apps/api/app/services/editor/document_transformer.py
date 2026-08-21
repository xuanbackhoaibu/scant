import json
from typing import Any, Dict, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class DocumentTransformationService:
    """
    Transforms reports across different enterprise formats:
    - 1-Page Executive Summary
    - Presentation Slides (Markdown / PPT outline)
    - Technical Memo
    - Client Proposal / RFP Response
    """

    @classmethod
    async def transform(
        cls,
        title: str,
        full_text: str,
        target_format: str = "executive_summary",  # executive_summary, presentation_slides, one_page, technical_memo
        target_audience: Optional[str] = None
    ) -> Dict[str, Any]:
        system_prompt = (
            "Bạn là một Principal Enterprise Communications Specialist. "
            "Nhiệm vụ của bạn là chuyển đổi một bản báo cáo dài thành định dạng tài liệu mục tiêu "
            "(Executive Summary, Slide Presentation outline, One-Page Briefing, hoặc Technical Memo). "
            "Giữ nguyên tính chính xác của các số liệu then chốt, thông điệp cốt lõi và đề xuất hành động. "
            "Trả về JSON với các khóa: target_format, formatted_title, content (structured text/markdown), key_takeaways (array)."
        )

        user_prompt = f"""
TIÊU ĐỀ GỐC: {title}
ĐỊNH DẠNG MỤC TIÊU: {target_format.upper()}
ĐỐI TƯỢNG ĐỘC GIẢ: {target_audience or "Ban Điều hành & Hội đồng Quản trị"}

NỘI DUNG BÁO CÁO GỐC:
"{full_text[:5000]}"

Hãy chuyển đổi và trả về JSON cấu trúc hoàn chỉnh.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.DOCUMENT_REVIEW,
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

        return {
            "target_format": target_format,
            "formatted_title": data.get("formatted_title", f"{title} - {target_format.upper()}"),
            "content": data.get("content", full_text[:1000]),
            "key_takeaways": data.get("key_takeaways", ["Tối ưu hiệu quả chi phí", "Tăng tốc chuyển đổi số", "Giảm thiểu rủi ro vận hành"]),
            "gateway_usage": ai_res.usage.model_dump(),
        }


document_transformer = DocumentTransformationService()
