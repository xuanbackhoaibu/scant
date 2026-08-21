from fastapi import APIRouter
from app.api.v1.auth import router as auth_router
from app.api.v1.projects import router as projects_router
from app.api.v1.health import router as health_router
from app.api.v1.files import router as files_router
from app.api.v1.templates import router as templates_router
from app.api.v1.ai import router as ai_router
from app.api.v1.reports import router as reports_router
from app.api.v1.research import router as research_router
from app.api.v1.exports import router as exports_router
from app.api.v1.data import router as data_router
from app.api.v1.changesets import router as changesets_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(projects_router)
api_router.include_router(files_router)
api_router.include_router(templates_router)
api_router.include_router(ai_router)
api_router.include_router(reports_router)
api_router.include_router(research_router)
api_router.include_router(exports_router)
api_router.include_router(data_router)
api_router.include_router(changesets_router)

__all__ = ["api_router"]
