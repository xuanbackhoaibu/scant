import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.database import Base
from app.models.entities import Project, Report, Template, User, Workspace
from app import seed_sample


@pytest.mark.asyncio
async def test_seed_data_is_idempotent(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def init_test_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(seed_sample, "AsyncSessionLocal", TestSession)
    monkeypatch.setattr(seed_sample, "init_db", init_test_db)
    monkeypatch.setattr(
        seed_sample.docx_exporter,
        "generate_docx",
        lambda **kwargs: "sample.docx",
    )

    first = await seed_sample.seed_data()
    second = await seed_sample.seed_data()

    async with TestSession() as db:
        counts = {
            "users": await db.scalar(select(func.count()).select_from(User)),
            "workspaces": await db.scalar(select(func.count()).select_from(Workspace)),
            "templates": await db.scalar(select(func.count()).select_from(Template)),
            "projects": await db.scalar(select(func.count()).select_from(Project)),
            "reports": await db.scalar(select(func.count()).select_from(Report)),
        }

    assert first["email"] == "demo@aireportstudio.pro"
    assert second["email"] == "demo@aireportstudio.pro"
    assert counts == {
        "users": 1,
        "workspaces": 1,
        "templates": 1,
        "projects": 1,
        "reports": 1,
    }


@pytest.mark.asyncio
async def test_seed_data_repairs_legacy_demo_project_metadata(monkeypatch):
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )
    TestSession = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )

    async def init_test_db():
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    monkeypatch.setattr(seed_sample, "AsyncSessionLocal", TestSession)
    monkeypatch.setattr(seed_sample, "init_db", init_test_db)
    monkeypatch.setattr(
        seed_sample.docx_exporter,
        "generate_docx",
        lambda **kwargs: "sample.docx",
    )

    await seed_sample.seed_data()
    async with TestSession() as db:
        project = await db.scalar(
            select(Project).where(Project.name == seed_sample.DEMO_PROJECT_NAME)
        )
        project.metadata_json = None
        await db.commit()

    await seed_sample.seed_data()

    async with TestSession() as db:
        project = await db.scalar(
            select(Project).where(Project.name == seed_sample.DEMO_PROJECT_NAME)
        )

    assert project.metadata_json == {}
