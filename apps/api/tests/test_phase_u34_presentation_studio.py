import pytest
from app.services.presentation.presentation_engine import presentation_engine, PresentationDeck


@pytest.mark.asyncio
async def test_report_to_presentation_transformation():
    report_title = "Báo Cáo Kết Quả Kinh Doanh & Định Hướng Chiến Lược 2026"
    report_body = """
    Doanh thu thuần hợp nhất đạt 450 tỷ VNĐ, tăng 24% so với năm trước.
    Lợi nhuận gộp đạt 173 tỷ VNĐ. Thị phần toàn quốc tăng thêm 3.5 điểm phần trăm.
    Kế hoạch quý 4 tập trung vào chuyển đổi số và tự động hóa chuỗi cung ứng.
    """

    deck = await presentation_engine.generate_presentation_from_report(
        report_title=report_title,
        report_content=report_body,
        target_slides_count=3,
        theme="corporate_clean"
    )

    assert isinstance(deck, PresentationDeck)
    assert deck.title == report_title
    assert deck.total_slides >= 3
    assert len(deck.slides) >= 3

    for slide in deck.slides:
        assert len(slide.title) > 0
        assert len(slide.key_message) > 0
        assert len(slide.bullet_points) >= 2
        assert len(slide.speaker_notes) > 0
        assert slide.visual_suggestion in ["metric_cards", "chart", "split_column", "quote"]
