from abc import ABC, abstractmethod
from typing import Any, AsyncGenerator, Dict, List, Optional


class AIProvider(ABC):
    """Abstract Interface for Multi-Provider AI Engine."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        response_format: Optional[str] = None,  # text or json
    ) -> Dict[str, Any]:
        """Generate text completion from prompt."""
        pass

    @abstractmethod
    async def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> AsyncGenerator[str, None]:
        """Stream generated text chunks asynchronously."""
        pass
