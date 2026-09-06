import pytest
from sqlalchemy import select,inspect
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from app.core.database import Base
from app.models.entities import User,UserQuota,AIUsageEvent
from app.models.admin_billing import Payment,Subscription
from app.models.admin_configuration import AdminConfiguration
from app.migrations.admin_console import migrate

@pytest.mark.asyncio
async def test_additive_migration_is_repeatable_and_preserves_overrides():
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for table in [Subscription.__table__,Payment.__table__,AdminConfiguration.__table__]:
            await conn.run_sync(table.drop)
    async with factory() as db:
        db.add_all([User(id='old',email='old@example.com',name='Old',plan='pro'),User(id='custom',email='custom@example.com',name='Custom',plan='free')])
        await db.flush()
        db.add_all([UserQuota(user_id='custom',monthly_token_limit=123,tokens_used_this_month=12),AIUsageEvent(user_id='old',task_type='test',provider='test',model='test',total_tokens=42,estimated_cost_usd=.1)])
        await db.commit()
    assert (await migrate(engine))['quota_rows_created']==1
    assert (await migrate(engine))['quota_rows_created']==0
    async with factory() as db:
        quotas={q.user_id:q for q in (await db.scalars(select(UserQuota))).all()}
        assert quotas['custom'].monthly_token_limit==123
        assert quotas['custom'].tokens_used_this_month==12
        assert quotas['old'].monthly_token_limit==2500000
        assert quotas['old'].tokens_used_this_month==42
    await engine.dispose()

@pytest.mark.asyncio
async def test_prerelease_subscription_schema_keeps_existing_payments():
    from sqlalchemy.schema import CreateTable
    from sqlalchemy import text
    engine=create_async_engine('sqlite+aiosqlite:///:memory:')
    factory=async_sessionmaker(engine,expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(Subscription.__table__.drop)
        ddl=str(CreateTable(Subscription.__table__).compile(dialect=engine.dialect)).replace('payment_id VARCHAR(36)', 'payment_id VARCHAR(36) NOT NULL')
        await conn.execute(text(ddl))
    async with factory() as db:
        db.add(User(id='payer',email='payer@example.com',name='Payer',plan='pro'))
        db.add(Payment(id='paid',user_id='payer',plan='pro',amount=100,currency='VND',provider='test',provider_session_id='session',order_code='order'))
        await db.flush()
        db.add(Subscription(id='original',user_id='payer',plan='pro',provider='test',payment_id='paid'))
        await db.commit()
    await migrate(engine)
    async with factory() as db:
        assert (await db.get(Subscription,'original')).payment_id=='paid'
        db.add(Subscription(user_id='payer',plan='free',provider='admin',payment_id=None))
        await db.commit()
    await migrate(engine)
    async with factory() as db:assert len((await db.scalars(select(Subscription))).all())==2
    await engine.dispose()
