from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel


class ImpactLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class ToolActionImpact(BaseModel):
    action_name: str
    impact_level: ImpactLevel
    requires_changeset: bool
    requires_explicit_confirmation: bool
    description: str


ACTION_IMPACT_REGISTRY: Dict[str, ToolActionImpact] = {
    # LOW
    "rewrite_sentence": ToolActionImpact(
        action_name="rewrite_sentence",
        impact_level=ImpactLevel.LOW,
        requires_changeset=False,
        requires_explicit_confirmation=False,
        description="Chỉnh sửa câu chữ, ngữ pháp hoặc định dạng văn bản nhỏ",
    ),
    "format_text": ToolActionImpact(
        action_name="format_text",
        impact_level=ImpactLevel.LOW,
        requires_changeset=False,
        requires_explicit_confirmation=False,
        description="Định dạng in đậm, in nghiêng hoặc căn lề",
    ),
    # MEDIUM
    "insert_section": ToolActionImpact(
        action_name="insert_section",
        impact_level=ImpactLevel.MEDIUM,
        requires_changeset=False,
        requires_explicit_confirmation=False,
        description="Thêm một phần mục mới vào báo cáo",
    ),
    "insert_table": ToolActionImpact(
        action_name="insert_table",
        impact_level=ImpactLevel.MEDIUM,
        requires_changeset=False,
        requires_explicit_confirmation=False,
        description="Chèn bảng số liệu hoặc biểu đồ",
    ),
    "insert_citation": ToolActionImpact(
        action_name="insert_citation",
        impact_level=ImpactLevel.MEDIUM,
        requires_changeset=False,
        requires_explicit_confirmation=False,
        description="Bổ sung trích dẫn tài liệu tham khảo",
    ),
    # HIGH
    "delete_section": ToolActionImpact(
        action_name="delete_section",
        impact_level=ImpactLevel.HIGH,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Xóa một hoặc nhiều phần mục của báo cáo",
    ),
    "replace_large_content": ToolActionImpact(
        action_name="replace_large_content",
        impact_level=ImpactLevel.HIGH,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Thay thế toàn bộ hoặc phần lớn nội dung tài liệu",
    ),
    "change_dataset": ToolActionImpact(
        action_name="change_dataset",
        impact_level=ImpactLevel.HIGH,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Thay đổi nguồn dữ liệu định lượng gốc",
    ),
    "change_template": ToolActionImpact(
        action_name="change_template",
        impact_level=ImpactLevel.HIGH,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Áp dụng mẫu template mới làm thay đổi bố cục",
    ),
    # CRITICAL
    "publish_document": ToolActionImpact(
        action_name="publish_document",
        impact_level=ImpactLevel.CRITICAL,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Xuất bản tài liệu chính thức ra bên ngoài",
    ),
    "delete_document": ToolActionImpact(
        action_name="delete_document",
        impact_level=ImpactLevel.CRITICAL,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Xóa vĩnh viễn báo cáo hoặc toàn bộ dự án",
    ),
    "change_access_control": ToolActionImpact(
        action_name="change_access_control",
        impact_level=ImpactLevel.CRITICAL,
        requires_changeset=True,
        requires_explicit_confirmation=True,
        description="Thay đổi quyền truy cập hoặc chia sẻ ra ngoài workspace",
    ),
}


class AgentImpactPolicyEnforcer:
    """Enforces safety gates based on agent tool action impact levels."""

    @staticmethod
    def get_action_impact(action_name: str) -> ToolActionImpact:
        return ACTION_IMPACT_REGISTRY.get(
            action_name,
            ToolActionImpact(
                action_name=action_name,
                impact_level=ImpactLevel.MEDIUM,
                requires_changeset=False,
                requires_explicit_confirmation=False,
                description="Tác vụ mặc định",
            )
        )

    @classmethod
    def validate_action_execution(
        cls,
        action_name: str,
        has_changeset: bool = False,
        has_user_confirmation: bool = False
    ) -> Tuple[bool, Optional[str]]:
        impact = cls.get_action_impact(action_name)
        if impact.requires_changeset and not has_changeset and not has_user_confirmation:
            return False, f"Action '{action_name}' có mức độ ảnh hưởng {impact.impact_level.value}, bắt buộc phải tạo ChangeSet hoặc xác nhận tường minh trước khi thực thi."
        return True, None


agent_impact_enforcer = AgentImpactPolicyEnforcer()
