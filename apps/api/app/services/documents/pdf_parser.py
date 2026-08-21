import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import pymupdf as fitz


class PDFParser:
    """High-performance PDF parser for requirements, rubrics, and academic references."""

    @staticmethod
    def extract_text_and_metadata(file_path: str) -> Dict[str, Any]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        doc = fitz.open(file_path)
        pages_text: List[str] = []
        full_text_list: List[str] = []
        total_pages = len(doc)
        toc = doc.get_toc()

        for page_num in range(total_pages):
            page = doc[page_num]
            text = page.get_text("text")
            pages_text.append(text)
            full_text_list.append(f"--- Trang {page_num + 1} ---\n{text}")

        full_text = "\n".join(full_text_list)
        metadata = doc.metadata or {}

        # Rough token count estimate (1 token ~ 4 chars for EN/VI)
        token_count = len(full_text) // 4

        doc.close()

        return {
            "total_pages": total_pages,
            "metadata": metadata,
            "toc": toc,
            "pages_text": pages_text,
            "full_text": full_text,
            "token_count": token_count,
        }

    @staticmethod
    def extract_requirements_summary(full_text: str) -> Dict[str, Any]:
        """Heuristic extractor for academic requirements and rubric sections."""
        lines = full_text.splitlines()
        objectives: List[str] = []
        requirements: List[str] = []
        rubric_items: List[str] = []

        current_section = None
        for line in lines:
            trimmed = line.strip()
            if not trimmed:
                continue

            lower = trimmed.lower()
            if any(k in lower for k in ["mục tiêu", "muc tieu", "objective", "yêu cầu chung"]):
                current_section = "objectives"
                continue
            elif any(k in lower for k in ["chức năng", "yêu cầu", "yeu cau", "functional"]):
                current_section = "requirements"
                continue
            elif any(k in lower for k in ["tiêu chí", "tieu chi", "rubric", "thang điểm", "đánh giá"]):
                current_section = "rubric"
                continue

            if current_section == "objectives" and len(objectives) < 10:
                objectives.append(trimmed)
            elif current_section == "requirements" and len(requirements) < 20:
                requirements.append(trimmed)
            elif current_section == "rubric" and len(rubric_items) < 15:
                rubric_items.append(trimmed)

        return {
            "detected_objectives": objectives,
            "detected_requirements": requirements,
            "detected_rubrics": rubric_items,
        }


pdf_parser = PDFParser()
