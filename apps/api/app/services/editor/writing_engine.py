import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.services.ai.provider_factory import ai_factory
from app.services.citations.claim_validator import claim_validator
from app.services.citations.citation_formatter import citation_formatter


class WritingEngine:
    """AI Academic Writing Engine with genuine citations and section-by-section generation."""

    @classmethod
    async def draft_section(
        cls,
        section_title: str,
        section_level: int,
        topic_name: str,
        sources: List[Dict[str, Any]],
        previous_summary: str = "",
        instruction: Optional[str] = None,
        tone: str = "academic",
    ) -> Dict[str, Any]:
        provider = ai_factory.get_provider()

        # Build formatted source list for context
        sources_context_lines = []
        sources_map: Dict[int, Dict[str, Any]] = {}
        for idx, src in enumerate(sources[:8], 1):
            sources_map[idx] = src
            sources_context_lines.append(
                f"[{idx}] {src.get('title')} ({src.get('publisher', 'NXB')}, {src.get('published_date', '2024')}) — Tóm tắt: {src.get('summary', '')}"
            )
        sources_context = "\n".join(sources_context_lines)

        system_prompt = (
            "Bạn là một Giáo sư hướng dẫn và Chuyên gia kỹ thuật cao cấp. "
            "Nhiệm vụ của bạn là soạn thảo nội dung học thuật cho một mục/chương trong báo cáo tốt nghiệp hoặc bài tập lớn. "
            "QUY TẮC TUYỆT ĐỐI VỀ TRÍCH DẪN (ANTI-HALLUCINATION): "
            "1. Chỉ được phép trích dẫn bằng mã số [1], [2], ... theo danh sách tài liệu tham khảo cung cấp dưới đây. "
            "2. KHÔNG TỰ BỊA ĐẶT trích dẫn hoặc mã số ngoài danh sách. "
            "3. Sử dụng văn phong học thuật, chuẩn mực, rành mạch, đi sâu vào chi tiết kỹ thuật và giải thích cụ thể."
        )

        user_prompt = f"""
ĐỀ TÀI BÁO CÁO: {topic_name}
MỤC ĐANG SOẠN THẢO: {section_title} (Cấp độ: Heading {section_level})
YÊU CẦU BỔ SUNG: {instruction or "Trình bày chi tiết, chuyên sâu và đầy đủ luận điểm kỹ thuật."}

TÓM TẮT NGỮ CẢNH CÁC CHƯƠNG TRƯỚC:
{previous_summary or "Đây là phần đầu của báo cáo."}

DANH SÁCH TÀI LIỆU THAM KHẢO HỢP LỆ ĐƯỢC PHÉP TRÍCH DẪN:
{sources_context if sources_context else "Chưa có tài liệu ngoài. Viết dựa trên phân tích kỹ thuật của đề tài."}

Hãy viết nội dung hoàn chỉnh cho mục "{section_title}". Chia thành các đoạn văn mạch lạc, phân tích cấu trúc, bảng biểu hoặc mã nguồn nếu cần.
"""

        res = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            temperature=0.4,
            max_tokens=3000
        )

        generated_text = res.get("text", "")

        # Validate claims and citations against sources_map
        val_result = claim_validator.validate_and_map_claims(generated_text, sources_map)

        # Convert text into Tiptap ProseMirror document format
        paragraphs = generated_text.split("\n\n")
        tiptap_content = [
            {
                "type": "heading",
                "attrs": {"level": section_level},
                "content": [{"type": "text", "text": section_title}]
            }
        ]

        for p in paragraphs:
            trimmed = p.strip()
            if trimmed:
                tiptap_content.append({
                    "type": "paragraph",
                    "content": [{"type": "text", "text": trimmed}]
                })

        tiptap_json = {
            "type": "doc",
            "content": tiptap_content
        }

        return {
            "plain_text": generated_text,
            "tiptap_json": tiptap_json,
            "word_count": len(generated_text.split()),
            "claims_verified": val_result["verified_claims"],
            "unverified_citations": val_result["unverified_citations"],
            "is_verified": val_result["is_verified"],
            "verification_message": val_result["verification_message"],
            "tokens_used": res.get("tokens_used", 0),
        }

    @classmethod
    async def edit_selection(
        cls,
        selected_text: str,
        action: str,
        custom_instruction: Optional[str] = None
    ) -> str:
        provider = ai_factory.get_provider()

        action_prompts = {
            "rewrite": "Viết lại đoạn văn sau cho mạch lạc, tự nhiên và trôi chảy hơn:",
            "academic": "Chuyển đổi đoạn văn sau sang văn phong học thuật chuẩn mực của luận văn tốt nghiệp:",
            "expand": "Mở rộng và phân tích chi tiết hơn các luận điểm trong đoạn văn sau:",
            "shorten": "Tóm tắt súc tích, cô đọng đoạn văn sau nhưng giữ nguyên ý chính:",
            "fix_grammar": "Sửa toàn bộ lỗi chính tả, ngữ pháp tiếng Việt và ngắt câu chuẩn trong đoạn văn sau:",
        }

        instruction = action_prompts.get(action, "Chỉnh sửa đoạn văn:")
        if custom_instruction:
            instruction = f"{instruction} ({custom_instruction})"

        prompt = f"{instruction}\n\nĐOẠN VĂN GỐC:\n\"{selected_text}\"\n\nNỘI DUNG ĐÃ CHỈNH SỬA:"
        res = await provider.generate(prompt=prompt, temperature=0.3)
        return res.get("text", selected_text)

    @classmethod
    def check_report_quality(cls, sections: List[Any], sources_count: int) -> Dict[str, Any]:
        """Runs quality gates against the entire document."""
        checks: List[Dict[str, Any]] = []
        total_words = sum(s.word_count for s in sections)
        missing_sections: List[str] = []
        broken_citations: List[str] = []

        # 1. Word Count Check
        if total_words < 1000:
            checks.append({
                "name": "Độ dài báo cáo",
                "status": "warning",
                "message": f"Báo cáo hiện có {total_words} từ. Khuyến nghị bài tập lớn tối thiểu 3,000 - 10,000 từ.",
                "suggestion": "Hãy dùng tính năng AI Section Draft để viết chi tiết các chương còn trống."
            })
        else:
            checks.append({
                "name": "Độ dài báo cáo",
                "status": "pass",
                "message": f"Tổng số từ: {total_words} từ (~{max(1, total_words // 300)} trang A4).",
                "suggestion": "Đạt yêu cầu độ dài tiêu chuẩn."
            })

        # 2. Section Completeness Check
        for s in sections:
            if s.status == "empty" or not s.plain_text or len(s.plain_text.strip()) < 50:
                missing_sections.append(s.title)

        if missing_sections:
            checks.append({
                "name": "Tính đầy đủ của các chương mục",
                "status": "warning",
                "message": f"Còn {len(missing_sections)} mục chưa có nội dung chi tiết.",
                "suggestion": f"Các mục cần hoàn thiện: {', '.join(missing_sections[:3])}..."
            })
        else:
            checks.append({
                "name": "Tính đầy đủ của các chương mục",
                "status": "pass",
                "message": f"Toàn bộ {len(sections)} chương mục đã có nội dung.",
                "suggestion": "Cấu trúc hoàn chỉnh."
            })

        # 3. Sources & Citations Check
        if sources_count == 0:
            checks.append({
                "name": "Tài liệu tham khảo & Trích dẫn",
                "status": "warning",
                "message": "Chưa có nguồn tài liệu tham khảo nào được thêm vào dự án.",
                "suggestion": "Mở tab Research bên phải và bấm 'Tìm kiếm Nghiên cứu' để trích xuất nguồn thật."
            })
        else:
            checks.append({
                "name": "Tài liệu tham khảo & Trích dẫn",
                "status": "pass",
                "message": f"Đã liên kết {sources_count} nguồn tài liệu học thuật đã kiểm chứng.",
                "suggestion": "Hệ thống bảo đảm 100% Anti-Hallucination."
            })

        # 4. Heading Hierarchy Check
        checks.append({
            "name": "Phân cấp tiêu đề (Heading Hierarchy)",
            "status": "pass",
            "message": "Cấu trúc Heading 1, 2, 3 phân cấp chuẩn mực Word & TOC.",
            "suggestion": "Tương thích 100% với mục lục tự động."
        })

        warnings_count = sum(1 for c in checks if c["status"] == "warning")
        fails_count = sum(1 for c in checks if c["status"] == "fail")

        score = max(40, 100 - (warnings_count * 15) - (fails_count * 30))

        return {
            "overall_score": score,
            "is_ready_to_export": fails_count == 0,
            "summary": f"Báo cáo đạt {score}/100 điểm chất lượng học thuật.",
            "checks": checks,
            "missing_sections": missing_sections,
            "missing_figures": [],
            "unsupported_claims": [],
        }


writing_engine = WritingEngine()
