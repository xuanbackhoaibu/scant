from typing import Dict, List, Optional, Tuple
from app.services.ai.types import AIRequest, AITaskType, AIProviderType


class ModelRoute:
    def __init__(self, primary_provider: AIProviderType, primary_model: str, fallback_provider: AIProviderType, fallback_model: str):
        self.primary_provider = primary_provider
        self.primary_model = primary_model
        self.fallback_provider = fallback_provider
        self.fallback_model = fallback_model


class ModelRouter:
    """
    Intelligent Model Router (Phase U18).
    Selects optimal models and failover targets based on task type, tier, and quality needs.
    """

    # Rates per 1M tokens in USD: (prompt_rate, completion_rate)
    TOKEN_PRICING: Dict[str, Tuple[float, float]] = {
        "gemini-2.5-flash": (0.075, 0.30),
        "gemini-2.5-pro": (1.25, 5.00),
        "gpt-4o-mini": (0.15, 0.60),
        "gpt-4o": (2.50, 10.00),
        "claude-3-5-sonnet": (3.00, 15.00),
        "default": (0.10, 0.40),
    }

    # Routing matrix
    ROUTING_MATRIX: Dict[AITaskType, ModelRoute] = {
        # Cheap / Ultra-fast tasks
        AITaskType.CLASSIFICATION: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.INTENT_DETECTION: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.RESEARCH_QUERY: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),

        # Fast / Efficient tasks
        AITaskType.REWRITE: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.SUMMARIZATION: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),

        # Balanced writing & data tasks
        AITaskType.OUTLINE: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.SECTION_WRITING: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.DATA_NARRATIVE: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),

        # High-reasoning & research synthesis
        AITaskType.RESEARCH_SYNTHESIS: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.FACT_CHECK: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.DOCUMENT_REVIEW: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.AGENT_REASONING: ModelRoute(
            AIProviderType.GEMINI, "gemini-2.5-flash",
            AIProviderType.OPENAI, "gpt-4o-mini"
        ),
        AITaskType.EMBEDDING: ModelRoute(
            AIProviderType.GEMINI, "text-embedding-004",
            AIProviderType.OPENAI, "text-embedding-3-small"
        ),
    }

    @classmethod
    def resolve_route(cls, request: AIRequest) -> ModelRoute:
        if request.preferred_provider and request.preferred_model:
            return ModelRoute(
                request.preferred_provider,
                request.preferred_model,
                AIProviderType.OPENAI if request.preferred_provider == AIProviderType.GEMINI else AIProviderType.GEMINI,
                "gpt-4o-mini" if request.preferred_provider == AIProviderType.GEMINI else "gemini-2.5-flash"
            )

        route = cls.ROUTING_MATRIX.get(
            request.task_type,
            ModelRoute(AIProviderType.GEMINI, "gemini-2.5-flash", AIProviderType.OPENAI, "gpt-4o-mini")
        )
        return route

    @classmethod
    def calculate_cost(cls, model_name: str, prompt_tokens: int, completion_tokens: int) -> float:
        prompt_rate, completion_rate = cls.TOKEN_PRICING.get(model_name, cls.TOKEN_PRICING["default"])
        cost = (prompt_tokens / 1_000_000.0 * prompt_rate) + (completion_tokens / 1_000_000.0 * completion_rate)
        return round(cost, 7)


model_router = ModelRouter()
