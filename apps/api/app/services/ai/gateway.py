import asyncio
import random
import time
from typing import Any, Dict, Optional
from app.services.ai.types import AIRequest, AIResponse, AIUsage, AIProviderType
from app.services.ai.model_router import model_router
from app.services.ai.provider_factory import ai_factory
from app.services.observability.metrics_collector import metrics_collector


class AIGateway:
    """
    Central Production AI Gateway (Phase U18).
    Handles Model Routing, Provider Failover, Exponential Backoff with Jitter, and Usage Tracking.
    """

    MAX_PRIMARY_RETRIES = 1
    INITIAL_BACKOFF_SECONDS = 0.5

    @classmethod
    async def execute(cls, request: AIRequest) -> AIResponse:
        from app.core.usage_context import usage_user_id
        if not request.user_id and usage_user_id.get():
            request=request.model_copy(update={"user_id":usage_user_id.get()})
        started=time.monotonic()
        try:
            response=await cls._execute(request)
        except Exception:
            await cls._persist_usage(request,None,started)
            raise
        if not response.is_demo:
            await cls._persist_usage(request,response,started)
        return response

    @classmethod
    async def _persist_usage(cls,request,response,started):
        from app.core.database import AsyncSessionLocal
        from app.services.usage.quota_engine import quota_engine
        from app.models.entities import User
        # Outside the provider retry loop: telemetry errors cannot replay paid calls.
        try:
            async with AsyncSessionLocal() as db:
                user_id=request.user_id if request.user_id and await db.get(User,request.user_id) else None
                await quota_engine.record_usage_event(db,user_id,request.project_id,request.task_type.value,
                    response.provider if response else 'unavailable',response.model if response else 'unavailable',
                    response.usage.prompt_tokens if response else 0,response.usage.completion_tokens if response else 0,
                    response.usage.cached_tokens if response else 0,response.usage.estimated_cost_usd if response else 0,
                    int((time.monotonic()-started)*1000),'success' if response else 'failed')
                await db.commit()
        except Exception:
            import logging
            logging.getLogger(__name__).error('AI usage persistence failed; provider result was not replayed')

    @classmethod
    async def _execute(cls, request: AIRequest) -> AIResponse:
        from app.core.database import AsyncSessionLocal
        from app.services.admin.configuration_service import gateway_config
        async with AsyncSessionLocal() as db:
            config, route = await gateway_config(db, request)
            if request.user_id:
                from app.models.entities import User
                from app.services.usage.quota_engine import quota_engine
                user=await db.get(User,request.user_id)
                if not user or not user.is_active:
                    raise RuntimeError('AI request account is unavailable')
                quota=await quota_engine.get_or_create_user_quota(db,user.id)
                if quota.tokens_used_this_month>=quota.monthly_token_limit or quota.cost_usd_this_month>=quota.monthly_cost_limit_usd:
                    raise RuntimeError('Monthly AI quota exceeded')
                await db.commit()
        start_time = time.time()

        # 1. Try Primary Provider with retry
        primary_provider = ai_factory.get_provider(route.primary_provider.value)
        last_error = None
        failover_used = False

        for attempt in range(config["primary_retries"] + 1):
            try:
                res = await asyncio.wait_for(primary_provider.generate(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    model=route.primary_model,
                    temperature=request.temperature,
                    max_tokens=request.max_tokens or 4096,
                    response_format=request.response_format,
                ), timeout=config["timeout_seconds"])
                latency_ms = int((time.time() - start_time) * 1000)
                metrics_collector.record_ai_request(latency_ms, success=True)
                return cls._build_response(request, route.primary_provider.value, route.primary_model, res, latency_ms, False)
            except Exception as e:
                last_error = e
                if attempt < config["primary_retries"]:
                    jitter = random.uniform(0.1, 0.3)
                    await asyncio.sleep(cls.INITIAL_BACKOFF_SECONDS * (2 ** attempt) + jitter)

        # 2. Primary failed -> Trigger Automatic Failover
        try:
            fallback_provider = ai_factory.get_provider(route.fallback_provider.value)
            res = await asyncio.wait_for(fallback_provider.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                model=route.fallback_model,
                temperature=request.temperature,
                max_tokens=request.max_tokens or 4096,
                response_format=request.response_format,
            ), timeout=config["timeout_seconds"])
            latency_ms = int((time.time() - start_time) * 1000)
            metrics_collector.record_ai_request(latency_ms, success=True)
            return cls._build_response(request, route.fallback_provider.value, route.fallback_model, res, latency_ms, True)
        except Exception as fallback_error:
            # If fallback also fails, raise clear gateway error
            latency_ms = int((time.time() - start_time) * 1000)
            metrics_collector.record_ai_request(latency_ms, success=False)
            raise RuntimeError(f"AI Gateway Error: Primary ({str(last_error)}) and Fallback ({str(fallback_error)}) both failed.")

    @classmethod
    def _build_response(
        cls,
        request: AIRequest,
        provider_name: str,
        model_name: str,
        raw_res: Dict[str, Any],
        latency_ms: int,
        failover_applied: bool
    ) -> AIResponse:
        text = raw_res.get("text", "")
        raw_usage = raw_res.get("usage", {})

        p_tokens = raw_usage.get("prompt_tokens") if raw_usage.get("prompt_tokens") is not None else (len(request.prompt) // 4)
        c_tokens = raw_usage.get("completion_tokens") if raw_usage.get("completion_tokens") is not None else (len(text) // 4)
        tot_tokens = p_tokens + c_tokens
        cost = model_router.calculate_cost(model_name, p_tokens, c_tokens)

        usage = AIUsage(
            prompt_tokens=p_tokens,
            completion_tokens=c_tokens,
            cached_tokens=0,
            total_tokens=tot_tokens,
            estimated_cost_usd=cost,
        )

        return AIResponse(
            text=text,
            is_demo=bool(raw_res.get("is_demo", False)),
            task_type=request.task_type,
            provider=provider_name,
            model=model_name,
            usage=usage,
            latency_ms=latency_ms,
            cached=False,
            failover_applied=failover_applied,
        )


ai_gateway = AIGateway()
