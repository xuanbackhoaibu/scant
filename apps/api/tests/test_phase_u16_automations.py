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
async def test_automation_lifecycle_api(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "opsuser@corp.com",
        "password": "Password123!",
        "name": "Ops User"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Project
    proj_res = await client.post("/api/v1/projects", json={
        "name": "Dự án Báo cáo Vận hành Tự động",
        "type": "business_report"
    }, headers=headers)
    project_id = proj_res.json()["id"]

    # 2. Create Automation
    auto_res = await client.post("/api/v1/automations", json={
        "project_id": project_id,
        "name": "Weekly Executive Brief Automation",
        "trigger_type": "schedule",
        "cron_expression": "0 8 * * 1",
        "report_title_pattern": "Báo cáo Tuần {date}",
        "export_formats": ["docx", "pdf"]
    }, headers=headers)

    assert auto_res.status_code == 200
    auto_data = auto_res.json()
    assert auto_data["is_active"] == True
    automation_id = auto_data["id"]

    # 3. Trigger Automation Run
    trig_res = await client.post(f"/api/v1/automations/{automation_id}/trigger", headers=headers)
    assert trig_res.status_code == 200
    run_res = trig_res.json()
    assert run_res["status"] == "completed"
    assert "report_id" in run_res
    run_id = run_res["run_id"]

    # 4. List Automation Runs
    runs_res = await client.get(f"/api/v1/automations/{automation_id}/runs", headers=headers)
    assert runs_res.status_code == 200
    runs = runs_res.json()
    assert len(runs) == 1
    assert len(runs[0]["logs"]) >= 4

    # 5. Retry Run
    retry_res = await client.post(f"/api/v1/automations/runs/{run_id}/retry", headers=headers)
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "completed"
