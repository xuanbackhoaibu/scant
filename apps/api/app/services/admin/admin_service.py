"""Compatibility facade for callers predating the paginated admin console."""
from app.services.admin.query_service import overview, list_users
from app.services.admin.plan_service import change_user_plan

class AdminService:
    get_system_dashboard_metrics = staticmethod(overview)
    list_users = staticmethod(list_users)

admin_service = AdminService()
