import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.repositories.user_repo import user_repo

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestAsyncSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def client():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with TestAsyncSession() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c

    app.dependency_overrides.clear()
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_admin_console_access_control(client: AsyncClient):
    # 1. Normal User (Non-Admin)
    reg_normal = await client.post("/api/v1/auth/register", json={
        "email": "employee@saas.com",
        "password": "Password123!",
        "name": "Normal Employee"
    })
    normal_token = reg_normal.json()["access_token"]
    normal_headers = {"Authorization": f"Bearer {normal_token}"}

    # Normal user trying to access /admin -> must get 403 Forbidden
    forbidden_res = await client.get("/api/v1/admin/dashboard", headers=normal_headers)
    assert forbidden_res.status_code == 403

    # 2. Super Admin User
    reg_admin = await client.post("/api/v1/auth/register", json={
        "email": "root_admin@saas.com",
        "password": "Password123!",
        "name": "Root SuperAdmin"
    })
    admin_token = reg_admin.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    # Elevate to superuser in DB
    async with TestAsyncSession() as db:
        admin_user = await user_repo.get_by_email(db, "root_admin@saas.com")
        await user_repo.update(db, db_obj=admin_user, obj_in={"is_superuser": True})

    # Super Admin accessing dashboard -> 200 OK
    dash_res = await client.get("/api/v1/admin/dashboard", headers=admin_headers)
    assert dash_res.status_code == 200
    metrics = dash_res.json()
    assert any(metric["key"] == "total_users" for metric in metrics["metrics"])
    assert "unavailable" in metrics

    # Super Admin lists users
    users_res = await client.get("/api/v1/admin/users", headers=admin_headers)
    assert users_res.status_code == 200
    assert len(users_res.json()["items"]) >= 2

    # Super Admin updates user plan
    target_id = reg_normal.json()["user"]["id"]
    patch_res = await client.patch(f"/api/v1/admin/users/{target_id}", json={
        "plan_tier": "enterprise", "reason": "Approved enterprise upgrade"
    }, headers=admin_headers)
    assert patch_res.status_code == 200
    assert patch_res.json()["plan"] == "enterprise"

    # AI Ops status
    ops_res = await client.get("/api/v1/admin/system/health", headers=admin_headers)
    assert ops_res.status_code == 200
    assert "database" in ops_res.json()
