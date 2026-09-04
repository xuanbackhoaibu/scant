import asyncio
import io
import os
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import settings
from app.models.entities import Job, Project, Report, ReportSection
from app.repositories.base import BaseRepository
from app.repositories.project_repo import project_repo
from app.repositories.report_repo import report_repo
from app.services.agent.agentic_report_orchestrator import agentic_orchestrator


class BulkReportService:
    """
    Enterprise Batch & Bulk Autonomous Report Generator.
    Processes CSV/XLSX job sheets, generates dozens of reports concurrently, and packages into ZIP.
    """

    @classmethod
    async def parse_batch_file(cls, file_bytes: bytes, filename: str) -> List[Dict[str, Any]]:
        rows = []
        if filename.endswith(".csv"):
            df = pd.read_csv(io.BytesIO(file_bytes))
        else:
            df = pd.read_excel(io.BytesIO(file_bytes))

        # Normalize column names
        df.columns = [str(c).strip().lower().replace(" ", "_") for c in df.columns]

        for idx, row in df.iterrows():
            title = str(row.get("title") or row.get("topic") or row.get("tên_đề_tài") or f"Báo cáo số {idx+1}").strip()
            prompt = str(row.get("prompt") or row.get("description") or row.get("mô_tả") or title).strip()
            doc_type = str(row.get("type") or row.get("loại") or "business_report").strip()
            audience = str(row.get("audience") or row.get("đối_tượng") or "Ban Lãnh đạo").strip()

            rows.append({
                "row_index": idx + 1,
                "title": title,
                "prompt": prompt,
                "type": doc_type,
                "audience": audience,
            })
        return rows

    @classmethod
    async def launch_batch_job(
        cls,
        user_id: str,
        batch_title: str,
        items: List[Dict[str, Any]],
        db: AsyncSession
    ) -> Dict[str, Any]:
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        job_repo = BaseRepository[Job](Job)

        created_jobs = []
        for item in items:
            # 1. Create Project
            proj = await project_repo.create(db, obj_in={
                "user_id": user_id,
                "name": item["title"],
                "type": item["type"],
                "description": item["prompt"],
            })

            # 2. Create Report
            rep = await report_repo.create(db, obj_in={
                "project_id": proj.id,
                "title": item["title"],
                "report_type": item["type"],
                "status": "generating",
                "revision": 1,
            })

            # 3. Create Job
            job = await job_repo.create(db, obj_in={
                "project_id": proj.id,
                "job_type": "bulk_report_item",
                "status": "running",
                "progress_percent": 10,
                "status_message": f"Đang chuẩn bị sinh báo cáo: {item['title']}",
                "metadata_json": {"batch_id": batch_id, "report_id": rep.id, "project_id": proj.id},
            })

            # Launch background worker
            asyncio.create_task(
                agentic_orchestrator.run_workflow(
                    job_id=job.id,
                    project_id=proj.id,
                    report_id=rep.id,
                    instructions=item["prompt"]
                )
            )

            created_jobs.append({
                "item_index": item["row_index"],
                "title": item["title"],
                "project_id": proj.id,
                "report_id": rep.id,
                "job_id": job.id,
            })

        return {
            "batch_id": batch_id,
            "batch_title": batch_title,
            "total_items": len(items),
            "jobs": created_jobs,
            "status": "processing",
        }


bulk_report_service = BulkReportService()
