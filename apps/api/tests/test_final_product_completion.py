import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.services.auth.google_auth_service import google_auth_service

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
async def test_google_auth_token_verification():
    # Empty token rejected
    is_valid, user_info, err = await google_auth_service.verify_id_token("")
    assert is_valid is False
    assert err is not None


@pytest.mark.asyncio
async def test_user_profile_preferences_and_password_update(client: AsyncClient):
    # 1. Register User
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "enterprise_user@corp.com",
        "password": "Password123!",
        "name": "Enterprise User"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Update Profile (preferred_locale, theme, document_language)
    prof_res = await client.put("/api/v1/auth/profile", json={
        "name": "Enterprise Director",
        "preferred_locale": "en",
        "theme": "dark",
        "document_language": "en"
    }, headers=headers)
    assert prof_res.status_code == 200
    data = prof_res.json()
    assert data["name"] == "Enterprise Director"
    assert data["preferred_locale"] == "en"
    assert data["theme"] == "dark"
    assert data["document_language"] == "en"

    # 3. Change Password
    # Wrong old password -> must fail
    fail_res = await client.put("/api/v1/auth/change-password", json={
        "old_password": "WrongPassword!",
        "new_password": "NewStrongPassword123!"
    }, headers=headers)
    assert fail_res.status_code == 400

    # Correct old password -> success
    pass_res = await client.put("/api/v1/auth/change-password", json={
        "old_password": "Password123!",
        "new_password": "NewStrongPassword123!"
    }, headers=headers)
    assert pass_res.status_code == 200

    # 4. Check Linked Accounts
    acc_res = await client.get("/api/v1/auth/accounts", headers=headers)
    assert acc_res.status_code == 200
    accs = acc_res.json()
    assert len(accs) >= 1
    assert accs[0]["provider"] == "password"


@pytest.mark.asyncio
async def test_brand_kit_database_persistence(client: AsyncClient):
    # Register user
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "brandkit_user@corp.com",
        "password": "Password123!",
        "name": "Brand Kit User"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get default Brand Kit
    get_res = await client.get("/api/v1/brand-kit", headers=headers)
    assert get_res.status_code == 200
    assert "primary_color" in get_res.json()

    # 2. Update Brand Kit with custom colors and typography
    put_res = await client.put("/api/v1/brand-kit", json={
        "primary_color": "#0f172a",
        "secondary_color": "#2563eb",
        "primary_font": "Plus Jakarta Sans",
        "heading_font": "Plus Jakarta Sans",
        "header_text": "ENTERPRISE • QUARTERLY REPORT",
        "confidentiality_notice": "CONFIDENTIAL"
    }, headers=headers)
    assert put_res.status_code == 200
    updated = put_res.json()
    assert updated["primary_color"] == "#0f172a"
    assert updated["primary_font"] == "Plus Jakarta Sans"

    # 3. Reload from database
    reload_res = await client.get("/api/v1/brand-kit", headers=headers)
    assert reload_res.status_code == 200
    assert reload_res.json()["header_text"] == "ENTERPRISE • QUARTERLY REPORT"
