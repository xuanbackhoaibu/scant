from app.services.research.academic.base import AcademicProvider, ResearchSourceModel
from app.services.research.academic.crossref_provider import CrossrefProvider
from app.services.research.academic.arxiv_provider import ArxivProvider
from app.services.research.academic.semantic_scholar_provider import SemanticScholarProvider
from app.services.research.academic.pubmed_provider import PubMedProvider
from app.services.research.academic.openalex_provider import OpenAlexProvider
from app.services.research.academic.microsoft_learn_provider import MicrosoftLearnProvider

__all__ = [
    "AcademicProvider",
    "ResearchSourceModel",
    "CrossrefProvider",
    "ArxivProvider",
    "SemanticScholarProvider",
    "PubMedProvider",
    "OpenAlexProvider",
    "MicrosoftLearnProvider",
]
