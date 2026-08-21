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
async def test_collaboration_and_comments_api(client: AsyncClient):
    reg_owner = await client.post("/api/v1/auth/register", json={
        "email": "owner@corp.com",
        "password": "Password123!",
        "name": "Owner User"
    })
    owner_token = reg_owner.json()["access_token"]
    owner_headers = {"Authorization": f"Bearer {owner_token}"}

    # 1. Create Project
    proj_res = await client.post("/api/v1/projects", json={
        "name": "Dự án Hợp tác Doanh nghiệp",
        "type": "business_report"
    }, headers=owner_headers)
    project_id = proj_res.json()["id"]

    # 2. Add Project Member
    mem_res = await client.post("/api/v1/collaboration/members", json={
        "project_id": project_id,
        "invited_email": "colleague@corp.com",
        "role": "editor"
    }, headers=owner_headers)
    assert mem_res.status_code == 200
    assert mem_res.json()["role"] == "editor"

    # 3. List Members
    list_mem = await client.get(f"/api/v1/collaboration/projects/{project_id}/members", headers=owner_headers)
    assert list_mem.status_code == 200
    assert len(list_mem.json()) >= 2

    # 4. Create Report & Post Threaded Comment
    rep_res = await client.post("/api/v1/reports", json={
        "project_id": project_id,
        "title": "Báo cáo Q1",
        "report_type": "business_report"
    }, headers=owner_headers)
    report_id = rep_res.json()["id"]

    comm_res = await client.post("/api/v1/collaboration/comments", json={
        "report_id": report_id,
        "comment_text": "Cần bổ sung biểu đồ doanh số miền Nam",
    }, headers=owner_headers)
    assert comm_res.status_code == 200
    comment_id = comm_res.json()["id"]

    # Reply to comment
    reply_res = await client.post("/api/v1/collaboration/comments", json={
        "report_id": report_id,
        "parent_id": comment_id,
        "comment_text": "Đã thêm dữ liệu miền Nam vào dataset",
    }, headers=owner_headers)
    assert reply_res.status_code == 200

    # List Comments with replies
    list_comm = await client.get(f"/api/v1/collaboration/reports/{report_id}/comments", headers=owner_headers)
    assert list_comm.status_code == 200
    threads = list_comm.json()
    assert len(threads) == 1
    assert len(threads[0]["replies"]) == 1

    # Resolve comment
    res_res = await client.post(f"/api/v1/collaboration/comments/{comment_id}/resolve", headers=owner_headers)
    assert res_res.status_code == 200
    assert res_res.json()["status"] == "resolved"
