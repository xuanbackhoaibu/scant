import json
import logging
import time
import uuid
from typing import Any, Dict, Optional


class StructuredLogger:
    """
    Production Structured JSON Logger (Phase U25).
    Generates uniform, structured log events with request_id and trace_id for APM / Sentry / CloudWatch.
    """

    def __init__(self):
        self.logger = logging.getLogger("ai_report_studio")
        self.logger.setLevel(logging.INFO)

    def log_http_request(
        self,
        request_id: str,
        method: str,
        route: str,
        status_code: int,
        duration_ms: int,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        log_event = {
            "event_type": "http_request",
            "request_id": request_id,
            "method": method,
            "route": route,
            "status_code": status_code,
            "duration_ms": duration_ms,
            "user_id": user_id,
            "timestamp": time.time(),
        }
        self.logger.info(json.dumps(log_event))
        return log_event

    def log_ai_trace(
        self,
        trace_id: str,
        task_type: str,
        provider: str,
        model: str,
        latency_ms: int,
        tokens: int,
        cost_usd: float,
        status: str = "success",
    ) -> Dict[str, Any]:
        log_event = {
            "event_type": "ai_trace",
            "trace_id": trace_id,
            "task_type": task_type,
            "provider": provider,
            "model": model,
            "latency_ms": latency_ms,
            "total_tokens": tokens,
            "estimated_cost_usd": cost_usd,
            "status": status,
            "timestamp": time.time(),
        }
        self.logger.info(json.dumps(log_event))
        return log_event


structured_logger = StructuredLogger()
