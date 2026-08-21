import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class DemoProjectTemplate(BaseModel):
    project_name: str
    project_type: str
    description: str
    sample_dataset_name: str
    sample_data_records: List[Dict[str, Any]]
    sample_sections: List[Dict[str, str]]


class DemoProjectService:
    """
    One-Click Demo Project Provisioning Service (Launch Phase L19).
    Allows new users to test full autonomous generation with non-private sample data.
    """

    @staticmethod
    def get_sales_demo_template() -> DemoProjectTemplate:
        return DemoProjectTemplate(
            project_name="Báo Cáo Tăng Trưởng Doanh Số Mẫu (Demo)",
            project_type="financial",
            description="Dự án mẫu khám phá tính năng tạo báo cáo tự động và phân tích định lượng.",
            sample_dataset_name="demo_sales_q2.csv",
            sample_data_records=[
                {"region": "Miền Bắc", "revenue": 140.0, "profit": 28.0, "growth_pct": 18.5},
                {"region": "Miền Trung", "revenue": 95.0, "profit": 19.0, "growth_pct": 12.0},
                {"region": "Miền Nam", "revenue": 215.0, "profit": 43.0, "growth_pct": 24.2},
            ],
            sample_sections=[
                {"title": "1. Tổng Quan Điều Hành", "content": "Báo cáo mẫu phản ánh tình hình hoạt động kinh doanh quý 2 năm 2026."},
                {"title": "2. Phân Tích Doanh Thu & Lợi Nhuận", "content": "Doanh thu toàn quốc đạt 450 tỷ VNĐ với mức tăng trưởng bình quân 19.8%."},
                {"title": "3. Kết Luận & Đề Xuất", "content": "Đẩy mạnh đầu tư hệ thống phân phối tại khu vực trọng điểm."},
            ]
        )


demo_project_service = DemoProjectService()
