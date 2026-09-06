from datetime import datetime, timezone
from fastapi import HTTPException
from sqlalchemy import select, update
from app.models.entities import UserQuota
from app.services.billing.plan_definitions import PLANS
from app.services.admin.audit_service import record_audit


def next_month():
    now=datetime.now(timezone.utc)
    return datetime(now.year+(now.month==12), 1 if now.month==12 else now.month+1, 1, tzinfo=timezone.utc)


async def change_user_plan(db, user, plan, actor, reason, request=None, payment=None):
    if plan not in PLANS:
        raise HTTPException(422, 'Gói dịch vụ không hợp lệ.')
    quota=(await db.execute(select(UserQuota).where(UserQuota.user_id==user.id).with_for_update())).scalar_one_or_none()
    before={'plan':user.plan, 'monthly_token_limit':quota.monthly_token_limit if quota else None, 'monthly_cost_limit_usd':quota.monthly_cost_limit_usd if quota else None}
    ent=PLANS[plan]
    if quota is None:
        quota=UserQuota(user_id=user.id, tokens_used_this_month=0,cost_usd_this_month=0,reset_at=next_month())
        db.add(quota)
    from app.models.admin_billing import Subscription
    await db.execute(update(Subscription).where(Subscription.user_id==user.id,Subscription.status=='active').values(status='superseded',ended_at=datetime.now(timezone.utc)))
    db.add(Subscription(user_id=user.id,plan=plan,provider=payment.provider if payment else 'admin',payment_id=payment.id if payment else None))
    user.plan=plan
    quota.monthly_token_limit=ent.monthly_tokens_limit
    quota.monthly_cost_limit_usd=ent.monthly_ai_budget_usd
    await record_audit(db,actor,'PLAN_CHANGE','user',user.id,before,{
        'plan':plan,'monthly_token_limit':quota.monthly_token_limit,'monthly_cost_limit_usd':quota.monthly_cost_limit_usd,
    },reason,request)
    await db.flush()
    return user
