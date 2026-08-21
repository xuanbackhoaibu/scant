from typing import Any, Dict, List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from app.services.ai.types import AITaskType


class PromptVersion(BaseModel):
    prompt_key: str
    version: str  # e.g., "v1.0.0", "v1.2.0"
    template: str
    task_type: AITaskType
    status: str = "active"  # "active" | "deprecated" | "draft"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CentralizedPromptRegistry:
    """
    Centralized Prompt Registry & Versioning Engine (Launch Phase L8).
    Eliminates scattered hardcoded prompts across services and tracks prompt versions in AI usage logs.
    """

    def __init__(self):
        self._prompts: Dict[str, Dict[str, PromptVersion]] = {}
        self._active_versions: Dict[str, str] = {}
        self._initialize_core_prompts()

    def _initialize_core_prompts(self):
        core_prompts = [
            PromptVersion(
                prompt_key="section_writing_universal",
                version="v1.0.0",
                template="Bạn là Chuyên gia Soạn thảo Văn kiện Cấp cao. Hãy soạn thảo phần {section_title} dựa trên ngữ cảnh: {context}.",
                task_type=AITaskType.SECTION_WRITING,
                status="active",
            ),
            PromptVersion(
                prompt_key="fact_checking_strict",
                version="v1.0.0",
                template="Bạn là Thẩm định viên Sự thật (Fact Inspector). Hãy đối chiếu từng tuyên bố sau với tài liệu nguồn: {claims}.",
                task_type=AITaskType.FACT_CHECK,
                status="active",
            ),
            PromptVersion(
                prompt_key="data_narrative_deterministic",
                version="v1.0.0",
                template="Bạn là Chuyên viên Phân tích Dữ liệu. Diễn giải các chỉ số KPI đã tính toán chính xác sau: {kpis}.",
                task_type=AITaskType.DATA_NARRATIVE,
                status="active",
            ),
            PromptVersion(
                prompt_key="research_synthesis_multi_hop",
                version="v1.0.0",
                template="Bạn là Nghiên cứu viên Trưởng. Tổng hợp các bằng chứng điều tra từ đồ thị nghiên cứu: {evidence_graph}.",
                task_type=AITaskType.RESEARCH_SYNTHESIS,
                status="active",
            ),
            PromptVersion(
                prompt_key="code_doc_generation",
                version="v1.0.0",
                template="Bạn là Kiến trúc sư Phần mềm. Soạn thảo tài liệu kỹ thuật dựa trên Code Graph: {code_graph}.",
                task_type=AITaskType.DOCUMENT_REVIEW,
                status="active",
            ),
        ]

        for p in core_prompts:
            self.register_prompt(p)

    def register_prompt(self, prompt: PromptVersion):
        if prompt.prompt_key not in self._prompts:
            self._prompts[prompt.prompt_key] = {}
        self._prompts[prompt.prompt_key][prompt.version] = prompt
        if prompt.status == "active":
            self._active_versions[prompt.prompt_key] = prompt.version

    def get_prompt(self, prompt_key: str, version: Optional[str] = None) -> Optional[PromptVersion]:
        if prompt_key not in self._prompts:
            return None
        ver = version or self._active_versions.get(prompt_key)
        return self._prompts[prompt_key].get(ver)

    def render_prompt(self, prompt_key: str, variables: Dict[str, Any], version: Optional[str] = None) -> tuple[str, str]:
        pv = self.get_prompt(prompt_key, version)
        if not pv:
            raise KeyError(f"Prompt key '{prompt_key}' not found in registry.")
        rendered = pv.template
        for k, v in variables.items():
            rendered = rendered.replace(f"{{{k}}}", str(v))
        return rendered, pv.version


prompt_registry = CentralizedPromptRegistry()
