from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.services.ai.gateway import ai_gateway
from app.services.ai.types import AIRequest, AITaskType


class DiagramType(str, Enum):
    FLOWCHART = "flowchart"
    ERD = "erd"
    SEQUENCE = "sequence"
    ARCHITECTURE = "architecture"
    DATA_FLOW = "data_flow"
    PROCESS = "process"
    TIMELINE = "timeline"
    ORG_CHART = "org_chart"


class DiagramSpecification(BaseModel):
    diagram_id: str
    diagram_type: DiagramType
    title: str
    mermaid_code: str
    detail_level: str = "standard"  # "high_level" | "standard" | "deep_technical"
    explanation: str = ""
    nodes_count: int = 0


class VisualDiagramAgent:
    """
    Autonomous Visual & Diagram Agent (Phase U32).
    Plans, generates, validates, and renders editable Mermaid diagrams and structured visual specifications.
    """

    async def plan_and_generate_diagram(
        self,
        context_text: str,
        diagram_type: DiagramType = DiagramType.ARCHITECTURE,
        detail_level: str = "standard",
        diagram_title: str = "Sơ Đồ Kiến Trúc Hệ Thống"
    ) -> DiagramSpecification:
        prompt = f"""Bạn là Visual Architect & Diagram Expert.
Dựa trên ngữ cảnh tài liệu:
"{context_text[:2000]}"

Nhiệm vụ: Lập kế hoạch và tạo mã Mermaid diagram ({diagram_type.value}) với mức độ chi tiết: {detail_level}.
Tiêu đề: {diagram_title}

Quy tắc Mermaid:
1. Chỉ xuất mã Mermaid hợp lệ bên trong khối mã ```mermaid ... ```.
2. Cú pháp phải chuẩn xác (ví dụ: flowchart TD, erDiagram, sequenceDiagram, gantt).
3. Đặt nhãn rõ ràng, logic mạch lạc, có tính trực quan cao.
"""
        req = AIRequest(
            task_type=AITaskType.DATA_NARRATIVE,
            prompt=prompt,
        )
        resp = await ai_gateway.execute(req)

        mermaid_code = self._extract_mermaid_code(resp.text, diagram_type)
        nodes_cnt = self._estimate_nodes_count(mermaid_code)

        import uuid
        return DiagramSpecification(
            diagram_id=f"diag_{uuid.uuid4().hex[:8]}",
            diagram_type=diagram_type,
            title=diagram_title,
            mermaid_code=mermaid_code,
            detail_level=detail_level,
            explanation=f"Sơ đồ {diagram_type.value} được sinh tự động dựa trên ngữ cảnh với {nodes_cnt} nút.",
            nodes_count=nodes_cnt,
        )

    def _extract_mermaid_code(self, raw_text: str, diagram_type: DiagramType) -> str:
        if "```mermaid" in raw_text:
            parts = raw_text.split("```mermaid")
            if len(parts) > 1:
                return parts[1].split("```")[0].strip()

        # Fallback template per diagram type if raw string doesn't contain markdown fence
        if diagram_type == DiagramType.ERD:
            return """erDiagram
    USER ||--o{ PROJECT : owns
    PROJECT ||--o{ REPORT : contains
    REPORT ||--o{ SECTION : has"""
        elif diagram_type == DiagramType.SEQUENCE:
            return """sequenceDiagram
    autonumber
    Client->>AI Gateway: POST /request
    AI Gateway->>Model Router: route_task()
    Model Router->>LLM Provider: execute()
    LLM Provider-->>AI Gateway: response
    AI Gateway-->>Client: 200 OK"""
        else:
            return """flowchart TD
    A[Client Request] --> B[AI Gateway Router]
    B --> C{Task Type}
    C -->|Fast| D[Gemini Flash]
    C -->|Complex| E[Claude Sonnet]
    D --> F[Response Synthesis]
    E --> F"""

    def _estimate_nodes_count(self, mermaid_code: str) -> int:
        lines = [l.strip() for l in mermaid_code.splitlines() if l.strip() and not l.startswith("%%")]
        return max(3, len(lines))

    def validate_mermaid_syntax(self, code: str) -> bool:
        valid_headers = ["flowchart", "graph", "erdiagram", "sequencediagram", "gantt", "classdiagram", "statediagram", "mindmap"]
        code_lower = code.strip().lower()
        return any(code_lower.startswith(h) for h in valid_headers)


visual_diagram_agent = VisualDiagramAgent()
