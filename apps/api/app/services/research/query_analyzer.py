import re
import json
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class DateRange(BaseModel):
    from_year: Optional[int] = Field(default=None, alias="from")
    to_year: Optional[int] = Field(default=None, alias="to")


class QueryAnalysisResult(BaseModel):
    topic: str
    country: Optional[str] = None
    date_range: Optional[DateRange] = None
    entities: List[str] = Field(default_factory=list)
    research_intent: str = "comprehensive_investigation"
    keywords_vi: List[str] = Field(default_factory=list)
    keywords_en: List[str] = Field(default_factory=list)
    preferred_sources: List[str] = Field(default_factory=lambda: ["academic", "government", "market-report", "news"])


class QueryAnalyzer:
    """
    Intelligent Query Understanding and Dual-Language Expansion Engine (Section 2).
    Generates targeted academic & web search queries in both Vietnamese and English.
    """

    async def analyze_and_expand(self, query: str) -> QueryAnalysisResult:
        cleaned_query = query.strip()
        if not cleaned_query:
            return QueryAnalysisResult(topic=query, keywords_vi=[query], keywords_en=[query])

        prompt = f"""Bạn là Research Query Understanding Agent.
Phân tích truy vấn nghiên cứu: "{cleaned_query}"

Hãy trích xuất thông tin dưới định dạng JSON duy nhất (không bọc text giải thích):
{{
  "topic": "chủ đề cốt lõi bằng tiếng Anh hoặc tiếng Việt chuẩn hóa",
  "country": "quốc gia liên quan (ví dụ: Vietnam, Global) hoặc null",
  "date_range": {{"from": 2024, "to": 2026}},
  "entities": ["tổ chức, thương hiệu hoặc công nghệ liên quan"],
  "research_intent": "market_analysis | technical_evaluation | academic_study | policy_review",
  "keywords_vi": [
    "cụm từ tìm kiếm tiếng Việt 1",
    "cụm từ tìm kiếm tiếng Việt 2",
    "cụm từ tìm kiếm tiếng Việt 3"
  ],
  "keywords_en": [
    "English search term 1",
    "English search term 2",
    "English search term 3"
  ],
  "preferred_sources": ["academic", "government", "market-report", "news"]
}}
"""
        try:
            req = AIRequest(
                task_type=AITaskType.RESEARCH_SYNTHESIS,
                prompt=prompt,
            )
            resp = await ai_gateway.execute(req)
            raw_text = resp.text.strip()
            # Extract JSON block
            json_match = re.search(r"\{[\s\S]*\}", raw_text)
            if json_match:
                data = json.loads(json_match.group(0))
                dr_data = data.get("date_range") or {}
                date_range = DateRange(from_year=dr_data.get("from"), to_year=dr_data.get("to")) if dr_data else None

                return QueryAnalysisResult(
                    topic=data.get("topic") or cleaned_query,
                    country=data.get("country"),
                    date_range=date_range,
                    entities=data.get("entities") or [],
                    research_intent=data.get("research_intent") or "comprehensive_investigation",
                    keywords_vi=data.get("keywords_vi") or [cleaned_query],
                    keywords_en=data.get("keywords_en") or [cleaned_query],
                    preferred_sources=data.get("preferred_sources") or ["academic", "government", "market-report"],
                )
        except Exception:
            pass

        # Rule-based Fallback Expansion
        return self._rule_based_fallback(cleaned_query)

    def _rule_based_fallback(self, query: str) -> QueryAnalysisResult:
        country = "Vietnam" if any(k in query.lower() for k in ["việt nam", "vietnam", "vn"]) else None
        years = re.findall(r"\b(20\d{2})\b", query)
        date_range = None
        if years:
            int_years = [int(y) for y in years]
            date_range = DateRange(from_year=min(int_years), to_year=max(int_years))

        # Basic Vietnamese to English term mappings
        translations = {
            "xe điện": "electric vehicle EV",
            "thị trường": "market analysis",
            "năng lượng tái tạo": "renewable energy",
            "trí tuệ nhân tạo": "artificial intelligence AI",
            "ngân hàng số": "digital banking fintech",
            "kinh tế số": "digital economy",
            "chính sách": "policy government regulation",
            "y tế": "healthcare medicine",
        }
        en_query = query
        for vi, en in translations.items():
            if vi in en_query.lower():
                en_query = re.sub(vi, en, en_query, flags=re.I)

        keywords_vi = [
            query,
            f"báo cáo {query}",
            f"thực trạng {query}",
        ]
        keywords_en = [
            en_query,
            f"{en_query} overview",
            f"{en_query} report",
        ]

        return QueryAnalysisResult(
            topic=query,
            country=country,
            date_range=date_range,
            entities=[],
            keywords_vi=keywords_vi,
            keywords_en=keywords_en,
            preferred_sources=["academic", "government", "market-report", "news"],
        )


query_analyzer = QueryAnalyzer()
