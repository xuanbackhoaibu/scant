"""Trusted authentication identity inherited by request-scoped AI tasks."""
from contextvars import ContextVar
usage_user_id: ContextVar[str | None] = ContextVar('usage_user_id',default=None)
