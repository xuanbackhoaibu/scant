import httpx
from typing import Any, AsyncGenerator, Dict, List, Optional
from app.core.config import settings
from app.services.ai.base import AIProvider


class OpenAIProvider(AIProvider):
    """OpenAI API Provider implementation."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.default_model = "gpt-4o-mini"
        self.base_url = "https://api.openai.com/v1/chat/completions"

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,
    ) -> Dict[str, Any]:
        target_model = model or self.default_model

        if not self.api_key:
            if not settings.allow_ai_offline_fallback:
                raise RuntimeError("OPENAI_API_KEY is required when AI offline fallback is disabled.")
            from app.services.ai.gemini_provider import GeminiProvider
            return GeminiProvider()._mock_academic_fallback(prompt, response_format)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload: Dict[str, Any] = {
            "model": target_model,
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        if response_format == "json":
            payload["response_format"] = {"type": "json_object"}

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(self.base_url, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()
            choice = data["choices"][0]
            text = choice["message"]["content"]
            tokens_used = data.get("usage", {}).get("total_tokens", len(text) // 4)

            return {
                "text": text,
                "tokens_used": tokens_used,
                "provider": "openai",
                "model": target_model,
            }

    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        res = await self.generate(prompt, system_prompt, model, temperature, max_tokens)
        words = res.get("text", "").split(" ")
        for i in range(0, len(words), 6):
            yield " ".join(words[i : i + 6]) + " "
