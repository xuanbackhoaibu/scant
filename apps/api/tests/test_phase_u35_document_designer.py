import pytest
from app.services.designer.document_designer_engine import (
    document_designer_engine,
    DESIGN_PRESETS,
)


def test_design_presets_library():
    assert len(DESIGN_PRESETS) == 7
    expected_keys = {"corporate", "consulting", "minimal", "technical", "financial", "research", "modern"}
    assert set(DESIGN_PRESETS.keys()) == expected_keys

    # Check properties
    for k, preset in DESIGN_PRESETS.items():
        assert len(preset.name) > 0
        assert preset.primary_color.startswith("#")
        assert len(preset.chart_palette) >= 3


def test_brand_kit_override_merging():
    base_preset = document_designer_engine.get_preset("corporate")
    assert base_preset.primary_color == "#0f172a"

    custom_brand_kit = {
        "primary_color": "#ff5722",
        "accent_color": "#ff9800",
        "primary_font": "Plus Jakarta Sans",
        "heading_font": "Plus Jakarta Sans",
    }

    merged = document_designer_engine.apply_brand_kit_override(base_preset, custom_brand_kit)
    assert merged.primary_color == "#ff5722"
    assert merged.accent_color == "#ff9800"
    assert merged.primary_font == "Plus Jakarta Sans"
    # Preserved un-overridden properties
    assert merged.table_style == "striped"


@pytest.mark.asyncio
async def test_ai_design_recommendation():
    res = await document_designer_engine.recommend_design_for_report(
        report_title="Báo cáo Kiểm toán Quỹ Đầu tư Công nghệ 2026",
        user_intent="Thiết kế chuẩn mực số liệu kiểm toán tài chính chính xác",
        brand_kit={"primary_color": "#064e3b"}
    )
    assert "recommended_preset_key" in res
    assert "design_specs" in res
    assert res["design_specs"]["primary_color"] == "#064e3b"
    assert res["brand_kit_applied"] is True
