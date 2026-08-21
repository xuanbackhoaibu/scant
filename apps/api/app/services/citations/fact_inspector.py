import json
import re
from typing import Any, Dict, List, Optional
from app.services.ai.provider_factory import ai_factory


class FactInspector:
    """
    Evidence Board & Fact Inspector Engine.
    Detects factual & numerical assertions in text and validates them against verified sources and datasets.
    """

    @classmethod
    async def inspect_facts(
        cls,
        text: str,
        sources: List[Dict[str, Any]],
        dataset_summaries: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        if not text or len(text.strip()) < 10:
            return {
                "claims": [],
                "overall_factual_score": 100,
                "verified_claims_count": 0,
                "unsupported_claims_count": 0
            }

        # Format sources into context
        src_context = "\n".join([f"[{i+1}] {s.get('title')}: {s.get('summary', '')}" for i, s in enumerate(sources)])
        dataset_context = "\n".join(dataset_summaries or [])

        provider = ai_factory.get_provider()
        system_prompt = (
            "Bạn là một Senior Fact-Checking Inspector & Claim Validator. "
            "Nhiệm vụ của bạn là rà soát từng luận điểm, con số, tỷ lệ phần trăm hoặc khẳng định dữ liệu trong văn bản. "
            "Đối chiếu từng luận điểm với Nguồn đã kiểm chứng và Dữ liệu thực tế. "
            "Bắt buộc phân loại mỗi luận điểm thành 1 trong 4 trạng thái: "
            "'verified' (có nguồn xác thực), 'unsupported' (không có nguồn chứng minh), "
            "'contradicted' (mâu thuẫn với số liệu nguồn), hoặc 'general_statement' (nhận định chung không cần nguồn). "
            "Trả về JSON với các khóa: claims (array of {claim_text, status, confidence, explanation, citation_source}), overall_factual_score (0-100)."
        )

        user_prompt = f"""
VĂN BẢN CẦN KIỂM ĐỊNH:
"{text}"

DANH MỤC NGUỒN XÁC THỰC:
{src_context or 'Chưa có nguồn xác thực nào.'}

DỮ LIỆU TẬP TIN:
{dataset_context or 'Chưa có tập dữ liệu số liệu.'}

Hãy phân tích và trả về JSON kết quả kiểm định sự thật.
"""

        res = await provider.generate(
            prompt=user_prompt,
            system_prompt=system_prompt,
            response_format="json",
            temperature=0.2
        )

        raw_text = res.get("text", "{}")
        try:
            data = json.loads(raw_text)
        except Exception:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        claims = data.get("claims", [])
        verified_count = sum(1 for c in claims if c.get("status") == "verified")
        unsupported_count = sum(1 for c in claims if c.get("status") in ["unsupported", "contradicted"])

        return {
            "claims": claims,
            "overall_factual_score": data.get("overall_factual_score", 90),
            "verified_claims_count": verified_count,
            "unsupported_claims_count": unsupported_count,
            "total_claims_count": len(claims),
        }


fact_inspector = FactInspector()
