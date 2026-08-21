import re
from typing import Any, Dict, List, Optional
from app.services.documents.docx_parser import docx_parser


class DocxTemplateAnalyzer:
    """Smart analyzer for university & enterprise Word templates."""

    PLACEHOLDER_REGEX = re.compile(r"\{\{([a-zA-Z0-9_\-]+)\}\}")

    VI_PATTERNS = {
        "student_name": [r"họ\s*và\s*tên\s*(?:sinh\s*viên|sv)?\s*[:：]\s*(.*)", r"người\s*thực\s*hiện\s*[:：]\s*(.*)"],
        "student_id": [r"(?:mã\s*số\s*sinh\s*viên|mssv|masv)\s*[:：]\s*(.*)"],
        "class_name": [r"lớp\s*[:：]\s*(.*)"],
        "instructor": [r"(?:giảng\s*viên\s*hướng\s*dẫn|gvhd|cán\s*bộ\s*hướng\s*dẫn)\s*[:：]\s*(.*)"],
        "topic_name": [r"(?:tên\s*đề\s*tài|đề\s*tài)\s*[:：]\s*(.*)"],
        "major": [r"(?:ngành|chuyên\s*ngành)\s*[:：]\s*(.*)"],
        "academic_year": [r"(?:năm\s*học|khóa\s*học|niên\s*khóa)\s*[:：]\s*(.*)"],
        "university": [r"(?:trường|đại\s*học|học\s*viện)\s*(.*)"],
    }

    @classmethod
    def analyze_template(cls, file_path: str) -> Dict[str, Any]:
        parsed = docx_parser.extract_document(file_path)
        full_text = parsed["full_text"]
        
        # 1. Detect explicit placeholders like {{student_name}}
        explicit_placeholders = set(cls.PLACEHOLDER_REGEX.findall(full_text))

        # 2. Detect implicit labels in natural Vietnamese
        detected_fields: Dict[str, str] = {}
        for field_name, patterns in cls.VI_PATTERNS.items():
            for pat in patterns:
                match = re.search(pat, full_text, re.IGNORECASE)
                if match:
                    val = match.group(1).strip() if len(match.groups()) > 0 else ""
                    detected_fields[field_name] = val
                    break

        # 3. Extract Styles (Page size, Margins, Font defaults)
        margins = {
            "top": 20,
            "bottom": 20,
            "left": 30,
            "right": 20
        }
        paper = "A4"
        if parsed["sections"]:
            sec = parsed["sections"][0]
            paper = sec.get("page_size", "A4")
            margins = sec.get("margins", margins)

        styles_summary = {
            "paper": paper,
            "margins": margins,
            "default_font": "Times New Roman",
            "font_size": 13,
            "line_spacing": 1.5,
            "headings_count": len(parsed["headings"]),
            "tables_count": parsed["tables_count"],
        }

        return {
            "styles": styles_summary,
            "explicit_placeholders": list(explicit_placeholders),
            "detected_fields": detected_fields,
            "sample_headings": [h["text"] for h in parsed["headings"][:10]],
            "is_valid_template": True,
        }


template_analyzer = DocxTemplateAnalyzer()
