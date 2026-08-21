from typing import Any, Dict, List
from pydantic import BaseModel


class PlanEntitlements(BaseModel):
    plan_tier: str
    name: str
    monthly_price_usd: float
    monthly_ai_budget_usd: float
    monthly_tokens_limit: int
    deep_research_limit: int
    storage_limit_mb: int
    projects_limit: int
    members_limit: int
    automation_limit: int
    premium_models: bool
    allowed_export_formats: List[str]


PLANS: Dict[str, PlanEntitlements] = {
    "free": PlanEntitlements(
        plan_tier="free",
        name="Free Tier",
        monthly_price_usd=0.0,
        monthly_ai_budget_usd=5.0,
        monthly_tokens_limit=250_000,
        deep_research_limit=3,
        storage_limit_mb=50,
        projects_limit=3,
        members_limit=1,
        automation_limit=0,
        premium_models=False,
        allowed_export_formats=["docx", "html", "md"],
    ),
    "pro": PlanEntitlements(
        plan_tier="pro",
        name="Professional",
        monthly_price_usd=29.0,
        monthly_ai_budget_usd=25.0,
        monthly_tokens_limit=2_500_000,
        deep_research_limit=50,
        storage_limit_mb=2048,
        projects_limit=50,
        members_limit=3,
        automation_limit=5,
        premium_models=True,
        allowed_export_formats=["docx", "pdf", "html", "md"],
    ),
    "team": PlanEntitlements(
        plan_tier="team",
        name="Team Collaboration",
        monthly_price_usd=99.0,
        monthly_ai_budget_usd=100.0,
        monthly_tokens_limit=15_000_000,
        deep_research_limit=300,
        storage_limit_mb=10240,
        projects_limit=200,
        members_limit=20,
        automation_limit=50,
        premium_models=True,
        allowed_export_formats=["docx", "pdf", "html", "md", "pptx"],
    ),
    "enterprise": PlanEntitlements(
        plan_tier="enterprise",
        name="Enterprise Scale",
        monthly_price_usd=499.0,
        monthly_ai_budget_usd=1000.0,
        monthly_tokens_limit=200_000_000,
        deep_research_limit=9999,
        storage_limit_mb=1048576,
        projects_limit=9999,
        members_limit=999,
        automation_limit=999,
        premium_models=True,
        allowed_export_formats=["docx", "pdf", "html", "md", "pptx"],
    ),
}


def get_plan_entitlements(tier: str) -> PlanEntitlements:
    return PLANS.get(tier.lower(), PLANS["free"])
