from typing import Any, Dict, Optional


class BrandKitService:
    """Enterprise Brand Kit Manager for document styling, headers, footers and color palettes."""

    DEFAULT_BRAND_KIT = {
        "primary_color": "#1E3A8A",  # Deep Navy
        "secondary_color": "#0D9488",  # Teal
        "accent_color": "#F59E0B",  # Amber
        "font_family_heading": "Inter",
        "font_family_body": "Inter",
        "logo_url": None,
        "header_text": "DOANH NGHIỆP CỔ PHẦN • BÁO CÁO CHIẾN LƯỢC",
        "footer_text": "BẢO MẬT & NỘI BỘ • TRANG {{page}} / {{totalPages}}",
        "confidentiality": "STRICTLY CONFIDENTIAL",
    }

    @classmethod
    def get_effective_brand_kit(cls, custom_kit: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {**cls.DEFAULT_BRAND_KIT, **(custom_kit or {})}


brand_kit_service = BrandKitService()
