"""Append-only administrative audit; writes share the mutation transaction."""
import re
from datetime import datetime, timezone
from app.models.entities import AuditLog

SENSITIVE = re.compile(r'password|secret|authorization|access_token|refresh_token|api_key|cookie|credential|content_text|payload', re.I)


def safe_value(value):
    if isinstance(value, dict):
        return {str(k): safe_value(v) for k,v in value.items() if not SENSITIVE.search(str(k))}
    if isinstance(value, (list,tuple)):
        return [safe_value(v) for v in value[:100]]
    if isinstance(value, datetime):
        return value.replace(tzinfo=value.tzinfo or timezone.utc).isoformat()
    if isinstance(value, str):
        value = re.sub(r'(?i)(bearer\s+|(?:api[_-]?key|token|secret|password)\s*[=:]\s*)[^\s,;]+', r'\1[REDACTED]', value)
        value = re.sub(r'\b(?:sk-|AIza)[A-Za-z0-9_-]{12,}', '[REDACTED]', value)
        value = re.sub(r'\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[REDACTED]', value)
        return value[:2000]
    return value if value is None or isinstance(value,(bool,int,float)) else str(value)[:200]


async def record_audit(db, actor, action, target_type, target_id, before, after, reason, request=None):
    if not reason or len(reason.strip()) < 3:
        from fastapi import HTTPException
        raise HTTPException(422, 'Vui lòng nhập lý do (ít nhất 3 ký tự).')
    event = AuditLog(user_id=actor.id if actor else None, action=action, resource_type=target_type,
        resource_id=target_id, details_json=safe_value({
            'before':before,'after':after,'reason':reason.strip(),
            'ip_address':request.client.host if request and request.client else None,
            'user_agent':request.headers.get('user-agent','')[:300] if request else None,
        }))
    db.add(event)
    await db.flush()
    return event
