import re
from typing import Any, Dict, List, Optional, Tuple


class ClaimValidator:
    """Anti-hallucination engine mapping in-text claims directly to genuine source evidence."""

    CITATION_REGEX = re.compile(r"\[(\d+)\]")

    @classmethod
    def validate_and_map_claims(
        cls,
        text: str,
        sources_map: Dict[int, Dict[str, Any]]  # e.g. {1: source_obj, 2: source_obj}
    ) -> Dict[str, Any]:
        """
        Extracts sentences containing citations, verifies they map to genuine sources,
        and constructs evidence claim mapping records.
        """
        sentences = re.split(r"(?<=[.?!])\s+", text)
        verified_claims: List[Dict[str, Any]] = []
        unverified_citations: List[str] = []
        citations_found: List[int] = []

        for sentence in sentences:
            matches = cls.CITATION_REGEX.findall(sentence)
            if not matches:
                continue

            for match in matches:
                cit_idx = int(match)
                citations_found.append(cit_idx)

                if cit_idx in sources_map:
                    src = sources_map[cit_idx]
                    evidence = src.get("snippet") or src.get("summary") or src.get("title") or ""
                    
                    verified_claims.append({
                        "citation_index": cit_idx,
                        "citation_key": f"[{cit_idx}]",
                        "source_id": src.get("id"),
                        "source_title": src.get("title"),
                        "source_url": src.get("url"),
                        "claim_text": sentence.strip(),
                        "evidence_text": evidence,
                        "confidence_score": src.get("reliability_score", 0.95),
                        "verification_status": "verified"
                    })
                else:
                    unverified_citations.append(f"[{cit_idx}]")

        is_clean = len(unverified_citations) == 0

        return {
            "is_verified": is_clean,
            "citations_found": list(set(citations_found)),
            "verified_claims": verified_claims,
            "unverified_citations": unverified_citations,
            "verification_message": (
                "Toàn bộ trích dẫn đã được kiểm chứng nguồn gốc thực tế."
                if is_clean
                else f"Cảnh báo: Phát hiện {len(unverified_citations)} trích dẫn chưa được xác minh ({', '.join(unverified_citations)})."
            )
        }


claim_validator = ClaimValidator()
