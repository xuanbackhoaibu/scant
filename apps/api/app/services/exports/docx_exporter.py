import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import docx
from docx.shared import Inches, Pt, Mm, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from app.core.config import settings
from app.services.citations.citation_formatter import citation_formatter


class DocxExporter:
    """High-fidelity DOCX Exporter generating editable academic documents conforming to university standards."""

    @classmethod
    def generate_docx(
        cls,
        report_title: str,
        topic_details: Dict[str, Any],
        sections: List[Any],
        sources: List[Any],
        document_settings: Optional[Dict[str, Any]] = None,
        include_cover: bool = True,
        include_toc: bool = True,
        include_references: bool = True,
        citation_style: str = "IEEE",
    ) -> str:
        doc = docx.Document()

        # 1. Configure Standard A4 Page Setup & Academic Margins
        # Vietnam Academic Standard: Left 30mm, Right 20mm, Top 20mm, Bottom 20mm
        section = doc.sections[0]
        section.page_width = Mm(210)
        section.page_height = Mm(297)
        section.top_margin = Mm(20)
        section.bottom_margin = Mm(20)
        section.left_margin = Mm(30)
        section.right_margin = Mm(20)

        # Set Normal Style Font to Times New Roman 13pt
        style_normal = doc.styles["Normal"]
        style_normal.font.name = "Times New Roman"
        style_normal.font.size = Pt(13)
        style_normal.font.color.rgb = RGBColor(0, 0, 0)
        style_normal.paragraph_format.line_spacing = 1.5
        style_normal.paragraph_format.space_after = Pt(6)

        # 2. Cover Page
        if include_cover:
            cls._build_cover_page(doc, report_title, topic_details)
            doc.add_page_break()

        # 3. Table of Contents Header
        if include_toc:
            toc_heading = doc.add_paragraph()
            toc_heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = toc_heading.add_run("MỤC LỤC")
            run.bold = True
            run.font.size = Pt(14)
            run.font.name = "Times New Roman"

            # Add structured TOC items
            for sec in sections:
                p_toc = doc.add_paragraph()
                p_toc.paragraph_format.line_spacing = 1.2
                p_toc.paragraph_format.space_after = Pt(2)
                indent = (sec.level - 1) * 0.3
                p_toc.paragraph_format.left_indent = Inches(indent)

                r_title = p_toc.add_run(sec.title)
                r_title.font.name = "Times New Roman"
                r_title.font.size = Pt(12)
                if sec.level == 1:
                    r_title.bold = True

            doc.add_page_break()

        # 4. Report Sections Content
        for sec in sections:
            # Heading formatting based on level
            p_head = doc.add_paragraph()
            p_head.paragraph_format.space_before = Pt(14)
            p_head.paragraph_format.space_after = Pt(8)
            p_head.paragraph_format.keep_with_next = True

            run_head = p_head.add_run(sec.title)
            run_head.font.name = "Times New Roman"

            if sec.level == 1:
                run_head.bold = True
                run_head.font.size = Pt(14)
                if "CHƯƠNG" in sec.title.upper():
                    p_head.alignment = WD_ALIGN_PARAGRAPH.LEFT
            elif sec.level == 2:
                run_head.bold = True
                run_head.font.size = Pt(13)
            else:
                run_head.bold = True
                run_head.italic = True
                run_head.font.size = Pt(13)

            # Paragraphs body
            body_text = sec.plain_text or ""
            # Strip the heading title if duplicated in plain_text
            lines = body_text.splitlines()
            if lines and lines[0].strip() == sec.title.strip():
                lines = lines[1:]

            cleaned_body = "\n".join(lines).strip()
            if cleaned_body:
                paragraphs = cleaned_body.split("\n\n")
                for p_text in paragraphs:
                    trimmed = p_text.strip()
                    if not trimmed:
                        continue
                    p_body = doc.add_paragraph()
                    p_body.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                    p_body.paragraph_format.line_spacing = 1.5
                    p_body.paragraph_format.first_line_indent = Inches(0.5)
                    p_body.paragraph_format.space_after = Pt(6)

                    r_body = p_body.add_run(trimmed)
                    r_body.font.name = "Times New Roman"
                    r_body.font.size = Pt(13)

        # 5. References Section (Tài liệu tham khảo)
        if include_references and sources:
            doc.add_page_break()
            p_ref_head = doc.add_paragraph()
            p_ref_head.paragraph_format.space_before = Pt(14)
            p_ref_head.paragraph_format.space_after = Pt(8)
            r_ref_head = p_ref_head.add_run("TÀI LIỆU THAM KHẢO")
            r_ref_head.bold = True
            r_ref_head.font.size = Pt(14)
            r_ref_head.font.name = "Times New Roman"

            for idx, src in enumerate(sources, 1):
                src_dict = {
                    "title": src.title if hasattr(src, "title") else src.get("title"),
                    "authors": src.authors if hasattr(src, "authors") else src.get("authors"),
                    "publisher": src.publisher if hasattr(src, "publisher") else src.get("publisher"),
                    "published_date": src.published_date if hasattr(src, "published_date") else src.get("published_date"),
                    "url": src.url if hasattr(src, "url") else src.get("url"),
                }
                entry_text = citation_formatter.format_bibliography_entry(idx, src_dict, style=citation_style)
                
                p_entry = doc.add_paragraph()
                p_entry.alignment = WD_ALIGN_PARAGRAPH.LEFT
                p_entry.paragraph_format.line_spacing = 1.3
                p_entry.paragraph_format.space_after = Pt(4)
                p_entry.paragraph_format.left_indent = Inches(0.4)
                p_entry.paragraph_format.first_line_indent = Inches(-0.4)

                r_entry = p_entry.add_run(entry_text)
                r_entry.font.name = "Times New Roman"
                r_entry.font.size = Pt(12)

        # Save to disk
        filename = f"report_{os.urandom(6).hex()}.docx"
        out_path = settings.EXPORT_DIR / filename
        doc.save(str(out_path))

        return str(out_path)

    @classmethod
    def _build_cover_page(cls, doc: docx.Document, title: str, topic: Dict[str, Any]) -> None:
        university = topic.get("university") or "TRƯỜNG ĐẠI HỌC BÁCH KHOA HÀ NỘI"
        major = topic.get("major") or "VIỆN CÔNG NGHỆ THÔNG TIN VÀ TRUYỀN THÔNG"
        subject = topic.get("subject") or "BÁO CÁO BÀI TẬP LỚN / ĐỒ ÁN MÔN HỌC"
        student_name = topic.get("student_name") or "Nguyễn Văn A"
        student_id = topic.get("student_id") or "20210001"
        class_name = topic.get("class_name") or "K66-CNTT-01"
        instructor = topic.get("instructor") or "TS. Nguyễn Văn B"
        academic_year = topic.get("academic_year") or "Hà Nội, 2026"

        # University Header
        p_uni = doc.add_paragraph()
        p_uni.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_uni.paragraph_format.space_after = Pt(2)
        r_uni = p_uni.add_run(university.upper())
        r_uni.bold = True
        r_uni.font.size = Pt(13)
        r_uni.font.name = "Times New Roman"

        p_maj = doc.add_paragraph()
        p_maj.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_maj.paragraph_format.space_after = Pt(36)
        r_maj = p_maj.add_run(major.upper())
        r_maj.bold = True
        r_maj.font.size = Pt(12)
        r_maj.font.name = "Times New Roman"

        # Subject / Subtitle
        p_sub = doc.add_paragraph()
        p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_sub.paragraph_format.space_after = Pt(18)
        r_sub = p_sub.add_run(subject.upper())
        r_sub.bold = True
        r_sub.font.size = Pt(14)
        r_sub.font.name = "Times New Roman"

        # Report Topic Title Box
        p_title = doc.add_paragraph()
        p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_title.paragraph_format.space_after = Pt(72)
        r_title_label = p_title.add_run("ĐỀ TÀI:\n")
        r_title_label.bold = True
        r_title_label.font.size = Pt(13)
        r_title_label.font.name = "Times New Roman"

        r_title = p_title.add_run(title.upper())
        r_title.bold = True
        r_title.font.size = Pt(16)
        r_title.font.name = "Times New Roman"

        # Student & Instructor Table
        table = doc.add_table(rows=4, cols=2)
        table.alignment = WD_TABLE_ALIGNMENT.CENTER
        
        info_rows = [
            ("Sinh viên thực hiện:", f"{student_name} - MSSV: {student_id}"),
            ("Lớp học phần:", class_name),
            ("Chuyên ngành:", major),
            ("Giảng viên hướng dẫn:", instructor),
        ]

        for i, (label, val) in enumerate(info_rows):
            row = table.rows[i]
            # Left cell (label)
            p_lbl = row.cells[0].paragraphs[0]
            p_lbl.paragraph_format.line_spacing = 1.3
            p_lbl.paragraph_format.space_after = Pt(4)
            r_l = p_lbl.add_run(label)
            r_l.font.name = "Times New Roman"
            r_l.font.size = Pt(12)
            r_l.bold = True

            # Right cell (value)
            p_v = row.cells[1].paragraphs[0]
            p_v.paragraph_format.line_spacing = 1.3
            p_v.paragraph_format.space_after = Pt(4)
            r_v = p_v.add_run(val)
            r_v.font.name = "Times New Roman"
            r_v.font.size = Pt(12)

        # Footer Date
        p_footer = doc.add_paragraph()
        p_footer.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_footer.paragraph_format.space_before = Pt(72)
        r_date = p_footer.add_run(academic_year)
        r_date.bold = True
        r_date.font.size = Pt(12)
        r_date.font.name = "Times New Roman"


docx_exporter = DocxExporter()
