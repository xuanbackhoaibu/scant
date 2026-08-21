import io
import json
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set
from app.services.security.upload_validator import upload_validator
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class CodeKnowledgeGraph:
    """Represents the parsed structural relationships of a software codebase."""

    def __init__(self):
        self.languages: Set[str] = set()
        self.frameworks: Set[str] = set()
        self.dependencies: Dict[str, List[str]] = {}
        self.routes: List[Dict[str, Any]] = []
        self.models: List[Dict[str, Any]] = []
        self.services: List[str] = []
        self.file_tree: List[str] = []

    def to_dict(self) -> Dict[str, Any]:
        return {
            "languages": sorted(list(self.languages)),
            "frameworks": sorted(list(self.frameworks)),
            "dependencies": self.dependencies,
            "routes_count": len(self.routes),
            "routes": self.routes[:30],
            "models_count": len(self.models),
            "models": self.models[:30],
            "services_count": len(self.services),
            "total_files": len(self.file_tree),
            "file_tree_sample": self.file_tree[:40],
        }


class CodebaseIntelligenceEngine:
    """
    Codebase Intelligence & Technical Architecture Engine (Phase U31).
    Scans project archives, extracts code knowledge graphs, and synthesizes evidence-backed technical documentation.
    """

    async def analyze_codebase_archive(
        self,
        zip_bytes: bytes,
        archive_name: str = "project.zip"
    ) -> Dict[str, Any]:
        # 1. Security Check
        is_safe, sec_err = upload_validator.validate_upload(zip_bytes, archive_name)
        if not is_safe:
            raise ValueError(f"Security validation failed: {sec_err}")

        # 2. Build Code Knowledge Graph
        graph = CodeKnowledgeGraph()

        with zipfile.ZipFile(io.BytesIO(zip_bytes)) as zf:
            for file_info in zf.infolist():
                if file_info.is_dir():
                    continue

                fn = file_info.filename
                graph.file_tree.append(fn)
                ext = Path(fn).suffix.lower()

                # Detect Languages
                if ext == ".py":
                    graph.languages.add("Python")
                elif ext in [".ts", ".tsx"]:
                    graph.languages.add("TypeScript")
                elif ext in [".js", ".jsx"]:
                    graph.languages.add("JavaScript")
                elif ext == ".go":
                    graph.languages.add("Go")
                elif ext == ".rs":
                    graph.languages.add("Rust")
                elif ext in [".sql", ".prisma"]:
                    graph.languages.add("SQL/ORM")

                # Read text content safely
                if file_info.file_size < 500_000 and ext in [".py", ".ts", ".tsx", ".js", ".json", ".toml", ".txt"]:
                    try:
                        content = zf.read(file_info).decode("utf-8", errors="ignore")
                        self._inspect_file_content(fn, content, graph)
                    except Exception:
                        pass

        # 3. Generate Evidence-Backed Architecture Documentation
        tech_docs = await self._generate_technical_docs(graph)

        return {
            "code_graph": graph.to_dict(),
            "technical_documentation": tech_docs,
        }

    def _inspect_file_content(self, filename: str, content: str, graph: CodeKnowledgeGraph):
        fn_lower = filename.lower()

        # Dependencies & Frameworks
        if fn_lower.endswith("package.json"):
            try:
                pj = json.loads(content)
                deps = list(pj.get("dependencies", {}).keys())
                graph.dependencies["node"] = deps
                if "next" in deps:
                    graph.frameworks.add("Next.js")
                if "react" in deps:
                    graph.frameworks.add("React")
                if "express" in deps:
                    graph.frameworks.add("Express")
                if "tailwindcss" in deps or "@tailwindcss/postcss" in deps:
                    graph.frameworks.add("TailwindCSS")
            except Exception:
                pass

        elif fn_lower.endswith("requirements.txt") or fn_lower.endswith("pyproject.toml"):
            lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
            graph.dependencies["python"] = lines[:40]
            content_lower = content.lower()
            if "fastapi" in content_lower:
                graph.frameworks.add("FastAPI")
            if "sqlalchemy" in content_lower:
                graph.frameworks.add("SQLAlchemy")
            if "pydantic" in content_lower:
                graph.frameworks.add("Pydantic")
            if "pandas" in content_lower:
                graph.frameworks.add("Pandas")

        # FastAPI / Express Routes
        if "@router." in content or "@app." in content or "app.get(" in content or "router.post(" in content:
            for line in content.splitlines():
                if any(verb in line for verb in ["@router.get", "@router.post", "@router.put", "@router.delete", "@app.get", "@app.post"]):
                    graph.routes.append({"file": filename, "definition": line.strip()})

        # Database Models
        if "Base)" in content or "Column(" in content or "interface " in content or "type " in content:
            for line in content.splitlines():
                if "class " in line and ("(Base)" in line or "(Model)" in line):
                    graph.models.append({"file": filename, "model_name": line.strip()})

        # Services
        if "service" in fn_lower and ("class " in content or "export const " in content):
            graph.services.append(filename)

    async def _generate_technical_docs(self, graph: CodeKnowledgeGraph) -> Dict[str, str]:
        summary_payload = graph.to_dict()
        prompt = f"""Bạn là Principal Software Architect.
Dưới đây là Lược đồ Cấu trúc Source Code đã được phân tích và kiểm chứng 100%:
{json.dumps(summary_payload, ensure_ascii=False, indent=2)}

Nhiệm vụ: Soạn thảo Tài liệu Kỹ thuật (Technical Architecture Documentation) chuẩn mực gồm:
1. Tổng quan Kiến trúc Hệ thống (System Architecture Overview)
2. Công nghệ & Framework sử dụng (Tech Stack)
3. Danh mục API Endpoints & Routes
4. Lược đồ Cơ sở Dữ liệu & Data Models
5. Hướng dẫn Triển khai & Vận hành (Deployment Guide)

QUY TẮC QUAN TRỌNG:
- KHÔNG tự bịa các tính năng hoặc endpoints không có trong dữ liệu phân tích.
- Mọi mô tả phải dựa trên bằng chứng (evidence) từ code đã cung cấp.
"""
        req = AIRequest(
            task_type=AITaskType.DOCUMENT_REVIEW,
            prompt=prompt,
        )
        resp = await ai_gateway.execute(req)

        return {
            "system_architecture": resp.text,
            "tech_stack_summary": f"Ngôn ngữ: {', '.join(graph.languages)} | Frameworks: {', '.join(graph.frameworks)}",
            "total_endpoints_discovered": len(graph.routes),
            "total_models_discovered": len(graph.models),
        }


codebase_intelligence_engine = CodebaseIntelligenceEngine()
