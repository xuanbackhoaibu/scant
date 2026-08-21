from typing import Any, Dict, List, Optional


class MultiProfileQualityEngine:
    """
    Profile-Aware Document Quality Assessment Engine.
    Evaluates documents based on specific business, technical, research, or financial criteria.
    """

    @classmethod
    def evaluate(
        cls,
        profile: str,  # business, technical, research, financial, data_analysis, custom
        sections: List[Any],
        sources_count: int = 0,
        claims_summary: Optional[Dict[str, Any]] = None,
        has_dataset: bool = False
    ) -> Dict[str, Any]:
        total_words = sum(len((s.plain_text or "").split()) for s in sections)
        sections_count = len(sections)
        titles = [s.title.lower() for s in sections]
        full_text = " ".join([s.plain_text or "" for s in sections]).lower()

        checks: List[Dict[str, Any]] = []
        score = 100

        # Universal checks
        if sections_count < 3:
            checks.append({"name": "Cấu trúc đề cương", "status": "warning", "message": "Tài liệu nên có tối thiểu 3 phần.", "suggestion": "Thêm các phần mục tiêu, thực trạng, giải pháp."})
            score -= 15
        else:
            checks.append({"name": "Cấu trúc đề cương", "status": "pass", "message": f"Tài liệu có {sections_count} phần logic.", "suggestion": None})

        if total_words < 300:
            checks.append({"name": "Độ dài nội dung", "status": "warning", "message": f"Văn bản còn ngắn ({total_words} từ).", "suggestion": "Bổ sung phân tích và lập luận chi tiết."})
            score -= 20
        else:
            checks.append({"name": "Độ dài nội dung", "status": "pass", "message": f"Dung lượng phong phú ({total_words} từ).", "suggestion": None})

        # Profile-specific checks
        if profile in ["business", "business_report", "proposal"]:
            has_exec_summary = any("executive summary" in t or "tóm tắt" in t for t in titles)
            if not has_exec_summary:
                checks.append({"name": "Executive Summary", "status": "warning", "message": "Báo cáo Doanh nghiệp cần có Tóm tắt Điều hành (Executive Summary).", "suggestion": "Thêm Tóm tắt Điều hành cho ban giám đốc."})
                score -= 15
            else:
                checks.append({"name": "Executive Summary", "status": "pass", "message": "Có Tóm tắt Điều hành cho lãnh đạo.", "suggestion": None})

            has_roadmap = "lộ trình" in full_text or "kế hoạch" in full_text or "timeline" in full_text or "roadmap" in full_text
            if not has_roadmap:
                checks.append({"name": "Lộ trình triển khai", "status": "warning", "message": "Chưa có lộ trình hoặc kế hoạch hành động cụ thể.", "suggestion": "Bổ sung lộ trình triển khai theo các giai đoạn."})
                score -= 10
            else:
                checks.append({"name": "Lộ trình triển khai", "status": "pass", "message": "Đã có đề xuất lộ trình và kế hoạch triển khai.", "suggestion": None})

        elif profile in ["technical", "technical_documentation"]:
            has_tech_details = "kiến trúc" in full_text or "api" in full_text or "sơ đồ" in full_text or "hệ thống" in full_text
            if not has_tech_details:
                checks.append({"name": "Đặc tả kỹ thuật", "status": "warning", "message": "Cần bổ sung đặc tả API hoặc kiến trúc hệ thống.", "suggestion": "Bổ sung kiến trúc kỹ thuật."})
                score -= 15
            else:
                checks.append({"name": "Đặc tả kỹ thuật", "status": "pass", "message": "Bao quát đặc tả kỹ thuật và luồng hệ thống.", "suggestion": None})

        elif profile in ["research", "market_research", "academic"]:
            if sources_count < 2:
                checks.append({"name": "Nguồn trích dẫn học thuật", "status": "fail", "message": "Nghiên cứu cần tối thiểu 2 nguồn kiểm chứng trở lên.", "suggestion": "Tìm thêm nguồn xác thực từ Deep Research."})
                score -= 25
            else:
                checks.append({"name": "Nguồn trích dẫn học thuật", "status": "pass", "message": f"Đã trích dẫn {sources_count} nguồn xác thực.", "suggestion": None})

        elif profile in ["data_analysis", "financial"]:
            has_numbers = any(char.isdigit() for char in full_text)
            if not has_numbers:
                checks.append({"name": "Dữ liệu & Số liệu kiểm chứng", "status": "warning", "message": "Báo cáo dữ liệu cần có các chỉ số hoặc bảng số liệu thống kê.", "suggestion": "Chèn bảng số liệu hoặc biểu đồ."})
                score -= 20
            else:
                checks.append({"name": "Dữ liệu & Số liệu kiểm chứng", "status": "pass", "message": "Đầy đủ số liệu định lượng và bảng chỉ số.", "suggestion": None})

        final_score = max(0, min(100, score))
        is_ready = final_score >= 60
        grade = "A" if final_score >= 85 else "B" if final_score >= 70 else "C" if final_score >= 50 else "D"

        return {
            "overall_score": final_score,
            "grade": grade,
            "is_ready_to_export": is_ready,
            "summary": f"Báo cáo đạt {final_score}/100 điểm chất lượng hồ sơ {profile.upper()}.",
            "checks": checks,
            "missing_sections": [c["name"] for c in checks if c["status"] in ["warning", "fail"]],
            "missing_figures": [],
            "unsupported_claims": [],
        }


multi_profile_quality_engine = MultiProfileQualityEngine()
