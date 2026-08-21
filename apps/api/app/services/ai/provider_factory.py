from typing import Optional
from app.core.config import settings
from app.services.ai.base import AIProvider
from app.services.ai.gemini_provider import GeminiProvider
from app.services.ai.openai_provider import OpenAIProvider


class AIProviderFactory:
    """Factory for resolving AI providers dynamically."""

    @staticmethod
    def get_provider(provider_name: Optional[str] = None) -> AIProvider:
        name = (provider_name or settings.DEFAULT_AI_PROVIDER or "gemini").lower()
        if name == "openai":
            return OpenAIProvider()
        # Default to GeminiProvider
        return GeminiProvider()


ai_factory = AIProviderFactory()
