import re
import unicodedata
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
    def _normalize_message(cls, message: str) -> str:
        return re.sub(r"\s+", " ", (message or "").strip().lower())

    @classmethod
    def _ascii_message(cls, message: str) -> str:
        normalized = unicodedata.normalize("NFD", cls._normalize_message(message))
        normalized = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return normalized.replace("đ", "d")

    @classmethod
    def _is_small_talk(cls, message: str) -> bool:
        normalized = cls._normalize_message(message)
        compact = re.sub(r"[!?.。,…,;:]+", "", normalized).strip()
        greetings = {
            "hi",
            "hello",
            "hey",
            "xin chao",
            "xin chào",
            "chao",
            "chào",
            "chào bạn",
            "xin chào bạn",
            "alo",
            "test",
        }
        if compact in greetings:
            return True
        return len(compact.split()) <= 3 and any(word in compact for word in ["chào", "hello", "hi", "hey"])

    @classmethod
    def _is_action_request(cls, message: str) -> bool:
        normalized = cls._normalize_message(message)
        ascii_message = cls._ascii_message(message)
        question_terms = [
            "la gi",
            "tac dung",
            "de lam gi",
            "sao",
            "tai sao",
            "nhu the nao",
            "co nghia la",
            "giai thich",
            "hoi",
            "khong hoat dong",
        ]
        explicit_action_patterns = [
            r"\b(hay|hãy|giup toi|giúp tôi|lam on|làm ơn|vui long|vui lòng)\s+",
            r"\b(viet|viết|soan|soạn|tao|tạo|chen|chèn|sua|sửa|doi|đổi|viet lai|viết lại)\b",
            r"\b(mo rong|mở rộng|rut gon|rút gọn|tom tat|tóm tắt|lap bang|lập bảng|ve bieu do|vẽ biểu đồ|tao bang|tạo bảng|tao anh|tạo ảnh)\b",
            r"\b(rewrite|generate|create|insert|summarize|make|edit|fix|translate)\b",
        ]
        has_explicit_action = any(re.search(pattern, normalized) or re.search(pattern, ascii_message) for pattern in explicit_action_patterns)
        if not has_explicit_action:
            return False
        if "?" in normalized and any(term in ascii_message for term in question_terms):
            return False
        return True

    @classmethod
    def _is_project_identity_question(cls, message: str) -> bool:
        ascii_message = cls._ascii_message(message)
        patterns = [
            r"\bde tai\b.*\b(la gi|gi|nao)\b",
            r"\bchu de\b.*\b(la gi|gi|nao)\b",
            r"\bten\b.*\b(du an|bao cao|de tai)\b",
            r"\btoi dang lam\b.*\b(gi|de tai nao|chu de nao)\b",
            r"\bproject\b.*\b(name|topic)\b",
            r"\breport\b.*\b(title|topic)\b",
        ]
        return any(re.search(pattern, ascii_message) for pattern in patterns)

    @classmethod
    def _mentions_current_section(cls, message: str) -> bool:
        ascii_message = cls._ascii_message(message)
        return any(term in ascii_message for term in ["phan nay", "muc nay", "doan nay", "noi dung nay", "section nay"])

    @classmethod
    def _project_topic_answer(cls, project_metadata: Dict[str, Any]) -> str:
        topic_details = project_metadata.get("topic_details") or {}
        topic = (
            topic_details.get("topic")
            or topic_details.get("title")
            or topic_details.get("topic_name")
            or project_metadata.get("report_title")
            or project_metadata.get("project_name")
            or "Chưa có tên đề tài trong dữ liệu dự án."
        )
        description = project_metadata.get("project_description") or topic_details.get("description")
        if description:
            return f"Đề tài hiện tại của bạn là: **{topic}**.\n\nMô tả ngắn: {description}"
        return f"Đề tài hiện tại của bạn là: **{topic}**."

    @classmethod
    def _project_context_lines(cls, project_metadata: Dict[str, Any], section_title: Optional[str]) -> str:
        topic_details = project_metadata.get("topic_details") or {}
        topic = (
            topic_details.get("topic")
            or topic_details.get("title")
            or topic_details.get("topic_name")
            or project_metadata.get("project_name")
            or "Chưa có tên đề tài"
        )
        return "\n".join([
            f"- Đề tài/dự án: {topic}",
            f"- Tên báo cáo: {project_metadata.get('report_title') or 'Chưa có báo cáo cụ thể'}",
            f"- Mô tả: {project_metadata.get('project_description') or topic_details.get('description') or 'Chưa có mô tả'}",
            f"- Loại tài liệu: {project_metadata.get('report_type') or project_metadata.get('project_type') or project_metadata.get('document_type') or 'Báo cáo chuyên môn'}",
            f"- Mục đang chọn: {section_title or 'Chưa chọn mục cụ thể'}",
        ])

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
        if cls._is_small_talk(req.message):
            return CopilotMessageResponse(
                reply=(
                    "Chào bạn. Mình đang sẵn sàng hỗ trợ trong Studio. "
                    "Bạn có thể yêu cầu mình viết tiếp mục đang chọn, tạo bảng, tạo biểu đồ, sửa văn phong hoặc kiểm tra nội dung."
                ),
                action_type=None,
                payload=None,
            )

        if cls._is_project_identity_question(req.message):
            return CopilotMessageResponse(
                reply=cls._project_topic_answer(project_metadata),
                action_type=None,
                payload=None,
            )

        is_action_request = cls._is_action_request(req.message) or bool(req.selected_text)

        # 1. Retrieve relevant knowledge chunks only when they can help the current reply.
        relevant_chunks = retrieval_service.search_relevant_chunks(
            query=req.message + (f" {req.selected_text}" if req.selected_text else ""),
            documents=knowledge_docs,
            top_k=3 if is_action_request else 1
        )
        knowledge_context = "\n".join([f"- [Từ {c['doc_name']}]: {c['text']}" for c in relevant_chunks])

        # 2. Build Sources context
        sources_context = "\n".join([f"[{i+1}] {s.get('title')} ({s.get('publisher', '')}) - {s.get('summary', '')}" for i, s in enumerate(sources[:5])])

        if not is_action_request:
            section_context = ""
            if cls._mentions_current_section(req.message) and section_text:
                section_context = f'\nNỘI DUNG MỤC ĐANG CHỌN RÚT GỌN:\n"{section_text[:700]}"\n'

            system_prompt = (
                "Bạn là một chatbot trợ lý giống ChatGPT, đang nằm trong AI Report Studio. "
                "Nhiệm vụ trong chế độ này là trả lời đúng câu hỏi của người dùng, không thực hiện thao tác với tài liệu. "
                "Quy tắc: trả lời trực tiếp, ngắn gọn, đúng trọng tâm; nếu thiếu dữ liệu thì nói rõ thiếu dữ liệu; không tự viết báo cáo; không đề xuất chèn nội dung trừ khi người dùng yêu cầu."
            )

            user_prompt = f"""
CHẾ ĐỘ COPILOT CHAT: ANSWER_ONLY

CÂU HỎI CỦA NGƯỜI DÙNG:
"{req.message}"

NGỮ CẢNH DỰ ÁN:
{cls._project_context_lines(project_metadata, section_title)}
{section_context}
TRI THỨC LIÊN QUAN RÚT GỌN:
{knowledge_context or 'Không có trích đoạn liên quan.'}

Hãy trả lời như ChatGPT: đúng câu hỏi, không lan man, tối đa 4 câu trừ khi người dùng yêu cầu chi tiết.
"""

            ai_res = await ai_gateway.execute(
                AIRequest(
                    task_type=AITaskType.AGENT_REASONING,
                    prompt=user_prompt,
                    system_prompt=system_prompt,
                    temperature=0.2,
                    max_tokens=500,
                )
            )
            return CopilotMessageResponse(
                reply=(ai_res.text or "").strip(),
                action_type=None,
                payload=None,
            )

        system_prompt = (
            "Bạn là Copilot thao tác tài liệu trong Universal AI Document Studio. "
            "Người dùng đã yêu cầu thực hiện một việc với báo cáo. Hãy tạo đúng nội dung cần thiết để có thể chèn vào tài liệu. "
            "Không trả lời lan man; ưu tiên nội dung hoàn chỉnh, có cấu trúc, phù hợp mục đang chọn."
        )

        user_prompt = f"""
THÔNG TIN DỰ ÁN:
- Tên dự án/đề tài: {project_metadata.get('project_name') or 'Chưa có tên dự án'}
- Tên báo cáo: {project_metadata.get('report_title') or 'Chưa có báo cáo cụ thể'}
- Mô tả dự án: {project_metadata.get('project_description') or 'Chưa có mô tả'}
- Chi tiết đề tài: {project_metadata.get('topic_details') or {}}
- Loại tài liệu: {project_metadata.get('report_type') or project_metadata.get('project_type') or project_metadata.get('document_type') or 'Báo cáo chuyên môn'}
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

Hãy thực hiện đúng yêu cầu của người dùng và cung cấp nội dung hoàn chỉnh để có thể chèn trực tiếp vào tài liệu.
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
            action_type="text_insert" if is_action_request and len(reply_text) > 80 else None,
            payload={"text": reply_text} if is_action_request and len(reply_text) > 80 else None,
        )


copilot_service = CopilotService()
