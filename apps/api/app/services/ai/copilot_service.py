import json
from typing import Any, Dict, List, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType
from app.schemas.ai import CopilotMessageRequest, CopilotMessageResponse
from app.services.knowledge.retrieval_service import retrieval_service


class CopilotService:
    """
    AI Project Copilot Service.
    Maintains situational awareness of:
    - Report content & active section
    - Selected text from editor
    - Project metadata & audience
    - Uploaded knowledge chunks
    - Verified research sources
    """

    @classmethod
    async def chat(
        cls,
        req: CopilotMessageRequest,
        project_metadata: Dict[str, Any],
        knowledge_docs: List[Dict[str, Any]],
        sources: List[Dict[str, Any]],
        section_title: Optional[str] = None,
        section_text: Optional[str] = None,
    ) -> CopilotMessageResponse:
        # 1. Retrieve relevant knowledge chunks if relevant to message
        relevant_chunks = retrieval_service.search_relevant_chunks(
            query=req.message + (f" {req.selected_text}" if req.selected_text else ""),
            documents=knowledge_docs,
            top_k=3
        )
        knowledge_context = "\n".join([f"- [Từ {c['doc_name']}]: {c['text']}" for c in relevant_chunks])

        # 2. Build Sources context
        sources_context = "\n".join([f"[{i+1}] {s.get('title')} ({s.get('publisher', '')}) - {s.get('summary', '')}" for i, s in enumerate(sources[:5])])

        system_prompt = (
            "Bạn là AI Project Copilot cao cấp trong Universal AI Document Studio. "
            "Bạn có năng lực hỗ trợ toàn diện: soạn thảo, viết tiếp, biên tập chuyên nghiệp, "
            "tạo bảng so sánh, tóm tắt điều hành (Executive Summary), rà soát số liệu và tìm luận cứ. "
            "Hãy trả lời thông minh, súc tích, văn phong chuyên nghiệp và định dạng rõ ràng."
        )

        user_prompt = f"""
THÔNG TIN DỰ ÁN:
- Loại tài liệu: {project_metadata.get('document_type', 'Báo cáo chuyên môn')}
- Độc giả mục tiêu: {project_metadata.get('audience', 'Ban Lãnh đạo & Đối tác')}
- Mục hiện tại đang chọn: {section_title or 'Chưa chọn mục cụ thể'}

NỘI DUNG VĂN BẢN ĐANG SOẠN THẢO TRONG MỤC:
"{section_text[:1500] if section_text else 'Chưa có nội dung.'}"

{f'ĐOẠN VĂN BẢN NGƯỜI DÙNG ĐANG BÔI ĐEN:\n"{req.selected_text}"\n' if req.selected_text else ''}

TRI THỨC TRÍCH XUẤT TỪ FILE ĐÍNH KÈM:
{knowledge_context or 'Không có trích đoạn liên quan.'}

DANH MỤC NGUỒN ĐÃ KIỂM CHỨNG:
{sources_context or 'Chưa có nguồn ngoài.'}

YÊU CẦU CỦA NGƯỜI DÙNG:
"{req.message}"

Hãy đưa ra câu trả lời và nội dung đề xuất tốt nhất. Nếu người dùng yêu cầu viết hoặc sửa văn bản, hãy cung cấp nội dung hoàn chỉnh để người dùng có thể chèn trực tiếp vào tài liệu.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.REWRITE if req.selected_text else AITaskType.SECTION_WRITING,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.3,
            )
        )

        reply_text = ai_res.text or ""

        return CopilotMessageResponse(
            reply=reply_text,
            action_type="text_insert" if len(reply_text) > 100 else None,
            payload={"text": reply_text}
        )


copilot_service = CopilotService()
