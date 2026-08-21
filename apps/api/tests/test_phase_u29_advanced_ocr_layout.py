import pytest
from app.services.documents.ocr.ocr_layout_engine import ocr_layout_engine
from app.services.documents.intelligence.types import BlockType


def test_native_text_layer_detection():
    # 1. Native text file
    assert ocr_layout_engine.has_native_text_layer(b"Hello report world", "document.txt") is True
    assert ocr_layout_engine.has_native_text_layer(b"mock docx", "financial.docx") is True

    # 2. Image/scan requiring OCR
    assert ocr_layout_engine.has_native_text_layer(b"\x89PNG", "scanned_receipt.png") is False
    assert ocr_layout_engine.has_native_text_layer(b"\xff\xd8\xff", "invoice_photo.jpg") is False


def test_ocr_layout_reconstruction_and_confidence_review():
    raw_ocr_blocks = [
        {"x": 0.1, "y": 0.4, "text": "Đoạn văn phân tích thị trường tài chính", "confidence": 0.96},
        {"x": 0.1, "y": 0.1, "text": "BÁO CÁO CHIẾN LƯỢC NĂM 2026", "confidence": 0.99},
        {"x": 0.1, "y": 0.8, "text": "Chữ mờ khó đọc do bản quét", "confidence": 0.58},  # Low confidence
    ]

    reconstructed = ocr_layout_engine.reconstruct_layout_from_ocr(
        ocr_blocks=raw_ocr_blocks,
        page_number=1
    )

    # 1. Reading order sorted top-to-bottom
    assert len(reconstructed) == 3
    assert reconstructed[0].text_content == "BÁO CÁO CHIẾN LƯỢC NĂM 2026"
    assert reconstructed[0].block_type == BlockType.HEADING
    assert reconstructed[0].needs_review is False

    assert reconstructed[1].text_content == "Đoạn văn phân tích thị trường tài chính"
    assert reconstructed[1].block_type == BlockType.PARAGRAPH

    # 2. Low-confidence block flagged for review
    assert reconstructed[2].text_content == "Chữ mờ khó đọc do bản quét"
    assert reconstructed[2].confidence == 0.58
    assert reconstructed[2].needs_review is True


def test_ocr_table_grid_reconstruction():
    # Disordered OCR table cells with spatial coordinates
    cell_blocks = [
        {"x": 0.5, "y": 0.1, "text": "Q1 2026"},
        {"x": 0.1, "y": 0.1, "text": "Chỉ tiêu"},
        {"x": 0.1, "y": 0.25, "text": "Doanh thu"},
        {"x": 0.5, "y": 0.25, "text": "250 Tỷ"},
        {"x": 0.1, "y": 0.4, "text": "Lợi nhuận"},
        {"x": 0.5, "y": 0.4, "text": "45 Tỷ"},
    ]

    grid = ocr_layout_engine.reconstruct_table_grid(cell_blocks)
    assert grid["num_rows"] == 3
    assert grid["num_cols"] == 2
    assert grid["grid_matrix"][0] == ["Chỉ tiêu", "Q1 2026"]
    assert grid["grid_matrix"][1] == ["Doanh thu", "250 Tỷ"]
    assert grid["grid_matrix"][2] == ["Lợi nhuận", "45 Tỷ"]
