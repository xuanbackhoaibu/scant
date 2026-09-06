"""One role policy for admin APIs; role values from a verified database user only."""
from fastapi import Depends, HTTPException
from app.api.deps import get_current_user
from app.models.entities import User


def admin_role(user: User) -> str:
    if user.is_superuser:
        return 'super_admin'
    return 'admin' if user.role == 'admin' else 'user'


def require_admin(user: User = Depends(get_current_user)) -> User:
    if not user.is_active or admin_role(user) == 'user':
        raise HTTPException(403, 'Quyền quản trị là bắt buộc.')
    return user


def require_super_admin(user: User = Depends(require_admin)) -> User:
    if admin_role(user) != 'super_admin':
        raise HTTPException(403, 'Thao tác này chỉ dành cho Super Admin.')
    return user
