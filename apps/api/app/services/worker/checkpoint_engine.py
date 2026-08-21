from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


class PipelineCheckpointEngine:
    """
    16-Stage Pipeline Checkpoint Engine (Phase U20).
    Persists stage outputs and enables resilient resumption from the last valid checkpoint.
    """

    def __init__(self):
        # job_id -> { stage_name: stage_output_data }
        self._checkpoints: Dict[str, Dict[str, Any]] = {}
        self._last_completed_stage: Dict[str, str] = {}

    def save_checkpoint(
        self,
        job_id: str,
        stage_name: str,
        stage_data: Dict[str, Any]
    ):
        if job_id not in self._checkpoints:
            self._checkpoints[job_id] = {}

        self._checkpoints[job_id][stage_name] = {
            "data": stage_data,
            "saved_at": datetime.now(timezone.utc).isoformat(),
        }
        self._last_completed_stage[job_id] = stage_name

    def get_checkpoint(self, job_id: str, stage_name: str) -> Optional[Dict[str, Any]]:
        job_ck = self._checkpoints.get(job_id, {})
        if stage_name in job_ck:
            return job_ck[stage_name]["data"]
        return None

    def get_last_completed_stage(self, job_id: str) -> Optional[str]:
        return self._last_completed_stage.get(job_id)

    def is_stage_completed(self, job_id: str, stage_name: str) -> bool:
        return stage_name in self._checkpoints.get(job_id, {})

    def clear_checkpoints(self, job_id: str):
        self._checkpoints.pop(job_id, None)
        self._last_completed_stage.pop(job_id, None)


checkpoint_engine = PipelineCheckpointEngine()
