import pytest
from app.services.branding.brand_kit_service import brand_kit_service
from app.services.quality.multi_profile_quality_engine import multi_profile_quality_engine


class MockSection:
    def __init__(self, title: str, plain_text: str):
        self.title = title
        self.plain_text = plain_text


def test_brand_kit_service():
    kit = brand_kit_service.get_effective_brand_kit({"primary_color": "#0052CC"})
    assert kit["primary_color"] == "#0052CC"
    assert kit["secondary_color"] == "#0D9488"
    assert "confidentiality" in kit


def test_multi_profile_quality_engine():
    sections = [
        MockSection("1. Executive Summary", "Báo cáo tóm tắt tình hình hoạt động kinh doanh và lộ trình triển khai 2026 với ngân sách 15 tỷ VND."),
        MockSection("2. Phân tích Thị trường", "Thị phần tăng trưởng 35% trong năm 2026 nhờ mạng lưới phân phối mở rộng."),
        MockSection("3. Đề xuất Kế hoạch Hành động", "Chi tiết lộ trình triển khai theo từng quý và kế hoạch tài chính.")
    ]

    # Evaluate business profile
    res_biz = multi_profile_quality_engine.evaluate(profile="business", sections=sections, sources_count=3)
    assert res_biz["overall_score"] >= 80
    assert res_biz["grade"] in ["A", "B"]

    # Evaluate research profile
    res_res = multi_profile_quality_engine.evaluate(profile="research", sections=sections, sources_count=5)
    assert res_res["overall_score"] >= 80
