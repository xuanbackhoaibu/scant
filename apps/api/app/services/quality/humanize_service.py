from typing import Any, Dict, Optional
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class HumanizeService:
    """
    Advanced Academic & Executive Text Humanizer.
    Eliminates robotic AI footprints while preserving 100% technical claims, numbers, and citations.
    """

    STYLE_PROMPTS = {
        "academic": (
            "Bạn là một Giáo sư và Tổng biên tập Tạp chí Khoa học Quốc tế. "
            "Hãy viết lại (humanize) đoạn văn sau đây để đạt văn phong học thuật xuất sắc nhất: "
            "câu văn tự nhiên, có chiều sâu lý luận, không bị gượng gạo hay lặp từ máy móc. "
            "Tuyệt đối giữ nguyên toàn bộ số liệu, công thức toán học và mã trích dẫn nguồn như [1], [2]."
        ),
        "executive": (
            "Bạn là một C-level Executive & Principal Consultant. "
            "Hãy chuyển hóa văn bản này thành văn phong điều hành sắc bén, rõ ràng, mang tính chiến lược cao, "
            "loại bỏ toàn bộ các từ nối rườm rà sáo rỗng. Giữ nguyên số liệu và đề xuất cốt lõi."
        ),
        "concise": (
            "Hãy tóm gọn và viết lại văn bản một cách súc tích nhất, loại bỏ từ thừa, tăng mật độ thông tin hữu ích. "
            "Giữ nguyên mọi số liệu và chỉ số định lượng."
        ),
        "natural": (
            "Hãy viết lại văn bản bằng giọng văn tự nhiên của một chuyên gia bản ngữ Việt Nam, "
            "thay thế các cấu trúc câu dịch thuật hoặc máy móc bằng cách diễn đạt mạch lạc, uyển chuyển."
        )
    }

    @classmethod
    async def humanize(
        cls,
        text: str,
        style: str = "academic",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        if not text or not text.strip():
            return {"original_text": text, "humanized_text": text, "style": style, "words_changed": 0}

        system_prompt = cls.STYLE_PROMPTS.get(style, cls.STYLE_PROMPTS["academic"])
        if custom_instructions:
            system_prompt += f"\nYêu cầu bổ sung: {custom_instructions}"

        user_prompt = f"""
VĂN BẢN CẦN HUMAN-IZE / NÂNG CẤP VĂN PHONG:
---
{text}
---

Hãy trả về văn bản đã được hoàn thiện mượt mà và tự nhiên nhất. Chỉ trả về nội dung bài viết, không kèm lời mở đầu hoặc kết luận của AI.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.REWRITE,
                prompt=user_prompt,
                system_prompt=system_prompt,
                temperature=0.4,
            )
        )

        humanized = ai_res.text.strip()
        orig_words = len(text.split())
        new_words = len(humanized.split())

        return {
            "original_text": text,
            "humanized_text": humanized,
            "style": style,
            "original_word_count": orig_words,
            "humanized_word_count": new_words,
            "tokens_used": ai_res.usage.total_tokens if ai_res.usage else 0,
        }


humanize_service = HumanizeService()
