import json
import re
from typing import Any, Dict, List, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.entities import Project, Report, ReportSection
from app.repositories.report_repo import section_repo
from app.services.agent.agentic_report_orchestrator import AgenticReportOrchestrator
from app.services.editor.writing_engine import writing_engine


class ReportQualityRepairService:
    """Audits and repairs generated reports before users export or present them."""

    GENERIC_MARKERS = [
        'Mục "',
        "làm rõ một nội dung cụ thể",
        "Nội dung nên đi từ khái niệm",
        "Phần này trình bày chi tiết nội dung",
    ]

    @classmethod
    def audit(cls, report: Report, project: Project, sections: List[ReportSection]) -> Dict[str, Any]:
        total_words = sum(int(getattr(sec, "word_count", 0) or 0) for sec in sections)
        issues: List[Dict[str, Any]] = []
        repeated_visuals = cls._repeated_visual_markers(sections)
        repeated_openings = cls._repeated_openings(sections)

        for sec in sections:
            title = getattr(sec, "title", "") or ""
            text = getattr(sec, "plain_text", "") or ""
            word_count = len(text.split())
            level = int(getattr(sec, "level", 1) or 1)
            expected = cls._expected_words(title, level)
            section_issues: List[str] = []

            if word_count < expected:
                section_issues.append(f"Mục còn ngắn ({word_count}/{expected} từ).")
            if cls._looks_generic(text):
                section_issues.append("Nội dung còn chung chung hoặc có câu fallback.")
            if cls._has_internal_repetition(text):
                section_issues.append("Có đoạn bị lặp trong cùng một mục.")
            if title in repeated_openings:
                section_issues.append("Cách mở đầu giống mục khác.")

            if section_issues:
                severity = "high" if cls._looks_generic(text) or word_count < expected * 0.55 else "medium"
                if section_issues == ["Cách mở đầu giống mục khác."]:
                    severity = "low"
                issues.append({
                    "section_id": sec.id,
                    "title": title,
                    "word_count": word_count,
                    "expected_words": expected,
                    "issues": section_issues,
                    "severity": severity,
                })

        for marker, titles in repeated_visuals:
            issues.append({
                "section_id": None,
                "title": "Ảnh/biểu đồ trùng",
                "word_count": 0,
                "expected_words": 0,
                "issues": [f"Marker bị lặp ở {len(titles)} mục: {', '.join(titles[:4])}"],
                "severity": "medium",
            })

        score = cls._score(total_words, len(sections), issues)
        return {
            "report_id": report.id,
            "title": report.title,
            "score": score,
            "status": "ready" if score >= 82 and not any(i["severity"] == "high" for i in issues) else "needs_repair",
            "summary": cls._summary(score, issues),
            "total_sections": len(sections),
            "total_words": total_words,
            "issues_count": len(issues),
            "high_issues_count": sum(1 for issue in issues if issue["severity"] == "high"),
            "issues": issues[:50],
            "recommendations": cls._recommendations(issues),
        }

    @classmethod
    async def repair(cls, db: AsyncSession, report: Report, project: Project, sections: List[ReportSection]) -> Dict[str, Any]:
        audit_before = cls.audit(report, project, sections)
        issue_ids = {
            issue["section_id"]
            for issue in audit_before["issues"]
            if issue.get("section_id")
        }

        repaired_sections = []
        seen_visuals: set[str] = set()
        topic = cls._topic(report, project)

        for sec in sections:
            should_repair = sec.id in issue_ids
            text = sec.plain_text or ""

            if should_repair:
                target_words = cls._repair_target_words(sec.title, int(sec.level or 1))
                text = writing_engine._build_fallback_draft(
                    section_title=sec.title,
                    topic_name=topic,
                    instruction=(
                        "Viết lại chuyên sâu, đúng đề tài, tránh câu chung chung, tránh lặp nội dung, "
                        "ưu tiên bảng so sánh khi phù hợp và không tự tạo bìa/mục lục."
                    ),
                    tone="academic",
                    sources=[],
                    target_words=target_words,
                )

            text = AgenticReportOrchestrator._deduplicate_paragraphs(text)
            text = AgenticReportOrchestrator._deduplicate_visual_markers(text, seen_visuals)
            content_json = writing_engine._text_to_tiptap_json(text, int(sec.level or 1))
            updated = await section_repo.update(db, db_obj=sec, obj_in={
                "plain_text": text,
                "content_json": content_json,
                "word_count": len(text.split()),
                "status": "draft",
            })
            repaired_sections.append(updated)

        audit_after = cls.audit(report, project, repaired_sections)
        return {
            "repaired_count": len(issue_ids),
            "before": audit_before,
            "after": audit_after,
            "message": f"Đã kiểm tra và sửa {len(issue_ids)} mục cần cải thiện.",
        }

    @classmethod
    async def repair_section(
        cls,
        db: AsyncSession,
        report: Report,
        project: Project,
        sections: List[ReportSection],
        section_id: str,
    ) -> Dict[str, Any]:
        target = next((sec for sec in sections if sec.id == section_id), None)
        if not target:
            raise ValueError("Section not found")

        topic = cls._topic(report, project)
        target_words = cls._repair_target_words(target.title, int(target.level or 1))
        text = writing_engine._build_fallback_draft(
            section_title=target.title,
            topic_name=topic,
            instruction=(
                "Viết lại riêng mục này thật chi tiết, đúng trọng tâm, không lặp câu mở đầu của mục khác, "
                "không dùng câu mô tả chung chung và giữ văn phong báo cáo học thuật."
            ),
            tone="academic",
            sources=[],
            target_words=target_words,
        )

        seen_visuals: set[str] = set()
        for sec in sections:
            if sec.id == section_id:
                continue
            cls._collect_visual_keys(sec.plain_text or "", seen_visuals)

        text = AgenticReportOrchestrator._deduplicate_paragraphs(text)
        text = AgenticReportOrchestrator._deduplicate_visual_markers(text, seen_visuals)
        updated = await section_repo.update(db, db_obj=target, obj_in={
            "plain_text": text,
            "content_json": writing_engine._text_to_tiptap_json(text, int(target.level or 1)),
            "word_count": len(text.split()),
            "status": "draft",
        })

        updated_sections = [updated if sec.id == section_id else sec for sec in sections]
        return {
            "section_id": updated.id,
            "title": updated.title,
            "word_count": updated.word_count,
            "audit": cls.audit(report, project, updated_sections),
            "message": f"Đã sửa mục “{updated.title}”.",
        }

    @classmethod
    def _topic(cls, report: Report, project: Project) -> str:
        return (report.title or project.name or "Báo cáo").strip()

    @classmethod
    def _expected_words(cls, title: str, level: int) -> int:
        upper = (title or "").upper()
        if "TÀI LIỆU THAM KHẢO" in upper:
            return 80
        if upper.startswith(("MỤC LỤC", "DANH MỤC")):
            return 20
        if upper.startswith("LỜI") or "KẾT LUẬN" in upper:
            return 420
        if upper.startswith("CHƯƠNG"):
            return 380
        if level >= 2 or re.match(r"^\d+\.\d+", title or ""):
            return 520
        return 420

    @classmethod
    def _repair_target_words(cls, title: str, level: int) -> int:
        expected = cls._expected_words(title, level)
        if re.match(r"^\d+\.\d+", title or ""):
            return max(720, expected + 180)
        return max(560, expected + 160)

    @classmethod
    def _looks_generic(cls, text: str) -> bool:
        lowered = (text or "").lower()
        return any(marker.lower() in lowered for marker in cls.GENERIC_MARKERS)

    @classmethod
    def _has_internal_repetition(cls, text: str) -> bool:
        seen: set[str] = set()
        for paragraph in re.split(r"\n{2,}", text or ""):
            key = re.sub(r"\W+", " ", paragraph.lower()).strip()[:180]
            if len(key) < 80:
                continue
            if key in seen:
                return True
            seen.add(key)
        return False

    @classmethod
    def _repeated_visual_markers(cls, sections: List[ReportSection]) -> List[Tuple[str, List[str]]]:
        marker_map: Dict[str, List[str]] = {}
        pattern = re.compile(r"\[\[(IMAGE|CHART)\s*:(.*?)\]\]", flags=re.IGNORECASE | re.DOTALL)
        for sec in sections:
            for match in pattern.finditer(sec.plain_text or ""):
                payload = re.sub(r"\s+", " ", match.group(2).lower()).strip()
                title_match = re.search(r"title\s*=\s*([^;]+)", payload)
                key = f"{match.group(1).lower()}:{title_match.group(1).strip() if title_match else payload[:100]}"
                marker_map.setdefault(key, []).append(sec.title)
        return [(key, titles) for key, titles in marker_map.items() if len(titles) > 1]

    @staticmethod
    def _collect_visual_keys(text: str, seen_visuals: set[str]) -> None:
        pattern = re.compile(r"\[\[(IMAGE|CHART)\s*:(.*?)\]\]", flags=re.IGNORECASE | re.DOTALL)
        for match in pattern.finditer(text or ""):
            payload = re.sub(r"\s+", " ", match.group(2).lower()).strip()
            title_match = re.search(r"title\s*=\s*([^;]+)", payload)
            key = f"{match.group(1).lower()}:{title_match.group(1).strip() if title_match else payload[:100]}"
            seen_visuals.add(key)

    @classmethod
    def _repeated_openings(cls, sections: List[ReportSection]) -> set[str]:
        openings: Dict[str, List[str]] = {}
        for sec in sections:
            paragraphs = [p.strip() for p in re.split(r"\n{2,}", sec.plain_text or "") if p.strip()]
            if len(paragraphs) < 2:
                continue
            first_body = paragraphs[1] if paragraphs[0].strip() == (sec.title or "").strip() else paragraphs[0]
            key = re.sub(r"\W+", " ", first_body.lower()).strip()[:150]
            if len(key) >= 80:
                openings.setdefault(key, []).append(sec.title)
        repeated_titles: set[str] = set()
        for titles in openings.values():
            if len(titles) > 1:
                repeated_titles.update(titles)
        return repeated_titles

    @staticmethod
    def _score(total_words: int, section_count: int, issues: List[Dict[str, Any]]) -> int:
        base = 92
        if total_words < max(2500, section_count * 320):
            base -= 12
        base -= sum(10 if issue["severity"] == "high" else 3 if issue["severity"] == "medium" else 1 for issue in issues)
        return max(35, min(100, base))

    @staticmethod
    def _summary(score: int, issues: List[Dict[str, Any]]) -> str:
        if not issues:
            return f"Báo cáo đạt {score}/100, có thể xem theo mẫu và xuất DOCX."
        if not any(issue["severity"] in {"high", "medium"} for issue in issues):
            return f"Báo cáo đạt {score}/100, chỉ còn vài điểm nhẹ về cách diễn đạt; có thể xem theo mẫu và xuất DOCX."
        return f"Báo cáo đạt {score}/100, còn {len(issues)} điểm cần cải thiện trước khi nộp/xuất file."

    @staticmethod
    def _recommendations(issues: List[Dict[str, Any]]) -> List[str]:
        if not issues:
            return ["Có thể xuất DOCX hoặc tiếp tục chỉnh sửa trong Studio."]
        recs = ["Bấm “Tự sửa báo cáo” để viết lại các mục ngắn hoặc chung chung."]
        if any(issue["title"] == "Ảnh/biểu đồ trùng" for issue in issues):
            recs.append("Loại bỏ ảnh/biểu đồ trùng để bản xem theo mẫu gọn hơn.")
        if any("ngắn" in " ".join(issue["issues"]).lower() for issue in issues):
            recs.append("Tăng độ dài các mục con quan trọng lên khoảng 600-800 từ.")
        return recs


report_quality_repair_service = ReportQualityRepairService()
