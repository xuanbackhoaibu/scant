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
async def test_copilot_chat_flow(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "director@corp.com",
        "password": "Password123!",
        "name": "Director Lee"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post("/api/v1/projects", json={
        "name": "Kế hoạch Tài chính Q1/2026",
        "type": "financial"
    }, headers=headers)
    project_id = proj_res.json()["id"]

    # Send copilot chat
    copilot_res = await client.post("/api/v1/ai/copilot", json={
        "project_id": project_id,
        "message": "Tạo Executive Summary tóm tắt tình hình tài chính quý 1"
    }, headers=headers)

    assert copilot_res.status_code == 200
    data = copilot_res.json()
    assert "reply" in data
    assert len(data["reply"]) > 0
