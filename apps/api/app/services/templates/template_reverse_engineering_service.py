import json
import re
from typing import Any, Dict, List, Optional
from app.services.ai.provider_factory import ai_factory
from app.services.documents.docx_parser import docx_parser
from app.services.documents.pdf_parser import pdf_parser


class TemplateReverseEngineeringService:
    """
    AI Template Reverse Engineering Engine.
    Dissects uploaded Word (.docx) or PDF templates into structured schema:
    - Fixed boilerplate content vs Replaceable dynamic content
    - Explicit & implicit custom fields (placeholders)
    - Required vs Optional sections
    - Repeating blocks & template instructions
    """

    @classmethod
    async def reverse_engineer_docx(cls, file_path: str) -> Dict[str, Any]:
        # 1. Parse raw DOCX structure
        parsed_doc = docx_parser.extract_document(file_path)

        # 2. Extract paragraph previews and table schemas
        paragraphs = parsed_doc.get("paragraphs", [])
        sample_paragraphs = [p["text"] for p in paragraphs if len(p.get("text", "").strip()) > 5][:40]
        headings = [h["text"] for h in parsed_doc.get("headings", [])]

        # 3. Detect placeholders like {{variable}} or [[variable]]
        explicit_placeholders = []
        for p_text in sample_paragraphs:
            found = re.findall(r"\{\{([a-zA-Z0-9_\-]+)\}\}", p_text)
            explicit_placeholders.extend(found)
        explicit_placeholders = list(set(explicit_placeholders))

        sec_0 = parsed_doc.get("sections", [{}])[0] if parsed_doc.get("sections") else {}
        margins = sec_0.get("margins", {"top": 25, "bottom": 25, "left": 25, "right": 25})

        # 4. Use AI to reverse engineer the document schema
        provider = ai_factory.get_provider()
        system_prompt = (
            "Bạn là một Principal Document Automation Engineer & Template Architect. "
            "Nhiệm vụ của bạn là phân tích cấu trúc của file tài liệu mẫu (DOCX/PDF), "
            "phân biệt chính xác: "
            "1. Nội dung cố định cần giữ nguyên (fixed_content) vs nội dung mẫu cần thay thế (replaceable_content), "
            "2. Danh sách trường dữ liệu động (fields: [{key, label, type, required}]), "
            "3. Danh sách các section/chương mục (sections: [{title, level, is_required}]), "
            "4. Lời hướng dẫn điền trong mẫu (instructions), "
            "5. Các khối lặp lại (repeating_blocks). "
            "Bắt buộc trả về kết quả dưới định dạng JSON với các khóa: "
            "document_type, title, sections, fields, styles, fixed_content, replaceable_content, instructions, repeating_blocks."
        )

        user_prompt = f"""
CẤU TRÚC VĂN BẢN MẪU:
- Tiêu đề & Headings tìm thấy: {headings}
- Biến placeholder tìm thấy: {explicit_placeholders}
- Các đoạn văn mẫu:
{json.dumps(sample_paragraphs[:20], ensure_ascii=False, indent=2)}

- Kiểu trang & Lề (mm): Top={margins.get('top')}, Left={margins.get('left')}, Right={margins.get('right')}, Bottom={margins.get('bottom')}

Hãy phân tích ngược và sinh JSON Template Schema hoàn chỉnh.
"""

        res = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json",
            temperature=0.3
        )

        raw_text = res.get("text", "{}")
        try:
            data = json.loads(raw_text)
        except Exception:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        # Merge physical parsed styles
        styles = data.get("styles", {})
        styles["paper"] = sec_0.get("page_size", "A4")
        styles["margins"] = margins
        styles["font_family"] = styles.get("font_family", "Inter")
        styles["font_size"] = styles.get("font_size", 12)

        return {
            "document_type": data.get("document_type", "business_report"),
            "title": data.get("title", "Mẫu Báo Cáo Tùy Chỉnh"),
            "sections": data.get("sections", []),
            "fields": data.get("fields", []),
            "styles": styles,
            "fixed_content": data.get("fixed_content", []),
            "replaceable_content": data.get("replaceable_content", []),
            "instructions": data.get("instructions", []),
            "repeating_blocks": data.get("repeating_blocks", []),
            "explicit_placeholders": explicit_placeholders,
        }

    @classmethod
    async def reverse_engineer_pdf(cls, file_path: str) -> Dict[str, Any]:
        parsed_pdf = pdf_parser.parse(file_path)
        sample_text = parsed_pdf.content_text[:3000]

        provider = ai_factory.get_provider()
        system_prompt = (
            "Bạn là một Principal Document Automation Engineer. "
            "Nhiệm vụ của bạn là phân tích tài liệu PDF mẫu để trích xuất cấu trúc schema: "
            "sections, fields, styles, fixed_content, replaceable_content. "
            "Bắt buộc trả về JSON hợp lệ."
        )

        res = await provider.generate(
            prompt=f"NỘI DUNG PDF MẪU:\n{sample_text}\n\nHãy phân tích và trả về Template Schema JSON.",
            system_prompt=system_prompt,
            response_format="json",
            temperature=0.3
        )

        try:
            data = json.loads(res.get("text", "{}"))
        except Exception:
            clean = res.get("text", "{}").replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        return {
            "document_type": data.get("document_type", "business_report"),
            "title": data.get("title", "Mẫu Tài Liệu PDF"),
            "sections": data.get("sections", []),
            "fields": data.get("fields", []),
            "styles": {
                "paper": "A4",
                "margins": {"top": 25, "bottom": 25, "left": 25, "right": 25},
                "font_family": "Times New Roman",
                "font_size": 12,
            },
            "fixed_content": data.get("fixed_content", []),
            "replaceable_content": data.get("replaceable_content", []),
            "instructions": data.get("instructions", []),
            "repeating_blocks": data.get("repeating_blocks", []),
        }


template_reverse_engineer = TemplateReverseEngineeringService()
