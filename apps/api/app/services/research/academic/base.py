from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone


class ResearchSourceModel(BaseModel):
    """
    Standardized Research Source model (Section 6 & 23).
    All providers (academic, government, market, web) normalize to this structure.
    """
    id: str = Field(..., description="Unique source identifier")
    source_type: str = Field(
        default="academic",
        description="academic | government | market | news | company | organization | web"
    )
    title: str
    authors: List[str] = Field(default_factory=list)
    publisher: Optional[str] = None
    journal: Optional[str] = None
    published_at: Optional[str] = None
    year: Optional[int] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    pmid: Optional[str] = None
    url: str
    abstract: Optional[str] = None
    snippet: Optional[str] = None
    citation_count: Optional[int] = None
    referenced_by_count: Optional[int] = None
    open_access: bool = False
    pdf_url: Optional[str] = None
    provider: str = Field(
        default="crossref",
        description="crossref | semantic-scholar | arxiv | pubmed | web | tavily"
    )
    metadata_verified: bool = False
    url_verified: bool = False
    retrieved_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    # Quality Scoring & Authority
    quality_score: float = Field(default=0.0, description="Score from 0 to 100 calculated by algorithm")
    quality_breakdown: Dict[str, float] = Field(default_factory=dict)
    authority_type: str = Field(default="unknown")
    verification_badges: List[str] = Field(default_factory=list)


class AcademicProvider(ABC):
    """Common interface for all academic providers (Section 3)."""

    name: str = "academic_provider"

    @abstractmethod
    async def search(self, query: str, limit: int = 10, **kwargs) -> List[ResearchSourceModel]:
        """Search academic repository and return normalized ResearchSourceModel objects."""
        pass
