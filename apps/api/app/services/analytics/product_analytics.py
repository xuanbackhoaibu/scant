from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class AnalyticsEvent(BaseModel):
    event_name: str  # signup, project_created, file_uploaded, generation_started, generation_completed, generation_failed, export_created, template_used
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ProductAnalyticsEngine:
    """
    Privacy-Conscious Product Analytics Engine (Launch Phase L17).
    Monitors user lifecycle and generation funnel metrics without storing private report content.
    """

    def __init__(self):
        self._events: List[AnalyticsEvent] = []

    def track(
        self,
        event_name: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        properties: Optional[Dict[str, Any]] = None
    ) -> AnalyticsEvent:
        # Sanitize: ensure no raw body content is logged
        safe_props = {k: v for k, v in (properties or {}).items() if "content" not in k.lower() and "body" not in k.lower()}
        event = AnalyticsEvent(
            event_name=event_name,
            user_id=user_id,
            project_id=project_id,
            properties=safe_props,
        )
        self._events.append(event)
        return event

    def get_funnel_metrics(self) -> Dict[str, Any]:
        signups = sum(1 for e in self._events if e.event_name == "signup")
        projects = sum(1 for e in self._events if e.event_name == "project_created")
        gen_started = sum(1 for e in self._events if e.event_name == "generation_started")
        gen_completed = sum(1 for e in self._events if e.event_name == "generation_completed")
        gen_failed = sum(1 for e in self._events if e.event_name == "generation_failed")
        exports = sum(1 for e in self._events if e.event_name == "export_created")

        # Conversion ratios
        activation_rate = (projects / signups * 100) if signups > 0 else 0.0
        completion_rate = (gen_completed / gen_started * 100) if gen_started > 0 else 0.0
        failure_rate = (gen_failed / gen_started * 100) if gen_started > 0 else 0.0
        export_rate = (exports / gen_completed * 100) if gen_completed > 0 else 0.0

        return {
            "total_events_logged": len(self._events),
            "signups_count": signups,
            "projects_created_count": projects,
            "generation_started_count": gen_started,
            "generation_completed_count": gen_completed,
            "generation_failed_count": gen_failed,
            "exports_count": exports,
            "funnel_conversion": {
                "activation_rate_pct": round(activation_rate, 1),
                "completion_rate_pct": round(completion_rate, 1),
                "failure_rate_pct": round(failure_rate, 1),
                "export_rate_pct": round(export_rate, 1),
            }
        }


product_analytics = ProductAnalyticsEngine()
