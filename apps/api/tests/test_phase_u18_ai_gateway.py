import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch
from app.services.ai.types import AIRequest, AITaskType, AIProviderType, AIResponse
from app.services.ai.model_router import model_router
from app.services.ai.gateway import ai_gateway
from app.services.editor.outline_service import outline_service
from app.schemas.ai import AnalyzeIntentRequest


def test_model_router_resolutions():
    # Classification / Intent -> Fast cheap model
    route_class = model_router.resolve_route(
        AIRequest(task_type=AITaskType.CLASSIFICATION, prompt="Phân loại yêu cầu")
    )
    assert route_class.primary_model == "gemini-2.5-flash"
    assert route_class.fallback_model == "gpt-4o-mini"

    # Agent Reasoning -> Strong model
    route_agent = model_router.resolve_route(
        AIRequest(task_type=AITaskType.AGENT_REASONING, prompt="Lập kế hoạch phân tích đa bước")
    )
    assert route_agent.primary_provider == AIProviderType.GEMINI

    # Cost Calculation
    cost = model_router.calculate_cost("gemini-2.5-flash", prompt_tokens=1000, completion_tokens=500)
    assert cost > 0.0


@pytest.mark.asyncio
async def test_ai_gateway_execute_success():
    req = AIRequest(
        task_type=AITaskType.SECTION_WRITING,
        prompt="Viết phần tổng quan dự án",
        temperature=0.3,
    )
    res = await ai_gateway.execute(req)
    assert isinstance(res, AIResponse)
    assert res.task_type == AITaskType.SECTION_WRITING
    assert res.usage.prompt_tokens > 0
    assert res.usage.completion_tokens > 0
    assert res.latency_ms >= 0
    assert res.failover_applied is False


@pytest.mark.asyncio
async def test_ai_gateway_failover_mechanism():
    req = AIRequest(
        task_type=AITaskType.FACT_CHECK,
        prompt="Kiểm tra thông tin doanh thu 500 tỷ",
        temperature=0.2,
    )

    # Mock primary provider failure so gateway automatically fails over to secondary
    with patch("app.services.ai.gemini_provider.GeminiProvider.generate", side_effect=Exception("Gemini 429 Rate Limit")):
        res = await ai_gateway.execute(req)
        assert res.failover_applied is True
        assert res.provider == "openai"
        assert res.model == "gpt-4o-mini"
        assert len(res.text) > 0


@pytest.mark.asyncio
async def test_outline_service_via_gateway():
    res = await outline_service.analyze_intent(
        AnalyzeIntentRequest(user_prompt="Báo cáo kiểm toán bảo mật hệ thống ngân hàng số")
    )
    assert res.suggested_title is not None
    assert len(res.key_themes) > 0
