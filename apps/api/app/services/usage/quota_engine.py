import hashlib
import time
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models.entities import AIUsageEvent, UserQuota, Report, Source, UploadedFile
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
        stmt = select(UserQuota).where(UserQuota.user_id == user_id)
        res = await db.execute(stmt)
        quota = res.scalar_one_or_none()
        if not quota:
            quota = await self.quota_repo.create(db, obj_in={
                "user_id": user_id,
                "monthly_token_limit": 1_000_000,
                "monthly_cost_limit_usd": 20.0,
                "tokens_used_this_month": 0,
                "cost_usd_this_month": 0.0,
            })
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
        event = await self.usage_repo.create(db, obj_in={
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

        if user_id:
            quota = await self.get_or_create_user_quota(db, user_id)
            await self.quota_repo.update(db, db_obj=quota, obj_in={
                "tokens_used_this_month": quota.tokens_used_this_month + input_tokens + output_tokens,
                "cost_usd_this_month": quota.cost_usd_this_month + estimated_cost_usd,
            })

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

        # Count generated reports
        rep_stmt = select(func.count(Report.id)).where(Report.project_id.in_(
            select(Report.project_id)
        ))
        rep_count_res = await db.execute(rep_stmt)
        reports_count = rep_count_res.scalar() or 0

        # Count sources
        src_stmt = select(func.count(Source.id))
        src_count_res = await db.execute(src_stmt)
        sources_count = src_count_res.scalar() or 0

        return {
            "monthly_token_limit": quota.monthly_token_limit,
            "tokens_used_this_month": quota.tokens_used_this_month,
            "monthly_cost_limit_usd": quota.monthly_cost_limit_usd,
            "cost_usd_this_month": round(quota.cost_usd_this_month, 4),
            "remaining_budget_usd": round(max(0.0, quota.monthly_cost_limit_usd - quota.cost_usd_this_month), 4),
            "documents_generated": reports_count,
            "research_sources_count": sources_count,
            "storage_used_mb": 14.5,
            "exports_count": 8,
        }


quota_engine = QuotaEngine()
