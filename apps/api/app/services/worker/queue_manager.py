import asyncio
import uuid
import time
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime, timezone


class TaskState:
    QUEUED = "queued"
    RUNNING = "running"
    PAUSED = "paused"
    WAITING_FOR_USER = "waiting_for_user"
    RETRYING = "retrying"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueueTask:
    def __init__(
        self,
        task_id: str,
        task_name: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None
    ):
        self.task_id = task_id
        self.task_name = task_name
        self.payload = payload
        self.idempotency_key = idempotency_key
        self.state = TaskState.QUEUED
        self.progress_percent = 0
        self.retry_count = 0
        self.max_retries = 3
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        self.heartbeat_at = datetime.now(timezone.utc)
        self.created_at = datetime.now(timezone.utc)
        self.finished_at: Optional[datetime] = None


class ProductionTaskQueue:
    """
    Production Worker Queue Manager (Phase U20).
    Provides resilient task queueing, worker dispatch, heartbeat tracking, and idempotency deduplication.
    """

    def __init__(self):
        self._tasks: Dict[str, QueueTask] = {}
        self._idempotency_index: Dict[str, str] = {}
        self._handlers: Dict[str, Callable] = {}
        self._queue: asyncio.Queue = asyncio.Queue()

    def register_handler(self, task_name: str, handler: Callable):
        self._handlers[task_name] = handler

    async def enqueue(
        self,
        task_name: str,
        payload: Dict[str, Any],
        idempotency_key: Optional[str] = None,
        max_retries: int = 3
    ) -> QueueTask:
        # Idempotency deduplication check
        if idempotency_key and idempotency_key in self._idempotency_index:
            existing_id = self._idempotency_index[idempotency_key]
            existing_task = self._tasks.get(existing_id)
            if existing_task and existing_task.state not in [TaskState.FAILED, TaskState.CANCELLED]:
                return existing_task

        task_id = str(uuid.uuid4())
        task = QueueTask(task_id, task_name, payload, idempotency_key)
        task.max_retries = max_retries

        self._tasks[task_id] = task
        if idempotency_key:
            self._idempotency_index[idempotency_key] = task_id

        await self._queue.put(task_id)
        return task

    def get_task(self, task_id: str) -> Optional[QueueTask]:
        return self._tasks.get(task_id)

    def cancel_task(self, task_id: str) -> bool:
        task = self._tasks.get(task_id)
        if task and task.state in [TaskState.QUEUED, TaskState.RUNNING, TaskState.PAUSED, TaskState.RETRYING]:
            task.state = TaskState.CANCELLED
            task.finished_at = datetime.now(timezone.utc)
            return True
        return False

    async def process_next_task(self) -> Optional[QueueTask]:
        """Executes next task in queue with error handling and retry policy."""
        try:
            task_id = await asyncio.wait_for(self._queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            return None

        task = self._tasks.get(task_id)
        if not task or task.state == TaskState.CANCELLED:
            return task

        handler = self._handlers.get(task.task_name)
        if not handler:
            task.state = TaskState.FAILED
            task.error_message = f"No registered worker handler for task: {task.task_name}"
            task.finished_at = datetime.now(timezone.utc)
            return task

        task.state = TaskState.RUNNING
        task.heartbeat_at = datetime.now(timezone.utc)

        try:
            res = handler(task.payload)
            if asyncio.iscoroutine(res):
                res = await res
            task.state = TaskState.COMPLETED
            task.progress_percent = 100
            task.result = res
            task.finished_at = datetime.now(timezone.utc)
        except Exception as e:
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.state = TaskState.RETRYING
                await self._queue.put(task_id)
            else:
                task.state = TaskState.FAILED
                task.error_message = str(e)
                task.finished_at = datetime.now(timezone.utc)

        return task


task_queue = ProductionTaskQueue()
