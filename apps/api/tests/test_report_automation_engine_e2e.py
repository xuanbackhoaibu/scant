import os
import pytest
import pytest_asyncio
import pandas as pd
from pathlib import Path
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings

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
async def test_automation_engine_end_to_end_with_real_excel(client: AsyncClient, tmp_path: Path):
    # 1. Register & Login
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "auto_lead@corp.vn",
        "password": "Password123!",
        "name": "Trưởng phòng Tự động hóa"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Create Project
    proj_res = await client.post("/api/v1/projects", json={
        "name": "Dự án Quản trị Doanh thu & Chi phí Q3",
        "type": "business_report"
    }, headers=headers)
    assert proj_res.status_code in [200, 201]
    project_id = proj_res.json()["id"]

    # 3. Create a real Excel workbook with 2 sheets
    excel_path = tmp_path / "bang_ke_luong_q3.xlsx"
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        df_luong = pd.DataFrame({
            "Mã NV": [f"NV{i:03d}" for i in range(1, 21)],
            "Họ và Tên": [f"Nhân viên {i}" for i in range(1, 21)],
            "Phòng ban": ["Kinh doanh", "Kỹ thuật", "Tài chính", "Vận hành"] * 5,
            "Lương cơ bản": [15000000 + i * 500000 for i in range(1, 21)],
            "Ngày công": [22, 21, 22, 20, 22] * 4,
            "Thưởng KPI": [2000000 + i * 200000 for i in range(1, 21)],
        })
        df_luong.to_excel(writer, sheet_name="Bang_luong", index=False)

        df_tonghop = pd.DataFrame({
            "Chỉ tiêu": ["Tổng quỹ lương", "Tổng nhân sự", "KPI trung bình"],
            "Giá trị": [350000000, 20, 95.5]
        })
        df_tonghop.to_excel(writer, sheet_name="Tong_hop", index=False)

    # 4. Upload file into Project
    with open(excel_path, "rb") as f:
        upload_res = await client.post(
            "/api/v1/files/upload",
            data={"project_id": project_id, "document_type": "dataset"},
            files={"file": ("bang_ke_luong_q3.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
            headers=headers,
        )
    assert upload_res.status_code == 200
    uploaded_file_id = upload_res.json()["id"]

    # 5. Create Automation configured with the real Excel data source
    create_auto_res = await client.post("/api/v1/automations", json={
        "project_id": project_id,
        "name": "Báo cáo Tổng hợp Quỹ lương Tự động",
        "description": "Tự động phân tích bảng lương và xuất báo cáo Word & PDF",
        "trigger_type": "schedule",
        "cron_expression": "0 8 * * 1",
        "timezone": "Asia/Ho_Chi_Minh",
        "data_source_id": uploaded_file_id,
        "source_type": "file",
        "source_config": {"sheet_name": "Bang_luong"},
        "analysis_prompt": "Nhấn mạnh tổng quỹ lương theo từng phòng ban và top thu nhập cao nhất",
        "analysis_mode": "kpi_financial",
        "report_title_pattern": "Báo cáo Lương Thưởng Định kỳ {date}",
        "export_formats": ["docx", "pdf"]
    }, headers=headers)

    assert create_auto_res.status_code == 200
    auto_data = create_auto_res.json()
    assert auto_data["is_active"] is True
    assert auto_data["next_run_at"] is not None  # Scheduler calculated next run
    automation_id = auto_data["id"]

    # 6. Trigger Run Immediately (Chạy ngay)
    run_res = await client.post(f"/api/v1/automations/{automation_id}/trigger", headers=headers)
    assert run_res.status_code == 200
    run_data = run_res.json()
    assert run_data["status"] == "completed"
    assert "report_id" in run_data
    assert len(run_data["output_files"]) >= 2  # Both docx and pdf created
    for out_file in run_data["output_files"]:
        assert Path(out_file["file_path"]).exists()
        assert out_file["file_size"] > 0
        assert "/api/v1/exports/download/" in out_file["download_url"]

    # 7. Verify Automation Runs History
    history_res = await client.get(f"/api/v1/automations/{automation_id}/runs", headers=headers)
    assert history_res.status_code == 200
    runs = history_res.json()
    assert len(runs) == 1
    run_history = runs[0]
    assert run_history["status"] == "completed"
    assert run_history["duration_ms"] > 0
    assert run_history["source_snapshot"]["sheet_name"] == "Bang_luong"
    assert run_history["source_snapshot"]["total_rows"] == 20

    # 8. Test Pause & Resume Automation
    pause_res = await client.post(f"/api/v1/automations/{automation_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["is_active"] is False

    resume_res = await client.post(f"/api/v1/automations/{automation_id}/resume", headers=headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["is_active"] is True
    assert resume_res.json()["next_run_at"] is not None

    # 9. Test Single Automation Detail
    detail_res = await client.get(f"/api/v1/automations/{automation_id}", headers=headers)
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Báo cáo Tổng hợp Quỹ lương Tự động"

    # 10. Clean up delete
    del_res = await client.delete(f"/api/v1/automations/{automation_id}", headers=headers)
    assert del_res.status_code == 200
