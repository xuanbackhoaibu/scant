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
async def test_one_click_auto_create_flow(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "autouser@corp.com",
        "password": "Password123!",
        "name": "Auto User"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Auto create with prompt
    form_data = {"prompt": "Báo cáo Tự động Thị trường Năng lượng Mặt trời 2026"}
    auto_res = await client.post("/api/v1/reports/auto-create", data=form_data, headers=headers)
    assert auto_res.status_code == 200
    data = auto_res.json()
    assert "job_id" in data
    assert "report_id" in data
    assert "project_id" in data
    assert data["status"] == "running"
    job_id = data["job_id"]

    # Pause Job
    pause_res = await client.post(f"/api/v1/reports/jobs/{job_id}/pause", headers=headers)
    assert pause_res.status_code == 200
    assert pause_res.json()["status"] == "paused"

    # Resume Job
    resume_res = await client.post(f"/api/v1/reports/jobs/{job_id}/resume", headers=headers)
    assert resume_res.status_code == 200
    assert resume_res.json()["status"] == "running"

    # Cancel Job
    cancel_res = await client.post(f"/api/v1/reports/jobs/{job_id}/cancel", headers=headers)
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Retry Job
    retry_res = await client.post(f"/api/v1/reports/jobs/{job_id}/retry", headers=headers)
    assert retry_res.status_code == 200
    assert retry_res.json()["status"] == "running"
