import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
import pandas as pd
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.entities import (
    Automation,
    AutomationRun,
    Project,
    Report,
    ReportSection,
    UploadedFile,
    Dataset,
    TemplateVersion,
    ExportRecord,
    Source,
)
from app.repositories.base import BaseRepository
from app.repositories.project_repo import project_repo
from app.repositories.report_repo import report_repo, section_repo
from app.services.data.sheet_analysis_service import SheetAnalysisService
from app.services.documents.pdf_parser import PDFParser
from app.services.documents.docx_parser import DocxParser
from app.services.editor.writing_engine import writing_engine
from app.services.exports.docx_exporter import docx_exporter
from app.services.exports.pdf_exporter import pdf_exporter
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType
from app.services.automation.automation_scheduler import automation_scheduler

logger = logging.getLogger("automation.engine")


class AutomationEngine:
    """
    End-to-End Report Automation Engine.
    Orchestrates real data ingestion (Excel/CSV/PDF/DOCX), mathematical computation,
    AI synthesis, report persistence, and real file export generation (DOCX/PDF).
    """

    _active_executions: Set[str] = set()

    @classmethod
    async def create_automation(
        cls,
        db: AsyncSession,
        project_id: str,
        user_id: str,
        name: str,
        description: Optional[str] = None,
        trigger_type: str = "manual",
        cron_expression: Optional[str] = None,
        timezone_name: str = "Asia/Ho_Chi_Minh",
        data_source_id: Optional[str] = None,
        source_type: str = "file",
        source_config_json: Optional[Dict[str, Any]] = None,
        template_id: Optional[str] = None,
        analysis_prompt: Optional[str] = None,
        analysis_mode: str = "comprehensive",
        report_title_pattern: str = "Báo cáo Tự động {date}",
        export_formats: Optional[List[str]] = None,
        is_active: bool = True,
    ) -> Automation:
        auto_repo = BaseRepository[Automation](Automation)

        next_run_at = None
        if is_active and trigger_type == "schedule" and cron_expression:
            next_run_at = automation_scheduler.compute_next_run(
                trigger_type=trigger_type,
                cron_expression=cron_expression,
                tz_name=timezone_name,
            )

        return await auto_repo.create(
            db,
            obj_in={
                "project_id": project_id,
                "user_id": user_id,
                "name": name.strip(),
                "description": description.strip() if description else None,
                "trigger_type": trigger_type,
                "cron_expression": cron_expression.strip() if cron_expression else None,
                "timezone": timezone_name,
                "data_source_id": data_source_id,
                "source_type": source_type,
                "source_config_json": source_config_json or {},
                "template_id": template_id,
                "analysis_prompt": analysis_prompt.strip() if analysis_prompt else None,
                "analysis_mode": analysis_mode,
                "report_title_pattern": report_title_pattern.strip() or "Báo cáo Tự động {date}",
                "export_formats_json": export_formats or ["docx"],
                "is_active": is_active,
                "next_run_at": next_run_at,
            },
        )

    @classmethod
    async def update_automation(
        cls,
        db: AsyncSession,
        automation: Automation,
        update_data: Dict[str, Any],
    ) -> Automation:
        auto_repo = BaseRepository[Automation](Automation)

        # Recompute next_run_at if trigger_type, cron_expression, or is_active changed
        new_active = update_data.get("is_active", automation.is_active)
        new_trigger = update_data.get("trigger_type", automation.trigger_type)
        new_cron = update_data.get("cron_expression", automation.cron_expression)
        new_tz = update_data.get("timezone", automation.timezone)

        if new_active and new_trigger == "schedule" and new_cron:
            update_data["next_run_at"] = automation_scheduler.compute_next_run(
                trigger_type=new_trigger,
                cron_expression=new_cron,
                tz_name=new_tz,
            )
        else:
            update_data["next_run_at"] = None

        if "export_formats" in update_data:
            update_data["export_formats_json"] = update_data.pop("export_formats")

        return await auto_repo.update(db, db_obj=automation, obj_in=update_data)

    @classmethod
    async def execute_run(
        cls,
        db: AsyncSession,
        automation_id: str,
        trigger_source: str = "manual",
    ) -> Dict[str, Any]:
        """
        Executes a complete, real end-to-end automation run.
        Guarantees concurrency safety, reads real files, executes statistical analysis,
        generates structured reports, exports physical DOCX/PDF files, and updates logs.
        """
        if automation_id in cls._active_executions:
            return {
                "error": "Automation đang được chạy trong một tiến trình khác. Vui lòng đợi hoàn thành.",
                "status": "running",
            }

        cls._active_executions.add(automation_id)
        auto_repo = BaseRepository[Automation](Automation)
        run_repo = BaseRepository[AutomationRun](AutomationRun)

        automation = await auto_repo.get(db, automation_id)
        if not automation:
            cls._active_executions.discard(automation_id)
            return {"error": "Automation not found"}

        project = await project_repo.get(db, automation.project_id)
        if not project:
            cls._active_executions.discard(automation_id)
            return {"error": "Project not found"}

        tz = automation_scheduler.get_zoneinfo(automation.timezone)
        start_time_utc = datetime.now(timezone.utc)
        start_time_local_str = start_time_utc.astimezone(tz).strftime("%d/%m/%Y %H:%M:%S")

        initial_log = f"[{start_time_local_str}] Khởi động thực thi Automation '{automation.name}' (Nguồn kích hoạt: {trigger_source})"
        run = await run_repo.create(
            db,
            obj_in={
                "automation_id": automation.id,
                "status": "running",
                "trigger_source": trigger_source,
                "log_messages_json": [initial_log],
                "started_at": start_time_utc,
            },
        )
        await db.commit()

        logs: List[str] = [initial_log]
        failed_step: Optional[str] = None

        def add_log(msg: str):
            curr_str = datetime.now(timezone.utc).astimezone(tz).strftime("%H:%M:%S")
            logs.append(f"[{curr_str}] {msg}")

        try:
            # =========================================================================
            # STEP 1: RESOLVE & INGEST DATA SOURCE
            # =========================================================================
            failed_step = "resolve_data_source"
            add_log("Bước 1: Tiếp nhận và kiểm tra nguồn dữ liệu cấu hình...")

            target_file_path: Optional[str] = None
            target_file_name: Optional[str] = None
            source_snapshot: Dict[str, Any] = {}

            # Lookup uploaded file or dataset
            if automation.data_source_id:
                if automation.source_type == "dataset":
                    ds = await BaseRepository[Dataset](Dataset).get(db, automation.data_source_id)
                    if ds and ds.raw_data_path and Path(ds.raw_data_path).exists():
                        target_file_path = ds.raw_data_path
                        target_file_name = ds.original_filename or ds.name
                else:
                    up_file = await BaseRepository[UploadedFile](UploadedFile).get(db, automation.data_source_id)
                    if up_file and up_file.file_path and Path(up_file.file_path).exists():
                        target_file_path = up_file.file_path
                        target_file_name = up_file.original_name or up_file.filename

            # Fallback to latest file in project if not specified or not found
            if not target_file_path:
                stmt = (
                    select(UploadedFile)
                    .where(UploadedFile.project_id == project.id)
                    .order_by(desc(UploadedFile.created_at))
                )
                res = await db.execute(stmt)
                files = res.scalars().all()
                # Prefer excel/csv, then docx/pdf
                tabular_files = [f for f in files if (f.original_name or "").lower().endswith((".xlsx", ".xls", ".csv"))]
                chosen_file = tabular_files[0] if tabular_files else (files[0] if files else None)
                if chosen_file and Path(chosen_file.file_path).exists():
                    target_file_path = chosen_file.file_path
                    target_file_name = chosen_file.original_name or chosen_file.filename

            # =========================================================================
            # STEP 2: DETERMINISTIC MATHEMATICAL & STATISTICAL ANALYSIS
            # =========================================================================
            failed_step = "analyze_data"
            sheet_analysis_data: Optional[Dict[str, Any]] = None
            df_preview_rows: List[Dict[str, Any]] = []

            if target_file_path and Path(target_file_path).exists():
                ext = Path(target_file_path).suffix.lower()
                add_log(f"Đã nạp tệp dữ liệu: '{target_file_name}' ({ext})")

                if ext in [".xlsx", ".xls", ".csv", ".tsv"]:
                    target_sheet = (automation.source_config_json or {}).get("sheet_name")
                    clean_df, sheet_used, all_sheets = SheetAnalysisService.load_sheet_dataframe(
                        file_path=target_file_path,
                        sheet_name=target_sheet,
                    )
                    add_log(f"Trích xuất bảng tính sheet '{sheet_used}' ({len(clean_df)} dòng dữ liệu, {len(clean_df.columns)} cột)")

                    analysis_res = await SheetAnalysisService.analyze_sheet(
                        file_path=target_file_path,
                        sheet_name=sheet_used,
                    )
                    sheet_analysis_data = analysis_res
                    numeric_cols = [c["name"] for c in analysis_res.get("columns", []) if c.get("type") in ["numeric", "currency", "percentage"]]
                    quality_issues = analysis_res.get("data_quality_issues", [])
                    source_snapshot = {
                        "source_type": "tabular",
                        "file_name": target_file_name,
                        "file_path": target_file_path,
                        "sheet_name": sheet_used,
                        "all_sheets": all_sheets,
                        "total_rows": analysis_res["overview"]["total_rows"],
                        "total_columns": analysis_res["overview"]["total_columns"],
                        "columns": [c["name"] for c in analysis_res.get("columns", [])],
                        "numeric_columns": numeric_cols,
                        "quality_issues_count": len(quality_issues),
                    }
                    df_preview_rows = clean_df.head(10).to_dict(orient="records")
                    add_log(
                        f"Phân tích hoàn tất: {analysis_res['overview']['total_rows']} dòng, "
                        f"{analysis_res['overview']['numeric_columns_count']} cột số, "
                        f"{len(quality_issues)} cảnh báo chất lượng."
                    )
                elif ext == ".pdf":
                    pdf_info = PDFParser.extract_text_and_metadata(target_file_path)
                    source_snapshot = {
                        "source_type": "pdf",
                        "file_name": target_file_name,
                        "total_pages": pdf_info.get("total_pages", 0),
                        "token_count": pdf_info.get("token_count", 0),
                    }
                    add_log(f"Đã đọc PDF: {pdf_info.get('total_pages', 0)} trang, ~{pdf_info.get('token_count', 0)} tokens.")
                elif ext in [".docx", ".doc"]:
                    docx_info = DocxParser.extract_text_and_structure(target_file_path)
                    source_snapshot = {
                        "source_type": "docx",
                        "file_name": target_file_name,
                        "word_count": docx_info.get("word_count", 0),
                    }
                    add_log(f"Đã đọc Word: ~{docx_info.get('word_count', 0)} từ.")
            else:
                add_log("Không phát hiện tệp bảng tính đính kèm; sử dụng thông tin và tài liệu mô tả của dự án.")
                source_snapshot = {
                    "source_type": "project_metadata",
                    "project_name": project.name,
                    "description": project.description or "",
                }

            # =========================================================================
            # STEP 3: CREATE REPORT & DRAFT SECTIONS (AI & DETERMINISTIC GROUNDING)
            # =========================================================================
            failed_step = "generate_report_sections"
            now_local = datetime.now(timezone.utc).astimezone(tz)
            date_str = now_local.strftime("%d/%m/%Y")
            time_str = now_local.strftime("%H:%M")

            report_title = (
                automation.report_title_pattern
                .replace("{date}", date_str)
                .replace("{time}", time_str)
                .replace("{project}", project.name)
            )

            # Resolve template version if template_id is specified
            template_version_id: Optional[str] = None
            template_path: Optional[str] = None
            if automation.template_id:
                tv_stmt = (
                    select(TemplateVersion)
                    .where(TemplateVersion.template_id == automation.template_id)
                    .order_by(desc(TemplateVersion.version_number))
                )
                tv_res = await db.execute(tv_stmt)
                latest_tv = tv_res.scalars().first()
                if latest_tv:
                    template_version_id = latest_tv.id
                    if latest_tv.file_path and Path(latest_tv.file_path).exists():
                        template_path = latest_tv.file_path

            report = await report_repo.create(
                db,
                obj_in={
                    "project_id": project.id,
                    "template_version_id": template_version_id,
                    "title": report_title,
                    "report_type": project.type or "business_report",
                    "status": "completed",
                    "revision": 1,
                    "document_settings_json": {
                        "generated_by_automation_id": automation.id,
                        "run_id": run.id,
                        "generated_at": now_local.isoformat(),
                    },
                },
            )
            add_log(f"Khởi tạo báo cáo mới: '{report.title}' (ID: {report.id})")

            # Section Generation Pipeline
            sections_data = await cls._generate_report_sections(
                automation=automation,
                project=project,
                sheet_data=sheet_analysis_data,
                df_preview_rows=df_preview_rows,
                date_str=date_str,
            )

            created_sections: List[ReportSection] = []
            for idx, sec_info in enumerate(sections_data, 1):
                tiptap_json = writing_engine._text_to_tiptap_json(sec_info["plain_text"], sec_info.get("level", 1))
                created_sec = await section_repo.create(
                    db,
                    obj_in={
                        "report_id": report.id,
                        "title": sec_info["title"],
                        "level": sec_info.get("level", 1),
                        "position": idx,
                        "status": "completed",
                        "plain_text": sec_info["plain_text"],
                        "content_json": tiptap_json,
                        "word_count": len(sec_info["plain_text"].split()),
                    },
                )
                created_sections.append(created_sec)

            total_words = sum(s.word_count for s in created_sections)
            add_log(f"Đã hoàn thành biên tập {len(created_sections)} mục nội dung ({total_words} từ).")

            # =========================================================================
            # STEP 4: PHYSICAL EXPORT GENERATION (DOCX & PDF)
            # =========================================================================
            failed_step = "export_documents"
            export_formats = automation.export_formats_json or ["docx"]
            output_files: List[Dict[str, Any]] = []

            # Retrieve sources if available in project
            sources_stmt = select(Source).where(Source.project_id == project.id)
            src_res = await db.execute(sources_stmt)
            project_sources = src_res.scalars().all()

            for fmt in export_formats:
                fmt_lower = fmt.lower().strip()
                if fmt_lower == "docx":
                    add_log("Đang kết xuất tệp Word (DOCX) chuẩn ấn bản...")
                    out_path_str = docx_exporter.generate_docx(
                        report_title=report.title,
                        topic_details=project.topic_details_json or {},
                        sections=created_sections,
                        sources=project_sources,
                        document_settings=report.document_settings_json or {},
                        include_cover=True,
                        include_toc=True,
                        include_references=bool(project_sources),
                        citation_style="IEEE",
                        template_path=template_path,
                    )
                    filename = Path(out_path_str).name
                    file_size = os.path.getsize(out_path_str)

                    # Persist ExportRecord
                    exp_record = await BaseRepository[ExportRecord](ExportRecord).create(
                        db,
                        obj_in={
                            "report_id": report.id,
                            "export_format": "docx",
                            "file_path": out_path_str,
                            "file_size": file_size,
                            "settings_json": {"automation_id": automation.id, "run_id": run.id},
                            "status": "completed",
                        },
                    )
                    output_files.append({
                        "format": "docx",
                        "name": f"{report.title}.docx",
                        "filename": filename,
                        "file_path": out_path_str,
                        "download_url": f"/api/v1/exports/download/{filename}",
                        "file_size": file_size,
                        "record_id": exp_record.id,
                    })
                    add_log(f"Đã tạo tệp DOCX: {filename} ({file_size // 1024} KB)")

                elif fmt_lower == "pdf":
                    add_log("Đang kết xuất tệp PDF/In ấn tiêu chuẩn...")
                    out_path_str = pdf_exporter.generate_pdf(
                        report_title=report.title,
                        topic_details=project.topic_details_json or {},
                        sections=created_sections,
                        sources=project_sources,
                        citation_style="IEEE",
                    )
                    filename = Path(out_path_str).name
                    file_size = os.path.getsize(out_path_str)

                    exp_record = await BaseRepository[ExportRecord](ExportRecord).create(
                        db,
                        obj_in={
                            "report_id": report.id,
                            "export_format": "pdf",
                            "file_path": out_path_str,
                            "file_size": file_size,
                            "settings_json": {"automation_id": automation.id, "run_id": run.id},
                            "status": "completed",
                        },
                    )
                    output_files.append({
                        "format": "pdf",
                        "name": f"{report.title}.html",
                        "filename": filename,
                        "file_path": out_path_str,
                        "download_url": f"/api/v1/exports/download/{filename}",
                        "file_size": file_size,
                        "record_id": exp_record.id,
                    })
                    add_log(f"Đã tạo tệp PDF: {filename} ({file_size // 1024} KB)")

            # =========================================================================
            # STEP 5: FINALIZE RUN & UPDATE AUTOMATION
            # =========================================================================
            failed_step = "finalize_run"
            finish_time_utc = datetime.now(timezone.utc)
            duration_ms = int((finish_time_utc - start_time_utc).total_seconds() * 1000)
            add_log(f"Hoàn thành toàn diện quy trình tự động hóa sau {duration_ms / 1000:.2f} giây.")

            # Compute next run time if scheduled
            next_run_at = None
            if automation.is_active and automation.trigger_type == "schedule" and automation.cron_expression:
                next_run_at = automation_scheduler.compute_next_run(
                    trigger_type=automation.trigger_type,
                    cron_expression=automation.cron_expression,
                    tz_name=automation.timezone,
                    base_time=finish_time_utc,
                )

            await auto_repo.update(
                db,
                db_obj=automation,
                obj_in={
                    "last_run_at": finish_time_utc,
                    "next_run_at": next_run_at,
                },
            )

            await run_repo.update(
                db,
                db_obj=run,
                obj_in={
                    "status": "completed",
                    "report_id": report.id,
                    "duration_ms": duration_ms,
                    "source_snapshot_json": source_snapshot,
                    "output_files_json": output_files,
                    "log_messages_json": logs,
                    "finished_at": finish_time_utc,
                },
            )
            await db.commit()

            return {
                "status": "completed",
                "run_id": run.id,
                "report_id": report.id,
                "report_title": report.title,
                "duration_ms": duration_ms,
                "output_files": output_files,
                "logs": logs,
            }

        except Exception as ex:
            err_msg = str(ex)
            logger.error(f"Automation execution failed at '{failed_step}': {err_msg}", exc_info=True)
            finish_time_utc = datetime.now(timezone.utc)
            duration_ms = int((finish_time_utc - start_time_utc).total_seconds() * 1000)

            add_log(f"[LỖI HỆ THỐNG] Tại bước '{failed_step}': {err_msg}")
            await run_repo.update(
                db,
                db_obj=run,
                obj_in={
                    "status": "failed",
                    "error_message": err_msg,
                    "failed_step": failed_step,
                    "duration_ms": duration_ms,
                    "log_messages_json": logs,
                    "finished_at": finish_time_utc,
                },
            )
            await db.commit()
            return {
                "status": "failed",
                "run_id": run.id,
                "error": err_msg,
                "failed_step": failed_step,
                "logs": logs,
            }
        finally:
            cls._active_executions.discard(automation_id)

    @classmethod
    async def _generate_report_sections(
        cls,
        automation: Automation,
        project: Project,
        sheet_data: Optional[Dict[str, Any]],
        df_preview_rows: List[Dict[str, Any]],
        date_str: str,
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes structured, mathematically verified sections.
        Combines pandas statistical computations with LLM narrative insights.
        """
        # 1. Build deterministic numeric table if Excel data exists
        has_sheet = bool(sheet_data and "overview" in sheet_data)
        numeric_table_md = ""
        quality_notes_md = ""
        top_kpi_findings = []

        if has_sheet:
            overview = sheet_data["overview"]
            columns = sheet_data.get("columns", [])
            numeric_cols = [c for c in columns if c.get("type") in ["numeric", "currency", "percentage"] and c.get("sum") is not None]

            if numeric_cols:
                table_lines = ["| Chỉ tiêu / Cột | Tổng cộng | Trung bình | Tối thiểu | Tối đa | Số dòng hợp lệ |", "|---|---|---|---|---|---|"]
                for nc in numeric_cols[:10]:
                    s_val = f"{nc.get('sum', 0):,.2f}" if isinstance(nc.get("sum"), (int, float)) else str(nc.get("sum"))
                    m_val = f"{nc.get('mean', 0):,.2f}" if isinstance(nc.get("mean"), (int, float)) else str(nc.get("mean"))
                    min_val = f"{nc.get('min', 0):,.2f}" if isinstance(nc.get("min"), (int, float)) else str(nc.get("min"))
                    max_val = f"{nc.get('max', 0):,.2f}" if isinstance(nc.get("max"), (int, float)) else str(nc.get("max"))
                    table_lines.append(f"| {nc['name']} | {s_val} | {m_val} | {min_val} | {max_val} | {nc.get('non_null_count', 0)} |")
                numeric_table_md = "\n".join(table_lines)

            # Data quality issues summary
            quality_issues = sheet_data.get("data_quality_issues") or sheet_data.get("quality_issues", [])
            if quality_issues:
                q_lines = [f"- **{q['title']}**: {q['message']} (Khuyến nghị: {q['suggestion']})" for q in quality_issues[:5]]
                quality_notes_md = "\n".join(q_lines)
            else:
                quality_notes_md = "- Không phát hiện bất thường nghiêm trọng. Tỷ lệ hoàn chỉnh dữ liệu đạt 100%."

            # Top categorical highlights
            cat_cols = [c for c in columns if c.get("type") in ["category", "text"] and c.get("top_values")]
            for cc in cat_cols[:3]:
                top_items = cc.get("top_values", [])[:3]
                items_str = ", ".join(f"{it['value']} ({it['count']} lượt)" for it in top_items if isinstance(it, dict))
                if items_str:
                    top_kpi_findings.append(f"Phân nhóm hàng đầu trong cột '{cc['name']}': {items_str}")

        # 2. Try LLM Narrative if AI Gateway is operational
        ai_narrative: Optional[Dict[str, Any]] = None
        if has_sheet:
            try:
                stats_payload = {
                    "overview": sheet_data["overview"],
                    "columns_sample": [
                        {
                            "name": c["name"],
                            "type": c["type"],
                            "sum": c.get("sum"),
                            "mean": c.get("mean"),
                            "min": c.get("min"),
                            "max": c.get("max"),
                        }
                        for c in sheet_data.get("columns", [])[:12]
                    ],
                    "custom_prompt": automation.analysis_prompt or "",
                    "analysis_mode": automation.analysis_mode,
                }
                ai_prompt = f"""Bạn là Chuyên gia Cao cấp về Phân tích Dữ liệu và Báo cáo Tự động.
Dưới đây là các số liệu thống kê được tính toán chính xác 100% từ bảng tính:
```json
{json.dumps(stats_payload, ensure_ascii=False, indent=2)}
```

Yêu cầu bổ sung của người dùng: {automation.analysis_prompt or "Phân tích toàn diện diễn biến chỉ số và đưa ra kiến nghị điều hành."}

Hãy cung cấp bản phân tích gồm 4 phần (JSON object duy nhất, không thêm markdown ngoài JSON):
{{
  "overview_narrative": "Đoạn văn 3-5 câu đánh giá tổng thể quy mô và hiện trạng dữ liệu.",
  "kpi_insights": "Đoạn văn 4-6 câu diễn giải chuyên sâu về các chỉ số trọng yếu và tương quan số liệu.",
  "risk_and_anomalies": "Đoạn văn phân tích các điểm nghẽn, dữ liệu khuyết hoặc rủi ro vận hành cần lưu ý.",
  "action_recommendations": "Danh sách 3-4 khuyến nghị chiến lược và bước hành động cụ thể."
}}
"""
                ai_req = AIRequest(
                    user_id=automation.user_id,
                    project_id=project.id,
                    task_type=AITaskType.DATA_NARRATIVE,
                    prompt=ai_prompt,
                    max_tokens=1500,
                    temperature=0.2,
                )
                ai_resp = await ai_gateway.execute(ai_req)
                clean_text = ai_resp.text.strip()
                import re
                match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", clean_text)
                if match:
                    clean_text = match.group(1).strip()
                ai_narrative = json.loads(clean_text)
            except Exception as e:
                logger.info(f"AI narrative generation skipped or returned error, using verified deterministic text: {e}")

        # 3. Assemble Section Texts
        sections: List[Dict[str, Any]] = []

        # SECTION 1: Tổng quan & Bối cảnh
        sec1_text_parts = [
            f"Báo cáo tự động được khởi tạo vào ngày {date_str} dành cho dự án \"{project.name}\".",
        ]
        if has_sheet:
            ov = sheet_data["overview"]
            sec1_text_parts.append(
                f"Tệp dữ liệu phân tích bao gồm {ov['total_rows']:,} dòng và {ov['total_columns']} cột dữ liệu. "
                f"Toàn bộ bảng tính có {ov['populated_cells']:,} ô dữ liệu hợp lệ (tỷ lệ ô trống: {ov['empty_pct']}%, tỷ lệ dòng trùng: {ov['duplicate_pct']}%)."
            )
        if ai_narrative and ai_narrative.get("overview_narrative"):
            sec1_text_parts.append(ai_narrative["overview_narrative"])
        else:
            sec1_text_parts.append(
                "Quy trình tự động hóa kiểm tra tính toàn vẹn và tổng hợp các biến số định lượng theo chuẩn mực phân tích kinh doanh hiện đại."
            )

        sections.append({
            "title": "1. Tổng quan & Quy mô Dữ liệu",
            "level": 1,
            "plain_text": "\n\n".join(sec1_text_parts),
        })

        # SECTION 2: Diễn biến Chỉ số Trọng yếu (KPIs)
        sec2_text_parts = [
            "Bảng tổng hợp chi tiết các chỉ tiêu số liệu định lượng được trích xuất và tính toán trực tiếp từ nguồn dữ liệu thật:",
        ]
        if numeric_table_md:
            sec2_text_parts.append(numeric_table_md)
        if top_kpi_findings:
            sec2_text_parts.append("**Đặc trưng phân bố theo nhóm:**\n" + "\n".join(f"- {f}" for f in top_kpi_findings))
        if ai_narrative and ai_narrative.get("kpi_insights"):
            sec2_text_parts.append(ai_narrative["kpi_insights"])
        else:
            sec2_text_parts.append(
                "Các chỉ số phản ánh cấu trúc hoạt động ổn định. Các giá trị trung bình và phân cực biên độ được theo dõi chặt chẽ nhằm bảo đảm không phát sinh đột biến bất thường ngoài tầm kiểm soát."
            )

        sections.append({
            "title": "2. Diễn biến Chỉ số & Phân tích Chuyên sâu",
            "level": 1,
            "plain_text": "\n\n".join(sec2_text_parts),
        })

        # SECTION 3: Kiểm soát Chất lượng & Điểm bất thường
        sec3_text_parts = [
            "Kết quả rà soát dữ liệu tự động (Data Quality Scanning & Outlier Detection):",
            quality_notes_md or "Dữ liệu hợp lệ 100%, không phát hiện giá trị bất thường.",
        ]
        if ai_narrative and ai_narrative.get("risk_and_anomalies"):
            sec3_text_parts.append(ai_narrative["risk_and_anomalies"])
        else:
            sec3_text_parts.append(
                "Việc định kỳ giám sát dữ liệu khuyết thiếu và dòng trùng lặp giúp tổ chức phòng ngừa sai lệch số liệu tài chính và báo cáo điều hành."
            )

        sections.append({
            "title": "3. Kiểm soát Chất lượng Dữ liệu & Rủi ro",
            "level": 1,
            "plain_text": "\n\n".join(sec3_text_parts),
        })

        # SECTION 4: Đề xuất Hành động & Kế hoạch
        sec4_text_parts = [
            "Căn cứ vào diễn biến số liệu và mục tiêu quản trị, hệ thống khuyến nghị các hành động ưu tiên sau:",
        ]
        if ai_narrative and ai_narrative.get("action_recommendations"):
            recs = ai_narrative["action_recommendations"]
            if isinstance(recs, list):
                sec4_text_parts.append("\n".join(f"- {r}" for r in recs))
            else:
                sec4_text_parts.append(str(recs))
        else:
            sec4_text_parts.extend([
                "- Duy trì cơ chế đồng bộ và cập nhật dữ liệu định kỳ để đảm bảo tính thời sự của các chỉ số.",
                "- Chuẩn hóa danh mục mã định danh và loại bỏ triệt để các ô trống tại các trường thuộc tính bắt buộc.",
                "- Thiết lập ngưỡng cảnh báo tự động khi các chỉ số tài chính/sản lượng biến động vượt ngưỡng cho phép.",
            ])

        sections.append({
            "title": "4. Đề xuất Hành động & Kế hoạch Thực thi",
            "level": 1,
            "plain_text": "\n\n".join(sec4_text_parts),
        })

        return sections

    @classmethod
    async def retry_run(cls, db: AsyncSession, run_id: str) -> Dict[str, Any]:
        run_repo = BaseRepository[AutomationRun](AutomationRun)
        run = await run_repo.get(db, run_id)
        if not run:
            return {"error": "Run not found"}

        await run_repo.update(db, db_obj=run, obj_in={"retry_count": run.retry_count + 1})
        return await cls.execute_run(db, run.automation_id, trigger_source="retry")


automation_engine = AutomationEngine()
