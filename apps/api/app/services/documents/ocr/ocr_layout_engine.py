import io
from typing import Any, Dict, List, Optional, Tuple
from app.services.documents.intelligence.types import (
    BlockType,
    BoundingBox,
    LayoutBlock,
    DocumentPage,
)


class AdvancedOCRLayoutEngine:
    """
    Advanced Conditional OCR & Intelligent Layout Reconstruction Engine (Phase U29).
    Detects presence of native text layer; invokes OCR only when missing; reconstructs tables and reading order.
    """

    @classmethod
    def has_native_text_layer(cls, file_bytes: bytes, filename: str) -> bool:
        """Determines if a document already possesses a clean digital text layer."""
        ext = filename.lower().split(".")[-1]
        if ext in ["txt", "md", "csv", "docx"]:
            return True

        if ext == "pdf":
            try:
                import fitz
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                total_text_len = sum(len(page.get_text("text").strip()) for page in doc)
                return total_text_len > 50  # Contains substantial native text
            except Exception:
                return False

        return False  # Images, scans, and empty PDFs require OCR

    @classmethod
    def reconstruct_layout_from_ocr(
        cls,
        ocr_blocks: List[Dict[str, Any]],
        page_number: int = 1,
        page_width: float = 800.0,
        page_height: float = 1000.0
    ) -> List[LayoutBlock]:
        """
        Sorts blocks by top-to-bottom, left-to-right reading order,
        flags low-confidence items for user review, and identifies table grids.
        """
        # Sort by Y coordinate first, then X coordinate
        sorted_raw = sorted(ocr_blocks, key=lambda b: (b.get("y", 0.0), b.get("x", 0.0)))
        reconstructed: List[LayoutBlock] = []

        for idx, item in enumerate(sorted_raw):
            confidence = float(item.get("confidence", 0.95))
            text = str(item.get("text", "")).strip()
            x = float(item.get("x", 0.0))
            y = float(item.get("y", 0.0))
            w = float(item.get("width", 1.0))
            h = float(item.get("height", 0.1))

            # Determine block type
            is_table_row = item.get("is_table_cell", False) or ("|" in text and len(text.split("|")) >= 2)
            if is_table_row:
                b_type = BlockType.TABLE
            elif len(text) < 80 and (text.isupper() or text.startswith("#")):
                b_type = BlockType.HEADING
            else:
                b_type = BlockType.PARAGRAPH

            # Flag review if confidence < 0.75
            needs_rev = confidence < 0.75

            reconstructed.append(
                LayoutBlock(
                    block_id=f"ocr_p{page_number}_b{idx+1}",
                    block_type=b_type,
                    page_number=page_number,
                    reading_order=idx + 1,
                    bounding_box=BoundingBox(x=x, y=y, width=w, height=h),
                    text_content=text,
                    confidence=round(confidence, 3),
                    needs_review=needs_rev,
                    style={"font_size": item.get("font_size", 12)},
                    structured_data=item.get("structured_data"),
                )
            )

        return reconstructed

    @classmethod
    def reconstruct_table_grid(
        cls,
        cell_blocks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Reconstructs 2D grid matrix of rows and columns from OCR bounding boxes."""
        # Group cells by similar Y coordinates (rows)
        rows_map: Dict[int, List[Dict[str, Any]]] = {}
        for cell in cell_blocks:
            y_approx = int(cell.get("y", 0.0) * 100)  # bucket by row height
            matched_key = None
            for k in rows_map.keys():
                if abs(k - y_approx) <= 3:  # tolerance
                    matched_key = k
                    break
            if matched_key is not None:
                rows_map[matched_key].append(cell)
            else:
                rows_map[y_approx] = [cell]

        # Sort rows top-to-bottom and cells left-to-right
        sorted_rows_keys = sorted(rows_map.keys())
        grid: List[List[str]] = []
        for rk in sorted_rows_keys:
            cells_in_row = sorted(rows_map[rk], key=lambda c: c.get("x", 0.0))
            grid.append([c.get("text", "").strip() for c in cells_in_row])

        return {
            "num_rows": len(grid),
            "num_cols": max((len(r) for r in grid), default=0),
            "grid_matrix": grid,
            "has_header": len(grid) > 1,
        }


ocr_layout_engine = AdvancedOCRLayoutEngine()
