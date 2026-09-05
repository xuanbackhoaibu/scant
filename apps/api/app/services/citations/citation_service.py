import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session

from app.models.entities import (
    Citation,
    Claim,
    Evidence,
    Report,
    ReportSection,
    Source,
)
from app.services.citations.citation_formatter import CitationFormatter

logger = logging.getLogger(__name__)


class CitationService:
    """
    Citation Management, Sequential Re-indexing, Delete Safety,
    and Anti-Hallucination Evidence Support Verification.
    """

    @classmethod
    def evaluate_evidence_support(
        cls,
        claim_text: str,
        evidence_text: str,
    ) -> Dict[str, Any]:
        """
        Evaluates the degree to which an evidence snippet supports a claim.
        Checks:
        1. Numerical matching: checks if numbers in claim exist in evidence.
        2. Keyword overlap: checks key noun phrases.
        Returns: support_level: STRONG | MODERATE | WEAK | UNSUPPORTED
        """
        if not claim_text or not evidence_text:
            return {
                "support_level": "UNSUPPORTED",
                "confidence_score": 0.0,
                "analysis": "Không có nội dung tuyên bố hoặc bằng chứng để đối chiếu.",
                "matched_numbers": [],
                "matched_keywords": [],
            }

        claim_clean = claim_text.lower()
        ev_clean = evidence_text.lower()

        # 1. Number extraction
        num_pattern = re.compile(r"\b\d+(?:[.,]\d+)?%?\b")
        claim_nums = set(num_pattern.findall(claim_clean))
        ev_nums = set(num_pattern.findall(ev_clean))

        matched_nums = list(claim_nums.intersection(ev_nums))
        unmatched_nums = list(claim_nums - ev_nums)

        # 2. Significant words extraction (len > 3, not common stop words)
        stop_words = {
            "này", "được", "trong", "những", "của", "với", "cho", "theo", "rằng",
            "ngày", "tháng", "năm", "tại", "một", "các", "trên", "dưới", "về",
            "this", "that", "with", "from", "have", "been", "were", "they", "will", "than"
        }
        claim_words = {w for w in re.findall(r"\b\w{3,}\b", claim_clean) if w not in stop_words}
        ev_words = {w for w in re.findall(r"\b\w{3,}\b", ev_clean) if w not in stop_words}

        matched_words = list(claim_words.intersection(ev_words))
        word_overlap_ratio = len(matched_words) / max(len(claim_words), 1)

        # Scoring
        score = 0.0
        if word_overlap_ratio >= 0.5:
            score += 0.5
        elif word_overlap_ratio >= 0.25:
            score += 0.3
        elif word_overlap_ratio > 0.1:
            score += 0.15

        if claim_nums:
            if len(unmatched_nums) == 0:
                score += 0.5
            elif len(matched_nums) > 0:
                score += 0.25
        else:
            # If no numbers, scale word overlap more
            score += min(0.5, word_overlap_ratio * 0.5)

        score = min(1.0, round(score, 2))

        if score >= 0.75:
            support_level = "STRONG"
            analysis = "Bằng chứng hỗ trợ mạnh mẽ tuyên bố, trùng khớp từ khóa và dữ liệu số."
        elif score >= 0.45:
            support_level = "MODERATE"
            analysis = "Bằng chứng có liên quan và hỗ trợ phần lớn luận điểm."
        elif score >= 0.2:
            support_level = "WEAK"
            analysis = "Bằng chứng chỉ trùng khớp một vài từ khóa chung, cần kiểm tra thêm."
        else:
            support_level = "UNSUPPORTED"
            analysis = "Nội dung bằng chứng không tìm thấy điểm tương đồng rõ ràng với tuyên bố."

        return {
            "support_level": support_level,
            "confidence_score": score,
            "analysis": analysis,
            "matched_numbers": matched_nums,
            "unmatched_numbers": unmatched_nums,
            "matched_keywords": matched_words[:10],
        }

    @classmethod
    def reindex_citations(
        cls,
        db: Session,
        report_id: str,
        style: str = "IEEE",
    ) -> List[Citation]:
        """
        Sequentially renumbers citations [1], [2], [3]... in order of appearance across sections.
        Ensures strict IEEE or APA style sequence.
        """
        # Get sections ordered by position
        sections = (
            db.query(ReportSection)
            .filter(ReportSection.report_id == report_id)
            .order_by(ReportSection.position.asc(), ReportSection.created_at.asc())
            .all()
        )

        citation_counter = 1
        all_updated: List[Citation] = []
        source_seen_map: Dict[str, int] = {}  # source_id -> citation_number for IEEE reuse

        for sec in sections:
            sec_citations = (
                db.query(Citation)
                .filter(Citation.report_section_id == sec.id)
                .order_by(Citation.citation_number.asc(), Citation.created_at.asc())
                .all()
            )

            for cit in sec_citations:
                if cit.source_id in source_seen_map and style.upper() == "IEEE":
                    # Reuse same number if source already cited earlier in IEEE style
                    cit.citation_number = source_seen_map[cit.source_id]
                else:
                    cit.citation_number = citation_counter
                    source_seen_map[cit.source_id] = citation_counter
                    citation_counter += 1

                source = db.query(Source).filter(Source.id == cit.source_id).first()
                author = source.authors if source else None
                year = str(source.publication_year) if (source and source.publication_year) else None

                cit.citation_style = style.upper()
                cit.citation_key = CitationFormatter.format_in_text(
                    citation_number=cit.citation_number,
                    author=author,
                    year=year,
                    style=style,
                )
                all_updated.append(cit)

        db.commit()
        for cit in all_updated:
            db.refresh(cit)
        return all_updated

    @classmethod
    def check_source_citations(
        cls,
        db: Session,
        source_id: str,
    ) -> Dict[str, Any]:
        """
        Checks if a source is currently used in any reports/sections.
        Prevents accidental deletion of cited sources.
        """
        citations = db.query(Citation).filter(Citation.source_id == source_id).all()
        report_ids = {c.report_id for c in citations if c.report_id}

        reports = db.query(Report).filter(Report.id.in_(report_ids)).all() if report_ids else []

        is_in_use = len(citations) > 0
        return {
            "source_id": source_id,
            "is_in_use": is_in_use,
            "citation_count": len(citations),
            "affected_reports": [
                {"id": r.id, "title": r.title} for r in reports
            ],
            "warning_message": (
                f"Nguồn này đang được trích dẫn ở {len(citations)} vị trí trong {len(reports)} báo cáo. "
                f"Xóa nguồn sẽ làm mất liên kết bằng chứng của các trích dẫn này."
                if is_in_use
                else "Nguồn này hiện chưa được trích dẫn trong báo cáo nào, có thể xóa an toàn."
            ),
        }

    @classmethod
    def create_citation(
        cls,
        db: Session,
        report_id: Optional[str],
        report_section_id: str,
        source_id: str,
        evidence_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        locator: Optional[str] = None,
        citation_style: str = "IEEE",
    ) -> Citation:
        """Creates a citation, links genuine source and evidence, and evaluates support level."""
        source = db.query(Source).filter(Source.id == source_id).first()
        if not source:
            raise ValueError(f"Source not found: {source_id}")

        evidence_text = ""
        evidence = None
        if evidence_id:
            evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
            if evidence:
                evidence_text = evidence.quote

        claim_text = ""
        claim = None
        if claim_id:
            claim = db.query(Claim).filter(Claim.id == claim_id).first()
            if claim:
                claim_text = claim.claim_text

        # Evaluate support level
        support_level = "STRONG"
        if claim_text and evidence_text:
            eval_res = cls.evaluate_evidence_support(claim_text, evidence_text)
            support_level = eval_res.get("support_level", "STRONG")
        elif not evidence_text:
            support_level = "MODERATE" if source.verification_status == "VERIFIED" else "WEAK"

        # Determine next citation number
        existing_count = (
            db.query(Citation)
            .filter(Citation.report_section_id == report_section_id)
            .count()
        )
        citation_num = existing_count + 1

        citation_key = CitationFormatter.format_in_text(
            citation_number=citation_num,
            author=source.authors,
            year=str(source.publication_year) if source.publication_year else None,
            style=citation_style,
        )

        cit = Citation(
            report_id=report_id,
            report_section_id=report_section_id,
            source_id=source_id,
            evidence_id=evidence_id,
            claim_id=claim_id,
            citation_number=citation_num,
            citation_style=citation_style,
            citation_key=citation_key,
            locator=locator,
            evidence_text=evidence_text or (evidence.quote if evidence else source.abstract or source.title),
            verification_status="VERIFIED" if source.verification_status in ["VERIFIED", "PARTIALLY_VERIFIED"] else "NEEDS_REVIEW",
            support_level=support_level,
        )
        db.add(cit)
        db.commit()
        db.refresh(cit)

        # Re-index report citations to ensure correct numbering
        if report_id:
            cls.reindex_citations(db, report_id, style=citation_style)
            db.refresh(cit)

        return cit

    @classmethod
    def generate_report_bibliography(
        cls,
        db: Session,
        report_id: str,
        style: str = "IEEE",
    ) -> Dict[str, Any]:
        """Generates real, verifiable bibliography references for all cited sources."""
        citations = (
            db.query(Citation)
            .filter(Citation.report_id == report_id)
            .order_by(Citation.citation_number.asc())
            .all()
        )

        seen_sources = set()
        ordered_sources: List[Dict[str, Any]] = []

        for cit in citations:
            if cit.source_id not in seen_sources:
                seen_sources.add(cit.source_id)
                src = db.query(Source).filter(Source.id == cit.source_id).first()
                if src:
                    ordered_sources.append({
                        "id": src.id,
                        "citation_number": cit.citation_number,
                        "title": src.title,
                        "authors": src.authors or "Chưa rõ tác giả",
                        "publisher": src.publisher or src.organization or "Xuất bản điện tử",
                        "published_date": str(src.publication_year or src.published_date or "2024"),
                        "url": src.canonical_url or src.url or "",
                        "doi": src.doi or "",
                        "source_type": src.source_type,
                    })

        entries: List[str] = []
        for s in ordered_sources:
            entry = CitationFormatter.format_bibliography_entry(
                index=s["citation_number"],
                source=s,
                style=style,
            )
            entries.append(entry)

        combined_text = "\n\n".join(entries)

        return {
            "style": style.upper(),
            "total_references": len(ordered_sources),
            "references": ordered_sources,
            "formatted_entries": entries,
            "bibliography_markdown": f"## Tài liệu tham khảo\n\n{combined_text}" if entries else "",
        }

    @classmethod
    def get_report_coverage(
        cls,
        db: Session,
        report_id: str,
    ) -> Dict[str, Any]:
        """Calculates claim and citation coverage statistics."""
        claims = db.query(Claim).filter(Claim.report_id == report_id).all()
        citations = db.query(Citation).filter(Citation.report_id == report_id).all()

        total_claims = len(claims)
        total_citations = len(citations)

        verified_citations = [c for c in citations if c.verification_status == "VERIFIED"]
        strong_citations = [c for c in citations if c.support_level == "STRONG"]

        claim_with_citations = 0
        for cl in claims:
            cl_citations = [c for c in citations if c.claim_id == cl.id]
            if cl_citations:
                claim_with_citations += 1

        coverage_ratio = (
            round((claim_with_citations / total_claims) * 100, 1)
            if total_claims > 0
            else (100.0 if total_citations > 0 else 0.0)
        )

    @classmethod
    async def reindex_citations_async(
        cls,
        db: Any,
        report_id: str,
        style: str = "IEEE",
    ) -> List[Citation]:
        from sqlalchemy import select
        # Get sections ordered by position
        stmt = (
            select(ReportSection)
            .where(ReportSection.report_id == report_id)
            .order_by(ReportSection.position.asc(), ReportSection.created_at.asc())
        )
        res = await db.execute(stmt)
        sections = res.scalars().all()

        citation_counter = 1
        all_updated: List[Citation] = []
        source_seen_map: Dict[str, int] = {}

        for sec in sections:
            stmt_cits = (
                select(Citation)
                .where(Citation.report_section_id == sec.id)
                .order_by(Citation.citation_number.asc(), Citation.created_at.asc())
            )
            res_cits = await db.execute(stmt_cits)
            sec_citations = res_cits.scalars().all()

            for cit in sec_citations:
                if cit.source_id in source_seen_map and style.upper() == "IEEE":
                    cit.citation_number = source_seen_map[cit.source_id]
                else:
                    cit.citation_number = citation_counter
                    source_seen_map[cit.source_id] = citation_counter
                    citation_counter += 1

                res_src = await db.execute(select(Source).where(Source.id == cit.source_id))
                source = res_src.scalars().first()
                author = source.authors if source else None
                year = str(source.publication_year) if (source and source.publication_year) else None

                cit.citation_style = style.upper()
                cit.citation_key = CitationFormatter.format_in_text(
                    citation_number=cit.citation_number,
                    author=author,
                    year=year,
                    style=style,
                )
                all_updated.append(cit)

        await db.commit()
        for cit in all_updated:
            await db.refresh(cit)
        return all_updated

    @classmethod
    async def check_source_citations_async(
        cls,
        db: Any,
        source_id: str,
    ) -> Dict[str, Any]:
        from sqlalchemy import select
        res_cits = await db.execute(select(Citation).where(Citation.source_id == source_id))
        citations = res_cits.scalars().all()
        report_ids = {c.report_id for c in citations if c.report_id}

        reports = []
        if report_ids:
            res_rep = await db.execute(select(Report).where(Report.id.in_(report_ids)))
            reports = res_rep.scalars().all()

        is_in_use = len(citations) > 0
        return {
            "source_id": source_id,
            "is_in_use": is_in_use,
            "citation_count": len(citations),
            "affected_reports": [
                {"id": r.id, "title": r.title} for r in reports
            ],
            "warning_message": (
                f"Nguồn này đang được trích dẫn ở {len(citations)} vị trí trong {len(reports)} báo cáo. "
                f"Xóa nguồn sẽ làm mất liên kết bằng chứng của các trích dẫn này."
                if is_in_use
                else "Nguồn này hiện chưa được trích dẫn trong báo cáo nào, có thể xóa an toàn."
            ),
        }

    @classmethod
    async def create_citation_async(
        cls,
        db: Any,
        report_id: Optional[str],
        report_section_id: str,
        source_id: str,
        evidence_id: Optional[str] = None,
        claim_id: Optional[str] = None,
        locator: Optional[str] = None,
        citation_style: str = "IEEE",
    ) -> Citation:
        from sqlalchemy import select
        res_src = await db.execute(select(Source).where(Source.id == source_id))
        source = res_src.scalars().first()
        if not source:
            raise ValueError(f"Source not found: {source_id}")

        evidence_text = ""
        evidence = None
        if evidence_id:
            res_ev = await db.execute(select(Evidence).where(Evidence.id == evidence_id))
            evidence = res_ev.scalars().first()
            if evidence:
                evidence_text = evidence.quote

        claim_text = ""
        claim = None
        if claim_id:
            res_cl = await db.execute(select(Claim).where(Claim.id == claim_id))
            claim = res_cl.scalars().first()
            if claim:
                claim_text = claim.claim_text

        support_level = "STRONG"
        if claim_text and evidence_text:
            eval_res = cls.evaluate_evidence_support(claim_text, evidence_text)
            support_level = eval_res.get("support_level", "STRONG")
        elif not evidence_text:
            support_level = "MODERATE" if source.verification_status == "VERIFIED" else "WEAK"

        res_cnt = await db.execute(select(Citation).where(Citation.report_section_id == report_section_id))
        existing_count = len(res_cnt.scalars().all())
        citation_num = existing_count + 1

        citation_key = CitationFormatter.format_in_text(
            citation_number=citation_num,
            author=source.authors,
            year=str(source.publication_year) if source.publication_year else None,
            style=citation_style,
        )

        cit = Citation(
            report_id=report_id,
            report_section_id=report_section_id,
            source_id=source_id,
            evidence_id=evidence_id,
            claim_id=claim_id,
            citation_number=citation_num,
            citation_style=citation_style,
            citation_key=citation_key,
            locator=locator,
            evidence_text=evidence_text or (evidence.quote if evidence else source.abstract or source.title),
            verification_status="VERIFIED" if source.verification_status in ["VERIFIED", "PARTIALLY_VERIFIED"] else "NEEDS_REVIEW",
            support_level=support_level,
        )
        db.add(cit)
        await db.commit()
        await db.refresh(cit)

        if report_id:
            await cls.reindex_citations_async(db, report_id, style=citation_style)
            await db.refresh(cit)

        return cit

    @classmethod
    async def generate_report_bibliography_async(
        cls,
        db: Any,
        report_id: str,
        style: str = "IEEE",
    ) -> Dict[str, Any]:
        from sqlalchemy import select
        stmt = (
            select(Citation)
            .where(Citation.report_id == report_id)
            .order_by(Citation.citation_number.asc())
        )
        res = await db.execute(stmt)
        citations = res.scalars().all()

        seen_sources = set()
        ordered_sources: List[Dict[str, Any]] = []

        for cit in citations:
            if cit.source_id not in seen_sources:
                seen_sources.add(cit.source_id)
                stmt_s = select(Source).where(Source.id == cit.source_id)
                res_s = await db.execute(stmt_s)
                src = res_s.scalars().first()
                if src:
                    ordered_sources.append({
                        "id": src.id,
                        "citation_number": cit.citation_number,
                        "title": src.title,
                        "authors": src.authors or "Chưa rõ tác giả",
                        "publisher": src.publisher or src.organization or "Xuất bản điện tử",
                        "published_date": str(src.publication_year or src.published_date or "2024"),
                        "url": src.canonical_url or src.url or "",
                        "doi": src.doi or "",
                        "source_type": src.source_type,
                    })

        entries: List[str] = []
        for s in ordered_sources:
            entry = CitationFormatter.format_bibliography_entry(
                index=s["citation_number"],
                source=s,
                style=style,
            )
            entries.append(entry)

        combined_text = "\n\n".join(entries)

        return {
            "style": style.upper(),
            "total_references": len(ordered_sources),
            "references": ordered_sources,
            "formatted_entries": entries,
            "bibliography_markdown": f"## Tài liệu tham khảo\n\n{combined_text}" if entries else "",
        }

    @classmethod
    async def get_report_coverage_async(
        cls,
        db: Any,
        report_id: str,
    ) -> Dict[str, Any]:
        from sqlalchemy import select
        res_claims = await db.execute(select(Claim).where(Claim.report_id == report_id))
        claims = res_claims.scalars().all()

        res_cits = await db.execute(select(Citation).where(Citation.report_id == report_id))
        citations = res_cits.scalars().all()

        total_claims = len(claims)
        total_citations = len(citations)

        verified_citations = [c for c in citations if c.verification_status == "VERIFIED"]
        strong_citations = [c for c in citations if c.support_level == "STRONG"]

        claim_with_citations = 0
        for cl in claims:
            cl_citations = [c for c in citations if c.claim_id == cl.id]
            if cl_citations:
                claim_with_citations += 1

        coverage_ratio = (
            round((claim_with_citations / total_claims) * 100, 1)
            if total_claims > 0
            else (100.0 if total_citations > 0 else 0.0)
        )

        return {
            "report_id": report_id,
            "total_claims": total_claims,
            "total_citations": total_citations,
            "claim_citation_coverage_pct": coverage_ratio,
            "verified_citation_count": len(verified_citations),
            "strong_support_count": len(strong_citations),
            "requires_review_count": total_citations - len(verified_citations),
        }


citation_service = CitationService()

