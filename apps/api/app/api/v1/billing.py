from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field, HttpUrl
from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User, get_utc_now
from app.models.admin_billing import Payment, Subscription
from app.api.deps import get_current_user
from app.services.billing.plan_definitions import PLANS, get_plan_entitlements
from app.services.billing.billing_provider import billing_provider
from app.services.admin.plan_service import change_user_plan
from app.services.admin.audit_service import record_audit

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan_tier: str
    success_url: HttpUrl = "http://localhost:3050/settings?billing=success"
    cancel_url: HttpUrl = "http://localhost:3050/settings?billing=cancelled"


@router.get("/plans")
async def list_available_plans():
    return [p.model_dump() for p in PLANS.values()]


@router.get("/my-entitlements")
async def get_my_entitlements(current_user: User = Depends(get_current_user)):
    return get_plan_entitlements(current_user.plan or "free").model_dump()


@router.post("/checkout")
async def create_plan_checkout(req: CheckoutRequest, request: Request,
        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if req.plan_tier not in PLANS or req.plan_tier == "free":
        raise HTTPException(400, "Invalid paid plan")
    result = await billing_provider.create_checkout_session(user_id=current_user.id, user_email=current_user.email,
        target_plan=req.plan_tier, success_url=str(req.success_url), cancel_url=str(req.cancel_url))
    payment = Payment(user_id=current_user.id, plan=req.plan_tier, amount=result["amount_vnd"], currency=result["currency"],
        provider=billing_provider.name, provider_session_id=result["session_id"], order_code=result["order_code"])
    db.add(payment)
    await db.flush()
    await record_audit(db, current_user, "billing.checkout", "payment", payment.id, {},
        {"plan": payment.plan, "amount": payment.amount, "currency": payment.currency, "status": "pending"}, "User requested checkout", request)
    await db.commit()
    return result


class ConfirmPaymentRequest(BaseModel):
    session_id: str = Field(min_length=1, max_length=100)
    target_plan: str


@router.post("/confirm-payment")
async def confirm_payment_activation(req: ConfirmPaymentRequest, request: Request,
        current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    payment = await db.scalar(select(Payment).where(Payment.provider_session_id == req.session_id, Payment.user_id == current_user.id))
    if payment is None:
        raise HTTPException(404, "Checkout not found")
    if req.target_plan != payment.plan or payment.plan not in PLANS:
        raise HTTPException(409, "Checkout plan mismatch")
    def response():
        return {"success": True, "message": "Payment verified", "new_plan": current_user.plan, "user_id": current_user.id}
    if payment.status == "paid":
        return response()
    evidence = await billing_provider.verify_payment(payment)
    if (evidence.get("session_id") != payment.provider_session_id or evidence.get("order_code") != payment.order_code
            or evidence.get("status") != "PAID" or evidence.get("amount") != payment.amount
            or evidence.get("amount_paid") != payment.amount or evidence.get("transaction_amount") != payment.amount
            or evidence.get("currency") != payment.currency or not evidence.get("transaction_id")):
        raise HTTPException(409, "Payment not settled or verification mismatch")
    now = get_utc_now()
    try:
        # Conditional write provides atomic claiming on both SQLite and PostgreSQL.
        claim = await db.execute(update(Payment).where(Payment.id == payment.id, Payment.status == "pending").values(
            status="paid", provider_transaction_id=f"{payment.provider}:{evidence['transaction_id']}", paid_at=now))
        if claim.rowcount != 1:
            raise HTTPException(409, "Payment confirmation already in progress; retry")
        # Serialize simultaneous activations for the same user on PostgreSQL.
        await db.execute(select(User).where(User.id == current_user.id).with_for_update().execution_options(populate_existing=True))
        await change_user_plan(db, current_user, payment.plan, current_user, "Server verified payment", request, payment=payment)
        await record_audit(db, current_user, "billing.payment_verified", "payment", payment.id,
            {"status": "pending"}, {"status": "paid", "plan": payment.plan}, "Server verified payment", request)
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(409, "Provider transaction already used") from exc
    return response()
