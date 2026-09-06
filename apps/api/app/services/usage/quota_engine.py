import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from app.models.entities import AIUsageEvent, UserQuota, Report, Source, UploadedFile, User, Project, ExportRecord
from datetime import datetime, timezone
from app.services.billing.plan_definitions import get_plan_entitlements
from app.services.admin.plan_service import next_month
from app.repositories.base import BaseRepository


class PromptCache:
    """In-memory cache with SHA-256 semantic keys to avoid re-generating identical requests."""

    def __init__(self, ttl_seconds: int = 3600):
        self._cache: Dict[str, Tuple[float, Any]] = {}
        self.ttl = ttl_seconds

    def _make_key(self, prompt: str, system_prompt: Optional[str], task_type: str) -> str:
        raw = f"{task_type}|{system_prompt or ''}|{prompt}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def get(self, prompt: str, system_prompt: Optional[str], task_type: str) -> Optional[Any]:
        key = self._make_key(prompt, system_prompt, task_type)
        if key in self._cache:
            ts, val = self._cache[key]
            if time.time() - ts < self.ttl:
                return val
            else:
                del self._cache[key]
        return None

    def set(self, prompt: str, system_prompt: Optional[str], task_type: str, value: Any):
        key = self._make_key(prompt, system_prompt, task_type)
        self._cache[key] = (time.time(), value)


prompt_cache = PromptCache()


