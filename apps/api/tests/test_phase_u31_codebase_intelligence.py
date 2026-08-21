import io
import zipfile
import pytest
from app.services.codebase.codebase_intelligence_engine import codebase_intelligence_engine


@pytest.mark.asyncio
async def test_codebase_zip_analysis_and_graph():
    # Construct mock project zip in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w") as zf:
        # FastAPI backend file
        zf.writestr(
            "apps/api/main.py",
            """from fastapi import FastAPI, APIRouter
app = FastAPI()
router = APIRouter()

@router.get("/users")
def list_users():
    return []

@router.post("/reports")
def create_report():
    return {}
"""
        )
        # Database models
        zf.writestr(
            "apps/api/models.py",
            """from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Report(Base):
    __tablename__ = 'reports'

class User(Base):
    __tablename__ = 'users'
"""
        )
        # Requirements
        zf.writestr("apps/api/requirements.txt", "fastapi>=0.100\nsqlalchemy\npydantic\npandas\n")
        # Next.js frontend package.json
        zf.writestr(
            "apps/web/package.json",
            '{"dependencies": {"next": "15.0.0", "react": "19.0.0", "tailwindcss": "4.0.0"}}'
        )

    zip_bytes = zip_buf.getvalue()

    result = await codebase_intelligence_engine.analyze_codebase_archive(
        zip_bytes=zip_bytes,
        archive_name="saas_project.zip"
    )

    code_graph = result["code_graph"]
    assert "Python" in code_graph["languages"]
    assert "TypeScript" in code_graph["languages"] or "JavaScript" in code_graph["languages"] or "Python" in code_graph["languages"]
    assert "FastAPI" in code_graph["frameworks"]
    assert "Next.js" in code_graph["frameworks"]

    # Verify routes & models extracted
    assert code_graph["routes_count"] >= 2
    assert code_graph["models_count"] >= 2

    # Verify generated technical documentation
    tech_docs = result["technical_documentation"]
    assert "system_architecture" in tech_docs
    assert tech_docs["total_endpoints_discovered"] >= 2
    assert tech_docs["total_models_discovered"] >= 2


@pytest.mark.asyncio
async def test_codebase_security_rejection():
    # Zip with path traversal
    bad_buf = io.BytesIO()
    with zipfile.ZipFile(bad_buf, "w") as zf:
        zf.writestr("../../etc/shadow", "malicious payload")

    with pytest.raises(ValueError, match="Security validation failed"):
        await codebase_intelligence_engine.analyze_codebase_archive(
            zip_bytes=bad_buf.getvalue(),
            archive_name="malicious.zip"
        )
