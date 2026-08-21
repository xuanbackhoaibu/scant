import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestAsyncSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestAsyncSession() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_full_phase1d_editor_and_export_flow(client: AsyncClient):
    # 1. Register & Project
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "editor_user@test.com",
        "password": "Password123!",
        "name": "Tran Thi E"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post("/api/v1/projects", json={
        "name": "Báo cáo Tốt nghiệp CNTT",
        "type": "academic",
        "topic_details": {
            "university": "Đại học Bách Khoa Hà Nội",
            "student_name": "Tran Thi E",
            "student_id": "20210005",
            "instructor": "PGS. TS. Nguyen Van F"
        }
    }, headers=headers)
    project_id = proj_res.json()["id"]

    # 2. Add verified source
    await client.post("/api/v1/research/sources", json={
        "project_id": project_id,
        "title": "ASP.NET Core Architecture Official Guide",
        "url": "https://learn.microsoft.com/aspnet/core",
        "authors": "Microsoft",
        "publisher": "Microsoft Press",
        "published_date": "2024",
        "source_type": "official_doc",
        "reliability_score": 0.98,
        "summary": "ASP.NET Core is an open source web framework."
    }, headers=headers)

    # 3. Create Report with Chapters
    report_res = await client.post("/api/v1/reports", json={
        "project_id": project_id,
        "title": "Báo cáo Đồ án Website Thương mại Điện tử",
        "report_type": "academic",
        "outline": [
            {
                "title": "CHƯƠNG 1: TỔNG QUAN ĐỀ TÀI",
                "level": 1,
                "position": 1,
                "children": [
                    {"title": "1.1 Bối cảnh chọn đề tài", "level": 2, "position": 2, "children": []}
                ]
            }
        ]
    }, headers=headers)
    assert report_res.status_code == 201
    report_data = report_res.json()
    report_id = report_data["id"]
    section_id = report_data["sections"][0]["id"]

    # 4. AI Draft Section
    draft_res = await client.post("/api/v1/ai/draft-section", json={
        "project_id": project_id,
        "report_id": report_id,
        "section_id": section_id,
        "instruction": "Trình bày tổng quan về ASP.NET Core MVC"
    }, headers=headers)
    assert draft_res.status_code == 200
    assert len(draft_res.json()["text"]) > 0

    # 5. Check Quality Gate
    qc_res = await client.post(f"/api/v1/ai/check-report/{report_id}", headers=headers)
    assert qc_res.status_code == 200
    qc_data = qc_res.json()
    assert qc_data["overall_score"] > 0

    # 6. Export DOCX
    docx_res = await client.post("/api/v1/exports/docx", json={
        "report_id": report_id,
        "export_format": "docx",
        "include_cover": True,
        "include_toc": True,
        "include_references": True
    }, headers=headers)
    assert docx_res.status_code == 200
    docx_data = docx_res.json()
    assert docx_data["file_size"] > 0
    assert "download_url" in docx_data

    # 7. Export PDF/HTML
    pdf_res = await client.post("/api/v1/exports/pdf", json={
        "report_id": report_id,
        "export_format": "pdf"
    }, headers=headers)
    assert pdf_res.status_code == 200
    assert pdf_res.json()["file_size"] > 0