class QuotaEngine:
    """
    Usage / Cost / Quota Engine & Budget Guard (Phase U19).
    Monitors token consumption, enforces monthly budget caps, and prevents wasteful jobs.
    """

    def __init__(self):
        self.usage_repo = BaseRepository[AIUsageEvent](AIUsageEvent)
        self.quota_repo = BaseRepository[UserQuota](UserQuota)

    async def get_or_create_user_quota(self, db: AsyncSession, user_id: str) -> UserQuota:
        await db.execute(update(User).where(User.id == user_id).values(updated_at=User.updated_at).execution_options(synchronize_session=False))
        stmt = select(UserQuota).where(UserQuota.user_id == user_id).with_for_update().execution_options(populate_existing=True)
        res = await db.execute(stmt)
        quota = res.scalar_one_or_none()
        if not quota:
            user = await db.get(User, user_id)
            plan = get_plan_entitlements(user.plan if user else "free")
            quota = UserQuota(**{
                "user_id": user_id,
                "monthly_token_limit": plan.monthly_tokens_limit,
                "monthly_cost_limit_usd": plan.monthly_ai_budget_usd,
                "tokens_used_this_month": 0,
                "cost_usd_this_month": 0.0,
                "reset_at": next_month(),
            })
            db.add(quota)
            await db.flush()
        now = datetime.now(timezone.utc)
        boundary = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        reset = quota.reset_at.replace(tzinfo=quota.reset_at.tzinfo or timezone.utc) if quota.reset_at else None
        if reset and reset <= boundary:
            quota.tokens_used_this_month = 0
            quota.cost_usd_this_month = 0
            quota.reset_at = next_month()
        elif not reset or reset < now:
            # Legacy reset_at stored last-reset time; preserve current-period usage.
            quota.reset_at = next_month()
        await db.flush()
        return quota

    async def record_usage_event(
        self,
        db: AsyncSession,
        user_id: Optional[str],
        project_id: Optional[str],
        task_type: str,
        provider: str,
        model: str,
        input_tokens: int,
        output_tokens: int,
        cached_tokens: int,
        estimated_cost_usd: float,
        latency_ms: int,
        status: str = "success",
    ) -> AIUsageEvent:
        event = AIUsageEvent(**{
            "user_id": user_id,
            "project_id": project_id,
            "task_type": task_type,
            "provider": provider,
            "model": model,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "cached_tokens": cached_tokens,
            "total_tokens": input_tokens + output_tokens,
            "estimated_cost_usd": estimated_cost_usd,
            "latency_ms": latency_ms,
            "status": status,
        })

        db.add(event)
        if user_id:
            quota = await self.get_or_create_user_quota(db, user_id)
            await db.execute(update(UserQuota).where(UserQuota.id==quota.id).values(
                tokens_used_this_month=UserQuota.tokens_used_this_month+input_tokens+output_tokens,
                cost_usd_this_month=UserQuota.cost_usd_this_month+estimated_cost_usd))
        await db.flush()

        return event

    def estimate_workload(
        self,
        job_type: str,
        num_sections: int = 5,
        num_sources: int = 4
    ) -> Dict[str, Any]:
        """Estimates expected tokens and cost before initiating major AI pipelines."""
        if job_type in ["auto_create", "deep_research"]:
            expected_input_tokens = (num_sources * 1500) + (num_sections * 800) + 2000
            expected_output_tokens = (num_sections * 900) + 1500
        else:
            expected_input_tokens = 1200
            expected_output_tokens = 600

        total_tokens = expected_input_tokens + expected_output_tokens
        estimated_cost = (expected_input_tokens / 1_000_000.0 * 0.075) + (expected_output_tokens / 1_000_000.0 * 0.30)

        return {
            "job_type": job_type,
            "expected_input_tokens": expected_input_tokens,
            "expected_output_tokens": expected_output_tokens,
            "expected_total_tokens": total_tokens,
            "estimated_cost_usd": round(estimated_cost, 5),
        }

    async def check_budget_guard(
        self,
        db: AsyncSession,
        user_id: str,
        job_type: str,
        num_sections: int = 5,
        num_sources: int = 4
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Budget Guard: Enforces quota checks prior to executing resource-intensive operations.
        Returns: (is_allowed, reason_or_message, workload_estimate)
        """
        workload = self.estimate_workload(job_type, num_sections, num_sources)
        quota = await self.get_or_create_user_quota(db, user_id)

        projected_cost = quota.cost_usd_this_month + workload["estimated_cost_usd"]
        projected_tokens = quota.tokens_used_this_month + workload["expected_total_tokens"]

        if projected_cost > quota.monthly_cost_limit_usd:
            return (
                False,
                f"Vượt quá hạn mức ngân sách tháng (${quota.monthly_cost_limit_usd:.2f} USD). Hiện tại đã dùng ${quota.cost_usd_this_month:.2f} USD.",
                workload
            )

        if projected_tokens > quota.monthly_token_limit:
            return (
                False,
                f"Vượt quá hạn mức token tháng ({quota.monthly_token_limit:,} tokens). Hiện tại đã dùng {quota.tokens_used_this_month:,} tokens.",
                workload
            )

        return (True, "Ngân sách khả dụng.", workload)

    async def get_user_summary(self, db: AsyncSession, user_id: str) -> Dict[str, Any]:
        quota = await self.get_or_create_user_quota(db, user_id)

        project_ids = select(Project.id).where(Project.user_id == user_id)
        reports_count = await db.scalar(select(func.count()).select_from(Report).where(Report.project_id.in_(project_ids))) or 0
        sources_count = await db.scalar(select(func.count()).select_from(Source).where(Source.project_id.in_(project_ids))) or 0
        storage_bytes = await db.scalar(select(func.sum(UploadedFile.file_size)).where(UploadedFile.project_id.in_(project_ids))) or 0
        exports_count = await db.scalar(select(func.count()).select_from(ExportRecord).join(Report, ExportRecord.report_id == Report.id).where(Report.project_id.in_(project_ids))) or 0
        return {
            "monthly_token_limit": quota.monthly_token_limit,
            "tokens_used_this_month": quota.tokens_used_this_month,
            "monthly_cost_limit_usd": quota.monthly_cost_limit_usd,
            "cost_usd_this_month": round(quota.cost_usd_this_month, 4),
            "remaining_budget_usd": round(max(0.0, quota.monthly_cost_limit_usd - quota.cost_usd_this_month), 4),
            "documents_generated": reports_count, "research_sources_count": sources_count,
            "storage_used_mb": round(storage_bytes / 1048576, 4), "exports_count": exports_count,
        }


quota_engine = QuotaEngine()
