import pytest
import pytest_asyncio
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.api.v1 import billing, admin_billing
from app.api.deps import get_current_user
from app.core.database import Base, get_db
from app.models.entities import User, AuditLog, UserQuota
from app.models.admin_billing import Payment, Subscription


class ControlledProvider:
    name = "controlled"
    configured = True
    changes = {}
    def amount_for_plan(self, plan):
        return 123000
    async def create_checkout_session(self, **kwargs):
        return {"session_id": "session-1", "order_code": "123", "target_plan": kwargs["target_plan"],
                "amount_vnd": 123000, "currency": "VND", "checkout_url": "https://example.test/pay"}
    async def verify_payment(self, payment):
        return {"session_id": payment.provider_session_id, "order_code": payment.order_code, "status": "PAID",
                "amount": 123000, "amount_paid": 123000, "transaction_amount": 123000, "currency": "VND",
                "transaction_id": "transaction-1", **self.changes}


@pytest_asyncio.fixture
async def context(monkeypatch):
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(engine, expire_on_commit=False)
    async with factory() as db:
        user = User(id="payer", email="payer@example.test", name="Payer", plan="free")
        db.add(user)
        db.add(User(id="other", email="other@example.test", name="Other", plan="free"))
        await db.commit()
    app = FastAPI()
    app.include_router(billing.router)
    app.include_router(admin_billing.router, prefix="/admin")
    async def database():
        async with factory() as db:
            try:
                yield db
                await db.commit()
            except Exception:
                await db.rollback()
                raise
    async def auth():
        async with factory() as db:
            return await db.get(User, "payer")
    app.dependency_overrides[get_db] = database
    # Return attached user from request DB so plan changes persist, like production auth.
    from fastapi import Depends
    async def attached_auth(db=Depends(get_db)):
        return await db.get(User, "payer")
    app.dependency_overrides[get_current_user] = attached_auth
    provider = ControlledProvider()
    monkeypatch.setattr(billing, "billing_provider", provider)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        yield client, factory, provider
    await engine.dispose()


async def checkout(client):
    result = await client.post("/billing/checkout", json={"plan_tier": "pro"})
    assert result.status_code == 200, result.text


@pytest.mark.asyncio
@pytest.mark.parametrize("changes", [{"status": "PENDING"}, {"amount": 1}, {"amount_paid": 1}, {"transaction_amount": 1},
    {"currency": "USD"}, {"session_id": "forged"}, {"order_code": "wrong"}, {"transaction_id": None}])
async def test_reject_bad_evidence(context, changes):
    client, factory, provider = context
    await checkout(client)
    provider.changes = changes
    result = await client.post("/billing/confirm-payment", json={"session_id": "session-1", "target_plan": "pro"})
    assert result.status_code == 409
    async with factory() as db:
        assert (await db.get(User, "payer")).plan == "free"
        assert await db.scalar(select(func.count()).select_from(Subscription)) == 0
        assert (await db.scalar(select(Payment))).status == "pending"


@pytest.mark.asyncio
async def test_invalid_session_owner_and_plan(context):
    client, factory, _ = context
    result = await client.post("/billing/confirm-payment", json={"session_id": "invented", "target_plan": "enterprise"})
    assert result.status_code == 404
    await checkout(client)
    result = await client.post("/billing/confirm-payment", json={"session_id": "session-1", "target_plan": "enterprise"})
    assert result.status_code == 409
    async with factory() as db:
        payment = await db.scalar(select(Payment))
        payment.user_id = "other"
        await db.commit()
    result = await client.post("/billing/confirm-payment", json={"session_id": "session-1", "target_plan": "pro"})
    assert result.status_code == 404


@pytest.mark.asyncio
async def test_verified_activation_replay_and_duplicate_transaction(context):
    client, factory, _ = context
    await checkout(client)
    for _ in range(2):
        result = await client.post("/billing/confirm-payment", json={"session_id": "session-1", "target_plan": "pro"})
        assert result.status_code == 200, result.text
    async with factory() as db:
        assert (await db.get(User, "payer")).plan == "pro"
        assert await db.scalar(select(func.count()).select_from(Subscription)) == 1
        assert await db.scalar(select(func.count()).select_from(AuditLog).where(AuditLog.action == "billing.payment_verified")) == 1
        db.add(Payment(user_id="payer", plan="enterprise", amount=123000, currency="VND", provider="controlled",
            provider_session_id="session-2", order_code="456"))
        await db.commit()
    result = await client.post("/billing/confirm-payment", json={"session_id": "session-2", "target_plan": "enterprise"})
    assert result.status_code == 409
    async with factory() as db:
        assert (await db.get(User, "payer")).plan == "pro"
        assert await db.scalar(select(func.count()).select_from(Subscription)) == 1


@pytest.mark.asyncio
async def test_unconfigured_provider_and_admin_guard(context, monkeypatch):
    client, _, _ = context
    from app.services.billing.billing_provider import VietQRPayOSBillingProvider
    monkeypatch.delenv("PAYOS_API_KEY", raising=False)
    monkeypatch.setattr(billing, "billing_provider", VietQRPayOSBillingProvider())
    result = await client.post("/billing/checkout", json={"plan_tier": "pro"})
    assert result.status_code == 503
    assert "Not configured" in result.text
    assert (await client.get("/admin/payments")).status_code == 403
