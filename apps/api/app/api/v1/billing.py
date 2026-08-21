from typing import Any, Dict, List
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.models.entities import User
from app.api.deps import get_current_user
from app.services.billing.plan_definitions import PLANS, get_plan_entitlements
from app.services.billing.entitlement_service import entitlement_service
from app.services.billing.billing_provider import billing_provider

router = APIRouter(prefix="/billing", tags=["billing"])


class CheckoutRequest(BaseModel):
    plan_tier: str  # pro, team, enterprise
    success_url: str = "http://localhost:3050/settings?billing=success"
    cancel_url: str = "http://localhost:3050/settings?billing=cancelled"


@router.get("/plans")
async def list_available_plans():
    """Lists all SaaS subscription plans and their detailed entitlement limits."""
    return [p.model_dump() for p in PLANS.values()]


@router.get("/my-entitlements")
async def get_my_entitlements(
    current_user: User = Depends(get_current_user),
):
    """Returns entitlements for current authenticated user's tier."""
    tier = getattr(current_user, "plan_tier", "free") or "free"
    return get_plan_entitlements(tier).model_dump()


@router.post("/checkout")
async def create_plan_checkout(
    req: CheckoutRequest,
    current_user: User = Depends(get_current_user),
):
    """Initiates checkout session for plan upgrade."""
    if req.plan_tier not in PLANS:
        raise HTTPException(status_code=400, detail=f"Gói dịch vụ không hợp lệ: {req.plan_tier}")

    res = await billing_provider.create_checkout_session(
        user_id=current_user.id,
        user_email=current_user.email,
        target_plan=req.plan_tier,
        success_url=req.success_url,
        cancel_url=req.cancel_url,
    )
    return res
