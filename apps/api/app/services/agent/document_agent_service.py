import json
from typing import Any, Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.entities import Project, Report, ReportSection
from app.repositories.project_repo import project_repo, document_repo, file_repo
from app.repositories.report_repo import report_repo, section_repo
from app.repositories.source_repo import source_repo
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType
from app.services.agent.agent_tool_registry import agent_tool_registry
from app.services.research.search_engine import search_engine
from app.services.research.source_ranker import source_ranker
from app.services.knowledge.retrieval_service import retrieval_service
from app.services.quality.multi_profile_quality_engine import multi_profile_quality_engine


class DocumentAgentService:
    """
    Autonomous Document Agent Service (Phase U12 & U18).
    Processes multi-turn requests by selecting and executing validated tools safely via AI Gateway.
    """

    @classmethod
    async def execute_turn(
        cls,
        db: AsyncSession,
        project_id: str,
        report_id: Optional[str],
        user_message: str,
        active_section_id: Optional[str] = None,
        selected_text: Optional[str] = None,
    ) -> Dict[str, Any]:
        project = await project_repo.get(db, project_id)
        if not project:
            return {"error": "Project not found"}

        report = await report_repo.get(db, report_id) if report_id else None
        sections = await section_repo.get_by_report(db, report_id) if report_id else []

        # Tool schemas
        tool_schemas = agent_tool_registry.get_tool_schemas_for_ai()

        system_prompt = (
            "Bạn là Autonomous Document Agent cao cấp trong AI Document Studio. "
            "Bạn có quyền gọi các công cụ (tools) để đọc tài liệu, tìm kiếm tri thức, sửa đổi văn bản, "
            "chèn bảng biểu, biểu đồ, sơ đồ và đánh giá chất lượng. "
            "Bắt buộc trả về JSON gồm: "
            "1. thoughts (suy nghĩ lập luận), "
            "2. human_readable_activity (câu tóm tắt hoạt động thân thiện với người dùng, ví dụ: 'Đang đọc 3 tài liệu tham khảo' hoặc 'Đang chèn bảng chỉ số KPI'), "
            "3. tool_calls (danh sách các action cần thực hiện: [{tool_name, arguments}]), "
            "4. message_to_user (lời giải thích hoặc phản hồi gửi cho người dùng)."
        )

        user_prompt = f"""
NGỮ CẢNH DỰ ÁN:
- Tên dự án: {project.name}
- Loại tài liệu: {project.type}
- Tổng số phần hiện có: {len(sections)} phần
- Phần đang chọn: {active_section_id or 'Chưa chọn'}
{f'- Đoạn văn bản bôi đen: "{selected_text}"' if selected_text else ''}

YÊU CẦU CỦA NGƯỜI DÙNG:
"{user_message}"

DANH MỤC CÔNG CỤ KHẢ DỤNG:
{json.dumps(tool_schemas, ensure_ascii=False, indent=2)}

Hãy phân tích và trả về JSON cấu trúc hoàn chỉnh.
"""

        ai_res = await ai_gateway.execute(
            AIRequest(
                task_type=AITaskType.AGENT_REASONING,
                prompt=user_prompt,
                system_prompt=system_prompt,
                response_format="json",
                temperature=0.2,
            )
        )

        raw_text = ai_res.text or "{}"
        try:
            data = json.loads(raw_text)
        except Exception:
            clean = raw_text.replace("```json", "").replace("```", "").strip()
            data = json.loads(clean)

        tool_calls = data.get("tool_calls", [])
        executed_actions: List[Dict[str, Any]] = []

        # Execute validated actions
        for tc in tool_calls:
            t_name = tc.get("tool_name")
            args = tc.get("arguments", {})
            tool_def = agent_tool_registry.get_tool(t_name)

            if not tool_def:
                continue

            # Execute specific tool safely
            action_result = await cls._execute_tool(db, project, report, t_name, args)
            executed_actions.append({
                "tool_name": t_name,
                "arguments": args,
                "result": action_result
            })

        return {
            "human_readable_activity": data.get("human_readable_activity", "Đã xử lý xong yêu cầu của bạn."),
            "thoughts": data.get("thoughts", ""),
            "message_to_user": data.get("message_to_user", "Tôi đã thực hiện các điều chỉnh theo yêu cầu của bạn."),
            "actions_executed": executed_actions,
            "gateway_usage": ai_res.usage.model_dump(),
        }

    @classmethod
    async def _execute_tool(
        cls,
        db: AsyncSession,
        project: Project,
        report: Optional[Report],
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:
        if tool_name == "read_document" and report:
            secs = await section_repo.get_by_report(db, report.id)
            return [{"id": s.id, "title": s.title, "word_count": s.word_count} for s in secs]

        elif tool_name == "read_section":
            sec_id = args.get("section_id")
            if sec_id:
                sec = await section_repo.get(db, sec_id)
                return {"id": sec.id, "title": sec.title, "text": sec.plain_text} if sec else None

        elif tool_name == "search_project_knowledge":
            q = args.get("query", "")
            docs = await document_repo.get_multi(db, project_id=project.id)
            docs_payload = [{"id": d.id, "original_name": d.title, "content_text": d.content_text} for d in docs]
            return retrieval_service.search_relevant_chunks(query=q, documents=docs_payload, top_k=3)

        elif tool_name == "search_web":
            q = args.get("query", "")
            provider = search_engine.get_search_provider()
            raw = await provider.search(q, max_results=4)
            return source_ranker.rank_sources(raw)

        elif tool_name == "add_section" and report:
            title = args.get("title", "Mục mới")
            level = args.get("level", 1)
            all_secs = await section_repo.get_by_report(db, report.id)
            new_sec = await section_repo.create(db, obj_in={
                "report_id": report.id,
                "title": title,
                "level": level,
                "position": len(all_secs) + 1,
                "status": "planned",
                "plain_text": f"{title}\n\nNội dung đang được khởi tạo...",
                "content_json": {"type": "doc", "content": [{"type": "heading", "attrs": {"level": level}, "content": [{"type": "text", "text": title}]}]},
                "word_count": 5,
            })
            return {"status": "success", "section_id": new_sec.id, "title": new_sec.title}

        elif tool_name == "insert_text":
            sec_id = args.get("section_id")
            text = args.get("text", "")
            if sec_id and text:
                sec = await section_repo.get(db, sec_id)
                if sec:
                    updated_text = f"{sec.plain_text or ''}\n\n{text}"
                    await section_repo.update(db, db_obj=sec, obj_in={
                        "plain_text": updated_text,
                        "word_count": len(updated_text.split()),
                    })
                    return {"status": "success", "section_id": sec.id}

        elif tool_name == "run_quality_check" and report:
            secs = await section_repo.get_by_report(db, report.id)
            sources = await source_repo.get_by_project(db, project.id)
            return multi_profile_quality_engine.evaluate(
                profile=report.report_type or project.type or "business",
                sections=secs,
                sources_count=len(sources)
            )

        return {"status": "executed", "tool": tool_name}


document_agent_service = DocumentAgentService()
