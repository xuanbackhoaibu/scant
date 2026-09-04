from pathlib import Path
from types import SimpleNamespace

import docx
from docx.enum.text import WD_ALIGN_PARAGRAPH

from app.services.editor.writing_engine import writing_engine
from app.services.exports.docx_exporter import DocxExporter


def test_generated_tiptap_body_paragraphs_default_to_justify():
    content = writing_engine._text_to_tiptap_json(
        "CHƯƠNG 1: TỔNG QUAN\n\nĐây là đoạn nội dung thân bài cần căn đều hai bên.",
        1,
    )

    paragraph = next(node for node in content["content"] if node["type"] == "paragraph")
    assert paragraph["attrs"]["textAlign"] == "justify"


def test_plain_docx_export_justifies_body_paragraphs():
    section = SimpleNamespace(
        title="CHƯƠNG 1: TỔNG QUAN",
        level=1,
        plain_text="CHƯƠNG 1: TỔNG QUAN\n\nĐây là đoạn nội dung thân bài cần căn đều hai bên.",
        content_json=None,
        word_count=12,
    )

    out_path = DocxExporter.generate_docx(
        report_title="Báo cáo căn lề",
        topic_details={},
        sections=[section],
        sources=[],
        include_cover=False,
        include_toc=False,
        include_references=False,
    )

    generated = docx.Document(out_path)
    body_paragraph = next(p for p in generated.paragraphs if p.text.startswith("Đây là đoạn"))
    assert body_paragraph.alignment == WD_ALIGN_PARAGRAPH.JUSTIFY

    Path(out_path).unlink(missing_ok=True)
