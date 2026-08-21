from typing import Any, Callable, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolDefinition(BaseModel):
    name: str
    description: str
    category: str  # inspection, structure, editing, citation, quality
    parameters: Dict[str, Any]
    requires_approval: bool = False


class AgentToolRegistry:
    """Registry of validated tools available to the Autonomous Document Agent."""

    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(self, tool: ToolDefinition):
        self._tools[tool.name] = tool

    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        return self._tools.get(name)

    def list_tools(self) -> List[ToolDefinition]:
        return list(self._tools.values())

    def get_tool_schemas_for_ai(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": t.name,
                "description": t.description,
                "parameters": t.parameters,
            }
            for t in self._tools.values()
        ]

    def _register_default_tools(self):
        # 1. Inspection Tools
        self.register(ToolDefinition(
            name="read_document",
            category="inspection",
            description="Đọc toàn bộ nội dung và danh sách các phần của tài liệu báo cáo.",
            parameters={"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}
        ))
        self.register(ToolDefinition(
            name="read_section",
            category="inspection",
            description="Đọc chi tiết văn bản của một phần mục cụ thể.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}}, "required": ["section_id"]}
        ))
        self.register(ToolDefinition(
            name="search_project_knowledge",
            category="inspection",
            description="Tìm kiếm các đoạn trích liên quan trong kho tri thức tệp đính kèm của dự án.",
            parameters={"type": "object", "properties": {"project_id": {"type": "string"}, "query": {"type": "string"}}, "required": ["project_id", "query"]}
        ))
        self.register(ToolDefinition(
            name="search_web",
            category="inspection",
            description="Tìm kiếm thông tin và bằng chứng bên ngoài trên Internet.",
            parameters={"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]}
        ))
        self.register(ToolDefinition(
            name="inspect_dataset",
            category="inspection",
            description="Phân tích thống kê và trích xuất số liệu từ tệp CSV/Excel.",
            parameters={"type": "object", "properties": {"file_id": {"type": "string"}}, "required": ["file_id"]}
        ))

        # 2. Structure Tools
        self.register(ToolDefinition(
            name="add_section",
            category="structure",
            description="Thêm một phần mục mới vào đề cương tài liệu.",
            parameters={"type": "object", "properties": {"report_id": {"type": "string"}, "title": {"type": "string"}, "level": {"type": "integer", "default": 1}}, "required": ["report_id", "title"]}
        ))
        self.register(ToolDefinition(
            name="delete_section",
            category="structure",
            description="Xóa một phần mục khỏi tài liệu.",
            requires_approval=True,
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}}, "required": ["section_id"]}
        ))
        self.register(ToolDefinition(
            name="rename_section",
            category="structure",
            description="Đổi tên tiêu đề của một phần mục.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "new_title": {"type": "string"}}, "required": ["section_id", "new_title"]}
        ))

        # 3. Editing Tools
        self.register(ToolDefinition(
            name="insert_text",
            category="editing",
            description="Chèn thêm văn bản vào một phần mục.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "text": {"type": "string"}}, "required": ["section_id", "text"]}
        ))
        self.register(ToolDefinition(
            name="replace_text",
            category="editing",
            description="Thay thế đoạn văn bản cụ thể trong mục.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["section_id", "old_text", "new_text"]}
        ))
        self.register(ToolDefinition(
            name="insert_table",
            category="editing",
            description="Chèn một bảng số liệu với tiêu đề cột và các dòng giá trị.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "headers": {"type": "array", "items": {"type": "string"}}, "rows": {"type": "array"}}, "required": ["section_id", "headers", "rows"]}
        ))
        self.register(ToolDefinition(
            name="insert_chart",
            category="editing",
            description="Chèn biểu đồ trực quan (bar, line, pie) với số liệu.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "chart_type": {"type": "string"}, "labels": {"type": "array"}, "values": {"type": "array"}, "title": {"type": "string"}}, "required": ["section_id", "chart_type", "labels", "values"]}
        ))
        self.register(ToolDefinition(
            name="insert_kpi",
            category="editing",
            description="Chèn khối chỉ số KPI nổi bật (ví dụ Doanh thu: 15 tỷ (+24%)).",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "metric": {"type": "string"}, "value": {"type": "string"}, "change": {"type": "string"}}, "required": ["section_id", "metric", "value"]}
        ))
        self.register(ToolDefinition(
            name="insert_diagram",
            category="editing",
            description="Chèn sơ đồ kiến trúc hoặc quy trình bằng Mermaid code.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "mermaid_code": {"type": "string"}}, "required": ["section_id", "mermaid_code"]}
        ))

        # 4. Citation & Quality Tools
        self.register(ToolDefinition(
            name="add_citation",
            category="citation",
            description="Gắn nguồn trích dẫn đã kiểm chứng vào luận điểm trong văn bản.",
            parameters={"type": "object", "properties": {"section_id": {"type": "string"}, "source_id": {"type": "string"}, "claim_text": {"type": "string"}}, "required": ["section_id", "source_id"]}
        ))
        self.register(ToolDefinition(
            name="run_fact_check",
            category="quality",
            description="Kiểm tra và xác thực toàn bộ số liệu và luận điểm chống hallucination.",
            parameters={"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}
        ))
        self.register(ToolDefinition(
            name="run_quality_check",
            category="quality",
            description="Đánh giá chất lượng văn bản theo thang điểm chuẩn hồ sơ.",
            parameters={"type": "object", "properties": {"report_id": {"type": "string"}}, "required": ["report_id"]}
        ))


agent_tool_registry = AgentToolRegistry()
