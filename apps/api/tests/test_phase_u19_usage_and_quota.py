import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.services.usage.quota_engine import quota_engine, prompt_cache

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


def test_prompt_cache():
    p = "Tạo đề cương báo cáo tài chính"
    prompt_cache.set(prompt=p, system_prompt=None, task_type="OUTLINE", value={"status": "cached_ok"})
    cached = prompt_cache.get(prompt=p, system_prompt=None, task_type="OUTLINE")
    assert cached is not None
    assert cached["status"] == "cached_ok"


@pytest.mark.asyncio
async def test_quota_engine_and_budget_guard():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSession() as db:
        user_id = "test-user-quota-01"

        # 1. Estimate workload
        est = quota_engine.estimate_workload("deep_research", num_sections=6, num_sources=5)
        assert est["expected_total_tokens"] > 10000
        assert est["estimated_cost_usd"] > 0.0

        # 2. Check budget guard with fresh quota
        allowed, msg, _ = await quota_engine.check_budget_guard(db, user_id, "deep_research")
        assert allowed is True

        # 3. Record high usage event
        await quota_engine.record_usage_event(
            db=db,
            user_id=user_id,
            project_id=None,
            task_type="AGENT_REASONING",
            provider="gemini",
            model="gemini-2.5-flash",
            input_tokens=950_000,
            output_tokens=100_000,
            cached_tokens=0,
            estimated_cost_usd=25.0,
            latency_ms=1200,
        )

        # 4. Budget guard should now block because cost exceeded $20 limit
        blocked, block_msg, _ = await quota_engine.check_budget_guard(db, user_id, "deep_research")
        assert blocked is False
        assert "Vượt quá hạn mức" in block_msg

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_usage_api_endpoints(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "saas_user@enterprise.com",
        "password": "Password123!",
        "name": "SaaS Executive"
    })
    assert reg_res.status_code == 200
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Get Usage Summary
    summary_res = await client.get("/api/v1/usage/summary", headers=headers)
    assert summary_res.status_code == 200
    data = summary_res.json()
    assert "monthly_token_limit" in data
    assert "cost_usd_this_month" in data
    assert "remaining_budget_usd" in data

    # 2. Get Usage Events
    events_res = await client.get("/api/v1/usage/events", headers=headers)
    assert events_res.status_code == 200
    assert isinstance(events_res.json(), list)

    # 3. Workload Estimator API
    est_res = await client.get("/api/v1/usage/estimate-workload?job_type=auto_create&num_sections=4", headers=headers)
    assert est_res.status_code == 200
    assert "expected_total_tokens" in est_res.json()
