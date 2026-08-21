import os
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.services.citations.citation_formatter import citation_formatter


class PDFExporter:
    """PDF Exporter for report documents."""

    @classmethod
    def generate_pdf(
        cls,
        report_title: str,
        topic_details: Dict[str, Any],
        sections: List[Any],
        sources: List[Any],
        citation_style: str = "IEEE",
    ) -> str:
        # Generate standalone HTML document with A4 print CSS
        html_lines = [
            "<!DOCTYPE html>",
            "<html lang='vi'>",
            "<head>",
            "<meta charset='utf-8'/>",
            f"<title>{report_title}</title>",
            "<style>",
            "@page { size: A4; margin: 20mm 20mm 20mm 30mm; }",
            "body { font-family: 'Times New Roman', serif; font-size: 13pt; line-height: 1.5; color: #000; }",
            "h1 { font-size: 14pt; text-transform: uppercase; font-weight: bold; margin-top: 24pt; margin-bottom: 12pt; page-break-after: avoid; }",
            "h2 { font-size: 13pt; font-weight: bold; margin-top: 18pt; margin-bottom: 8pt; page-break-after: avoid; }",
            "h3 { font-size: 13pt; font-style: italic; font-weight: bold; margin-top: 14pt; margin-bottom: 6pt; page-break-after: avoid; }",
            "p { text-align: justify; text-indent: 1.27cm; margin-bottom: 6pt; }",
            ".cover { height: 100vh; display: flex; flex-direction: column; justify-content: space-between; text-align: center; page-break-after: always; }",
            ".bib-entry { padding-left: 1.27cm; text-indent: -1.27cm; margin-bottom: 6pt; font-size: 12pt; }",
            "</style>",
            "</head>",
            "<body>",
        ]

        # Cover Page
        uni = topic_details.get("university", "TRƯỜNG ĐẠI HỌC BÁCH KHOA HÀ NỘI")
        student = topic_details.get("student_name", "Nguyễn Văn A")
        sid = topic_details.get("student_id", "20210001")
        instructor = topic_details.get("instructor", "TS. Nguyễn Văn B")

        html_lines.append(f"<div class='cover'>")
        html_lines.append(f"<h2>{uni.upper()}</h2>")
        html_lines.append(f"<div style='margin-top: 80px;'><h1>ĐỀ TÀI:<br/>{report_title.upper()}</h1></div>")
        html_lines.append(f"<div style='text-align: left; margin: 0 auto; width: 60%; font-size: 12pt;'>")
        html_lines.append(f"<p><b>Sinh viên:</b> {student} (MSSV: {sid})</p>")
        html_lines.append(f"<p><b>Giảng viên hướng dẫn:</b> {instructor}</p>")
        html_lines.append(f"</div>")
        html_lines.append(f"<p style='text-align:center;'>Hà Nội, 2026</p>")
        html_lines.append(f"</div>")

        # Sections
        for sec in sections:
            tag = "h1" if sec.level == 1 else "h2" if sec.level == 2 else "h3"
            html_lines.append(f"<{tag}>{sec.title}</{tag}>")
            paragraphs = (sec.plain_text or "").split("\n\n")
            for p in paragraphs:
                if p.strip() and p.strip() != sec.title.strip():
                    html_lines.append(f"<p>{p.strip()}</p>")

        # References
        if sources:
            html_lines.append("<div style='page-break-before: always;'>")
            html_lines.append("<h1>TÀI LIỆU THAM KHẢO</h1>")
            for idx, src in enumerate(sources, 1):
                src_dict = {
                    "title": src.title if hasattr(src, "title") else src.get("title"),
                    "authors": src.authors if hasattr(src, "authors") else src.get("authors"),
                    "publisher": src.publisher if hasattr(src, "publisher") else src.get("publisher"),
                    "published_date": src.published_date if hasattr(src, "published_date") else src.get("published_date"),
                    "url": src.url if hasattr(src, "url") else src.get("url"),
                }
                entry = citation_formatter.format_bibliography_entry(idx, src_dict, style=citation_style)
                html_lines.append(f"<div class='bib-entry'>{entry}</div>")
            html_lines.append("</div>")

        html_lines.append("</body></html>")

        # Save HTML
        filename = f"report_{os.urandom(6).hex()}.html"
        out_path = settings.EXPORT_DIR / filename
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(html_lines))

        return str(out_path)


pdf_exporter = PDFExporter()
