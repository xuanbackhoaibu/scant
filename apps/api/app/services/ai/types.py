from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AITaskType(str, Enum):
    CLASSIFICATION = "CLASSIFICATION"
    INTENT_DETECTION = "INTENT_DETECTION"
    REWRITE = "REWRITE"
    SUMMARIZATION = "SUMMARIZATION"
    OUTLINE = "OUTLINE"
    RESEARCH_QUERY = "RESEARCH_QUERY"
    RESEARCH_SYNTHESIS = "RESEARCH_SYNTHESIS"
    SECTION_WRITING = "SECTION_WRITING"
    FACT_CHECK = "FACT_CHECK"
    DATA_NARRATIVE = "DATA_NARRATIVE"
    DOCUMENT_REVIEW = "DOCUMENT_REVIEW"
    AGENT_REASONING = "AGENT_REASONING"
    EMBEDDING = "EMBEDDING"


class AIProviderType(str, Enum):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"


class AIUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class AIRequest(BaseModel):
    task_type: AITaskType
    prompt: str
    system_prompt: Optional[str] = None
    response_format: str = "text"  # "text" | "json"
    temperature: float = 0.3
    max_tokens: Optional[int] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    plan_tier: str = "pro"  # "free" | "pro" | "team" | "enterprise"
    quality_requirement: str = "standard"  # "fast" | "standard" | "high"
    preferred_provider: Optional[AIProviderType] = None
    preferred_model: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AIResponse(BaseModel):
    text: str
    task_type: AITaskType
    provider: str
    model: str
    usage: AIUsage
    latency_ms: int = 0
    cached: bool = False
    failover_applied: bool = False
