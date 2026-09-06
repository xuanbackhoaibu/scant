"""Run: python -m app.migrations.admin_console. Additive, repeatable migration.

Back up the database first. Run before rolling out admin-enabled API workers.
Existing account plans and existing quota overrides are preserved.
"""
import asyncio
from datetime import datetime, timezone
from sqlalchemy import Index, select, func, inspect, MetaData, insert, text
from sqlalchemy.ext.asyncio import async_sessionmaker
from app.core.database import engine
from app.models.entities import User, UserQuota, AIUsageEvent, Job, AuditLog, Project, UploadedFile
from app.models.admin_billing import Payment, Subscription
from app.models.admin_configuration import AdminConfiguration
from app.services.admin.plan_service import next_month
from app.services.billing.plan_definitions import PLANS

INDEXES=[
    Index('ix_admin_users_created',User.created_at),
    Index('ix_admin_usage_user_date',AIUsageEvent.user_id,AIUsageEvent.created_at),
    Index('ix_admin_usage_date',AIUsageEvent.created_at),
    Index('ix_admin_jobs_status_date',Job.status,Job.created_at),
    Index('ix_admin_jobs_project_date',Job.project_id,Job.created_at),
    Index('ix_admin_audit_target_date',AuditLog.resource_id,AuditLog.created_at),
    Index('ix_admin_audit_date',AuditLog.created_at),
    Index('ix_admin_projects_user_date',Project.user_id,Project.created_at),
    Index('ix_admin_files_project',UploadedFile.project_id),
    Index('ix_admin_payments_date',Payment.created_at),
]

def upgrade_subscription_grants(connection):
    columns=inspect(connection).get_columns('billing_subscriptions')
    if next(column for column in columns if column['name']=='payment_id')['nullable']:
        return
    if connection.dialect.name=='postgresql':
        connection.execute(text('ALTER TABLE billing_subscriptions ALTER COLUMN payment_id DROP NOT NULL'))
        return
    if connection.dialect.name!='sqlite':
        raise RuntimeError('Subscription nullable migration supports PostgreSQL and SQLite only')
    # Upgrade a pre-release admin schema without dropping subscription records.
    metadata=MetaData()
    User.__table__.to_metadata(metadata)
    Payment.__table__.to_metadata(metadata)
    temporary=Subscription.__table__.to_metadata(metadata,name='billing_subscriptions_next')
    temporary.indexes.clear()
    temporary.drop(connection,checkfirst=True)
    temporary.create(connection)
    names=[column.name for column in Subscription.__table__.columns]
    connection.execute(insert(temporary).from_select(names,select(*Subscription.__table__.columns)))
    Subscription.__table__.drop(connection)
    connection.execute(text('ALTER TABLE billing_subscriptions_next RENAME TO billing_subscriptions'))
    for index in Subscription.__table__.indexes:index.create(connection,checkfirst=True)


async def migrate(bind=engine):
    async with bind.begin() as conn:
        for table in [Payment.__table__,Subscription.__table__,AdminConfiguration.__table__]:
            await conn.run_sync(lambda connection,t=table:t.create(connection,checkfirst=True))
        await conn.run_sync(upgrade_subscription_grants)
        for index in INDEXES:
            await conn.run_sync(lambda connection,i=index:i.create(connection,checkfirst=True))
    factory=async_sessionmaker(bind,expire_on_commit=False)
    month=datetime.now(timezone.utc).replace(day=1,hour=0,minute=0,second=0,microsecond=0)
    created=0
    async with factory() as db:
        while True:
            users=(await db.scalars(select(User).outerjoin(UserQuota,UserQuota.user_id==User.id).where(UserQuota.id.is_(None)).limit(500))).all()
            if not users:break
            usage=(await db.execute(select(AIUsageEvent.user_id,func.sum(AIUsageEvent.total_tokens),func.sum(AIUsageEvent.estimated_cost_usd)).where(AIUsageEvent.user_id.in_([u.id for u in users]),AIUsageEvent.created_at>=month).group_by(AIUsageEvent.user_id))).all()
            counts={uid:(tokens,cost) for uid,tokens,cost in usage}
            for user in users:
                plan=PLANS.get(user.plan,PLANS['free']);tokens,cost=counts.get(user.id,(0,0))
                db.add(UserQuota(user_id=user.id,monthly_token_limit=plan.monthly_tokens_limit,monthly_cost_limit_usd=plan.monthly_ai_budget_usd,tokens_used_this_month=tokens or 0,cost_usd_this_month=cost or 0,reset_at=next_month()))
            await db.commit();created+=len(users)
    return {'quota_rows_created':created,'tables_checked':3,'indexes_checked':len(INDEXES)}

if __name__=='__main__':
    print(asyncio.run(migrate()))
