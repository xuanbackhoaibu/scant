import asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import AsyncSessionLocal, init_db
from app.core.security import get_password_hash
from app.models.entities import (
    User, Workspace, Project, Template, TemplateVersion,
    Report, ReportSection, Source, Citation, ClaimSource
)
from app.services.exports.docx_exporter import docx_exporter


DEMO_EMAIL = "demo@aireportstudio.pro"
DEMO_PASSWORD = "DemoVIP123!"
DEMO_WORKSPACE_SLUG = "vip-engineering"
DEMO_TEMPLATE_NAME = "Mẫu Báo cáo Bài tập lớn CNTT - ĐH Bách Khoa Hà Nội"
DEMO_PROJECT_NAME = "Xây dựng Website Thương mại Điện tử ASP.NET Core MVC"
DEMO_REPORT_TITLE = "Báo cáo Đồ án: Xây dựng Website Thương mại Điện tử ASP.NET Core MVC"


async def _one_or_none(db: AsyncSession, statement):
    return (await db.execute(statement.limit(1))).scalar_one_or_none()


async def seed_data():
    await init_db()
    async with AsyncSessionLocal() as db:
        # 1. Create Demo VIP User
        user = await _one_or_none(db, select(User).where(User.email == DEMO_EMAIL))
        if user is None:
            user = User(
                email=DEMO_EMAIL,
                password_hash=get_password_hash(DEMO_PASSWORD),
                name="Kỹ sư VIP Pro",
                plan="enterprise",
                is_active=True,
            )
            db.add(user)
            await db.flush()
        else:
            user.name = "Kỹ sư VIP Pro"
            user.plan = "enterprise"
            user.is_active = True

        # 2. Create Workspace
        ws = await _one_or_none(
            db,
            select(Workspace).where(
                Workspace.user_id == user.id,
                Workspace.slug == DEMO_WORKSPACE_SLUG,
            ),
        )
        if ws is None:
            ws = Workspace(
                user_id=user.id,
                name="VIP Engineering Workspace",
                slug=DEMO_WORKSPACE_SLUG,
                settings_json={},
            )
            db.add(ws)
            await db.flush()

        # 3. Create Standard Templates
        tpl_bkhn = await _one_or_none(
            db,
            select(Template).where(
                Template.user_id == user.id,
                Template.name == DEMO_TEMPLATE_NAME,
            ),
        )
        if tpl_bkhn is None:
            tpl_bkhn = Template(
                user_id=user.id,
                name=DEMO_TEMPLATE_NAME,
                category="academic",
                description="Mẫu chuẩn khoa CNTT & TT: A4, lề trái 30mm, Times New Roman 13pt, Dãn dòng 1.5.",
                is_system=True,
                is_public=True,
                organization="Đại học Bách Khoa Hà Nội",
            )
            db.add(tpl_bkhn)
            await db.flush()

        tpl_ver = await _one_or_none(
            db,
            select(TemplateVersion).where(
                TemplateVersion.template_id == tpl_bkhn.id,
                TemplateVersion.version_number == 1,
            ),
        )
        if tpl_ver is None:
            tpl_ver = TemplateVersion(
                template_id=tpl_bkhn.id,
                version_number=1,
                styles_json={
                    "paper": "A4",
                    "margins": {"top": 20, "bottom": 20, "left": 30, "right": 20},
                    "font_family": "Times New Roman",
                    "font_size": 13,
                    "line_spacing": 1.5,
                },
                placeholders_json={"explicit": ["student_name", "student_id", "topic"], "detected": {}},
            )
            db.add(tpl_ver)
            await db.flush()

        # 4. Create Sample Academic Project (ASP.NET Core MVC E-Commerce)
        proj = await _one_or_none(
            db,
            select(Project).where(
                Project.user_id == user.id,
                Project.name == DEMO_PROJECT_NAME,
            ),
        )
        if proj is None:
            proj = Project(
                user_id=user.id,
                workspace_id=ws.id,
                name=DEMO_PROJECT_NAME,
                type="academic",
                description="Đề tài bài tập lớn nghiên cứu kiến trúc Clean Architecture, xây dựng website bán hàng trực tuyến tích hợp cơ chế phân quyền, giỏ hàng, thanh toán và tối ưu hóa truy vấn cơ sở dữ liệu.",
                settings_json={},
                topic_details_json={
                    "topic_name": DEMO_PROJECT_NAME,
                    "subject": "Phát triển Ứng dụng Web & Kiến trúc Phần mềm",
                    "major": "Công nghệ Thông tin",
                    "university": "TRƯỜNG ĐẠI HỌC BÁCH KHOA HÀ NỘI",
                    "instructor": "TS. Nguyễn Văn B",
                    "student_name": "Nguyễn Văn A",
                    "student_id": "20210001",
                    "class_name": "K66-CNTT-01",
                    "academic_year": "Hà Nội, 2026",
                },
            )
            db.add(proj)
            await db.flush()
        else:
            proj.workspace_id = ws.id
            proj.settings_json = proj.settings_json or {}
            proj.metadata_json = proj.metadata_json or {}
            proj.topic_details_json = proj.topic_details_json or {
                "topic_name": DEMO_PROJECT_NAME,
                "subject": "Phát triển Ứng dụng Web & Kiến trúc Phần mềm",
                "major": "Công nghệ Thông tin",
                "university": "TRƯỜNG ĐẠI HỌC BÁCH KHOA HÀ NỘI",
                "instructor": "TS. Nguyễn Văn B",
                "student_name": "Nguyễn Văn A",
                "student_id": "20210001",
                "class_name": "K66-CNTT-01",
                "academic_year": "Hà Nội, 2026",
            }

        # 5. Create Verified Academic Sources
        src1 = Source(
            project_id=proj.id,
            title="ASP.NET Core Documentation & Architecture Overview",
            url="https://learn.microsoft.com/en-us/aspnet/core/fundamentals/",
            authors="Microsoft Learn Team",
            publisher="Microsoft Press",
            published_date="2024",
            source_type="official_doc",
            reliability_score=0.98,
            summary="ASP.NET Core is a cross-platform, high-performance, open-source framework for modern web applications.",
        )
        src2 = Source(
            project_id=proj.id,
            title="Relational Database Design Principles and Normalization (1NF, 2NF, 3NF)",
            url="https://ieeexplore.ieee.org/document/relational-db-design",
            authors="E. F. Codd, C. J. Date",
            publisher="IEEE Computer Society",
            published_date="2022",
            source_type="paper",
            reliability_score=0.95,
            summary="Database normalization minimizes data redundancy and improves data integrity through formal normal forms.",
        )
        src3 = Source(
            project_id=proj.id,
            title="JSON Web Token (JWT) Standard Specification RFC 7519",
            url="https://datatracker.ietf.org/doc/html/rfc7519",
            authors="M. Jones, J. Bradley, N. Sakimura",
            publisher="IETF Tools",
            published_date="2021",
            source_type="standard",
            reliability_score=0.96,
            summary="JSON Web Token is a compact, URL-safe means of representing claims securely.",
        )
        for source in [src1, src2, src3]:
            existing_source = await _one_or_none(
                db,
                select(Source).where(
                    Source.project_id == proj.id,
                    Source.title == source.title,
                ),
            )
            if existing_source is None:
                db.add(source)
        await db.flush()

        # 6. Create Sample Report
        report = await _one_or_none(
            db,
            select(Report).where(
                Report.project_id == proj.id,
                Report.title == DEMO_REPORT_TITLE,
            ),
        )
        if report is None:
            report = Report(
                project_id=proj.id,
                template_version_id=tpl_ver.id,
                title=DEMO_REPORT_TITLE,
                report_type="academic",
                status="completed",
                revision=1,
                document_settings_json={
                    "paper": "A4",
                    "font_family": "Times New Roman",
                    "font_size": 13,
                    "line_spacing": 1.5,
                    "margins": {"top": 20, "bottom": 20, "left": 30, "right": 20},
                    "citation_style": "IEEE",
                },
            )
            db.add(report)
            await db.flush()

        # 7. Create Structured Chapters & Sections
        chapters_data = [
            ("LỜI MỞ ĐẦU", 1, 1, "Trong kỷ nguyên chuyển đổi số và thương mại điện tử bùng nổ, việc xây dựng các nền tảng bán hàng trực tuyến có độ sẵn sàng cao, bảo mật vững chắc và trải nghiệm người dùng tối ưu là nhu cầu cấp thiết."),
            ("CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI", 1, 2, "Chương này trình bày lý do chọn đề tài, mục tiêu nghiên cứu, phạm vi ứng dụng và phương pháp thực hiện."),
            ("1.1 Lý do chọn đề tài", 2, 3, "Thương mại điện tử đòi hỏi hệ thống xử lý giao dịch đồng thời nhanh chóng và kiến trúc mở rộng linh hoạt."),
            ("1.2 Mục tiêu đề tài", 2, 4, "Mục tiêu là hiện thực hóa một hệ thống web bán hàng toàn diện áp dụng kiến trúc ASP.NET Core MVC [1]."),
            ("CHƯƠNG 2: CƠ SỞ LÝ THUYẾT VÀ CÔNG NGHỆ", 1, 5, "Nghiên cứu kiến trúc nền tảng ASP.NET Core, Entity Framework Core và các cơ chế bảo mật xác thực hiện đại."),
            ("2.1 Tổng quan về framework ASP.NET Core", 2, 6, "ASP.NET Core là framework mã nguồn mở hiệu năng cao cho phép phát triển ứng dụng đám mây độc lập nền tảng [1]."),
            ("2.2 Thiết kế cơ sở dữ liệu và chuẩn hóa quan hệ", 2, 7, "Cơ sở dữ liệu được thiết kế đạt chuẩn chuẩn hóa bậc 3 (3NF) nhằm loại bỏ dư thừa dữ liệu và đảm bảo toàn vẹn giao dịch [2]."),
            ("2.3 Cơ chế phân quyền và bảo mật xác thực JWT", 2, 8, "Cơ chế JWT (JSON Web Token) được triển khai theo chuẩn RFC 7519 đảm bảo an toàn cho phiên làm việc không trạng thái [3]."),
            ("CHƯƠNG 3: THIẾT KẾ VÀ HIỆN THỰC HÓA HỆ THỐNG", 1, 9, "Chi tiết triển khai các chức năng danh mục sản phẩm, giỏ hàng, đặt hàng và tích hợp cổng thanh toán trực tuyến."),
            ("CHƯƠNG 4: KIỂM THỬ VÀ ĐÁNH GIÁ KẾT QUẢ", 1, 10, "Kịch bản kiểm thử chức năng và đo lường hiệu năng xử lý với hàng nghìn truy vấn đồng thời."),
            ("CHƯƠNG 5: KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN", 1, 11, "Đề tài đã hoàn thành xuất sắc các mục tiêu đề ra và sẵn sàng cho việc tích hợp AI gợi ý sản phẩm trong tương lai."),
        ]

        existing_sections = (
            await db.execute(select(ReportSection).where(ReportSection.report_id == report.id))
        ).scalars().all()
        sections_list = list(existing_sections)
        existing_section_titles = {section.title for section in existing_sections}

        for title, level, pos, text in chapters_data:
            if title in existing_section_titles:
                continue
            sec = ReportSection(
                report_id=report.id,
                title=title,
                level=level,
                position=pos,
                status="draft",
                plain_text=f"{title}\n\n{text}",
                content_json={
                    "type": "doc",
                    "content": [
                        {"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": title}]},
                        {"type": "paragraph", "content": [{"type": "text", "text": text}]},
                    ],
                },
                word_count=len(f"{title} {text}".split()),
                structured_summary_json={},
            )
            db.add(sec)
            sections_list.append(sec)

        await db.commit()

        # Generate sample DOCX on disk
        docx_exporter.generate_docx(
            report_title=report.title,
            topic_details=proj.topic_details_json,
            sections=sections_list,
            sources=[src1, src2, src3],
        )

        print("✅ Sample Academic Project and VIP Templates seeded successfully!")
        return {
            "email": DEMO_EMAIL,
            "password": DEMO_PASSWORD,
            "project_id": proj.id,
            "report_id": report.id,
        }


if __name__ == "__main__":
    asyncio.run(seed_data())
