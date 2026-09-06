"""Metadata-only commercial operations. Catalog is code-owned, not mutable config."""
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.admin_access import require_admin
from app.models.admin_billing import Payment, Subscription
from app.services.billing.plan_definitions import PLANS
from app.services.billing.billing_provider import billing_provider

router = APIRouter(dependencies=[Depends(require_admin)])


def metadata(record):
    return {column.name: getattr(record, column.name) for column in record.__table__.columns if column.name != "order_code"}


def provider_metadata():
    return {"provider_status": "configured" if billing_provider.configured else "not_configured",
            "read_only_reason": "Catalog is maintained in deployment code; one-time payments do not support recurring billing, cancellation or refunds here."}


@router.get("/plans")
async def plans(page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100)):
    items = [{**plan.model_dump(), "checkout_amount": billing_provider.amount_for_plan(key), "checkout_currency": "VND", "editable": False} for key, plan in PLANS.items()]
    return {"items": items[(page-1)*page_size:page*page_size], "total": len(items), "page": page, "page_size": page_size, **provider_metadata()}


async def list_records(model, db, page, page_size, search, status, user_id, plan, start, end, sort, order):
    date_column = model.created_at if model is Payment else model.started_at
    allowed_sort = {"created_at": date_column, "started_at": date_column, "status": model.status, "plan": model.plan}
    if sort not in allowed_sort or order not in ("asc", "desc"):
        raise HTTPException(422, "Unsupported sort or order")
    if start:start=start.replace(tzinfo=start.tzinfo or timezone.utc).astimezone(timezone.utc)
    if end:end=end.replace(tzinfo=end.tzinfo or timezone.utc).astimezone(timezone.utc)
    if start and end and start >= end:
        raise HTTPException(422, "from must precede to")
    query = select(model)
    for field, value in ((model.status, status), (model.user_id, user_id), (model.plan, plan)):
        if value:
            query = query.where(field == value)
    if search:
        query = query.where(or_(model.id.contains(search, autoescape=True), model.user_id.contains(search, autoescape=True)))
    if start:
        query = query.where(date_column >= start)
    if end:
        query = query.where(date_column < end)
    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    column = allowed_sort[sort]
    rows = (await db.scalars(query.order_by(column.asc() if order == "asc" else column.desc(), model.id).offset((page-1)*page_size).limit(page_size))).all()
    return {"items": [metadata(row) for row in rows], "total": total, "page": page, "page_size": page_size, **provider_metadata()}


@router.get("/payments")
async def payments(db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    search: str = Query("", max_length=200), status: str | None = None, user_id: str | None = None, plan: str | None = None,
    start: datetime | None = Query(None, alias="from"), end: datetime | None = Query(None, alias="to"), sort: str = "created_at", order: str = "desc"):
    return await list_records(Payment, db, page, page_size, search, status, user_id, plan, start, end, sort, order)


@router.get("/payments/{payment_id}")
async def payment_detail(payment_id: str, db: AsyncSession = Depends(get_db)):
    payment = await db.get(Payment, payment_id)
    if payment is None:
        raise HTTPException(404, "Payment not found")
    subscription = await db.scalar(select(Subscription).where(Subscription.payment_id == payment.id))
    return {**metadata(payment), "subscription": metadata(subscription) if subscription else None}


@router.get("/billing")
@router.get("/billing/subscriptions")
async def subscriptions(db: AsyncSession = Depends(get_db), page: int = Query(1, ge=1), page_size: int = Query(25, ge=1, le=100),
    search: str = Query("", max_length=200), status: str | None = None, user_id: str | None = None, plan: str | None = None,
    start: datetime | None = Query(None, alias="from"), end: datetime | None = Query(None, alias="to"), sort: str = "created_at", order: str = "desc"):
    return await list_records(Subscription, db, page, page_size, search, status, user_id, plan, start, end, sort, order)
