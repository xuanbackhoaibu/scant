import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.services.observability.structured_logger import structured_logger
from app.services.observability.metrics_collector import metrics_collector

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


def test_structured_logging():
    # 1. HTTP Log
    http_event = structured_logger.log_http_request(
        request_id="req-test-12345",
        method="POST",
        route="/api/v1/reports/auto-create",
        status_code=200,
        duration_ms=45,
        user_id="usr-99",
    )
    assert http_event["request_id"] == "req-test-12345"
    assert http_event["duration_ms"] == 45

    # 2. AI Trace Log
    ai_event = structured_logger.log_ai_trace(
        trace_id="tr-trace-987",
        task_type="SECTION_WRITING",
        provider="gemini",
        model="gemini-2.5-flash",
        latency_ms=210,
        tokens=1500,
        cost_usd=0.00035,
    )
    assert ai_event["trace_id"] == "tr-trace-987"
    assert ai_event["estimated_cost_usd"] == 0.00035


def test_metrics_telemetry():
    metrics_collector.record_http_request(30)
    metrics_collector.record_http_request(85)
    metrics_collector.record_ai_request(240, success=True)
    metrics_collector.record_export(380)

    summary = metrics_collector.get_summary()
    assert "api_latency_p50_ms" in summary
    assert "ai_latency_p50_ms" in summary
    assert "ai_failure_rate_pct" in summary


@pytest.mark.asyncio
async def test_metrics_api(client: AsyncClient):
    res = await client.get("/api/v1/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "api_latency_p50_ms" in data
    assert "database_latency_ms" in data
