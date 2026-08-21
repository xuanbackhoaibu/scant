import asyncio
import random
import time
from typing import Any, Dict, Optional
from app.services.ai.types import AIRequest, AIResponse, AIUsage, AIProviderType
from app.services.ai.model_router import model_router
from app.services.ai.provider_factory import ai_factory


class AIGateway:
    """
    Central Production AI Gateway (Phase U18).
    Handles Model Routing, Provider Failover, Exponential Backoff with Jitter, and Usage Tracking.
    """

    MAX_PRIMARY_RETRIES = 1
    INITIAL_BACKOFF_SECONDS = 0.5

    @classmethod
    async def execute(cls, request: AIRequest) -> AIResponse:
        route = model_router.resolve_route(request)
        start_time = time.time()

        # 1. Try Primary Provider with retry
        primary_provider = ai_factory.get_provider(route.primary_provider.value)
        last_error = None
        failover_used = False

        for attempt in range(cls.MAX_PRIMARY_RETRIES + 1):
            try:
                res = await primary_provider.generate(
                    prompt=request.prompt,
                    system_prompt=request.system_prompt,
                    temperature=request.temperature,
                    response_format=request.response_format,
                )
                latency_ms = int((time.time() - start_time) * 1000)
                return cls._build_response(request, route.primary_provider.value, route.primary_model, res, latency_ms, False)
            except Exception as e:
                last_error = e
                if attempt < cls.MAX_PRIMARY_RETRIES:
                    jitter = random.uniform(0.1, 0.3)
                    await asyncio.sleep(cls.INITIAL_BACKOFF_SECONDS * (2 ** attempt) + jitter)

        # 2. Primary failed -> Trigger Automatic Failover
        try:
            fallback_provider = ai_factory.get_provider(route.fallback_provider.value)
            res = await fallback_provider.generate(
                prompt=request.prompt,
                system_prompt=request.system_prompt,
                temperature=request.temperature,
                response_format=request.response_format,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            return cls._build_response(request, route.fallback_provider.value, route.fallback_model, res, latency_ms, True)
        except Exception as fallback_error:
            # If fallback also fails, raise clear gateway error
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

        p_tokens = raw_usage.get("prompt_tokens") or (len(request.prompt) // 4)
        c_tokens = raw_usage.get("completion_tokens") or (len(text) // 4)
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
            task_type=request.task_type,
            provider=provider_name,
            model=model_name,
            usage=usage,
            latency_ms=latency_ms,
            cached=False,
            failover_applied=failover_applied,
        )


ai_gateway = AIGateway()
