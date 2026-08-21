import pytest
import pytest_asyncio
import pandas as pd
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings
from app.services.data.data_engine import data_engine

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
test_engine = create_async_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestAsyncSession = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with TestAsyncSession() as session:
        yield session
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession):
    async def override_get_db():
        yield db_session
    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


def test_data_engine_profiling_and_aggregation():
    # Create sample CSV
    data = {
        "Region": ["North", "South", "North", "Central", "South", "North"],
        "Product": ["EV Sedan", "EV SUV", "EV Sedan", "EV Truck", "EV SUV", "EV Sedan"],
        "Revenue": [1200, 1800, 1100, 950, 2200, 1350],
        "UnitsSold": [12, 15, 11, 8, 20, 14],
    }
    df = pd.DataFrame(data)
    csv_path = settings.UPLOAD_DIR / "sample_sales.csv"
    df.to_csv(str(csv_path), index=False)

    # 1. Test profile
    profile = data_engine.profile_dataset(str(csv_path))
    assert profile["total_rows"] == 6
    assert profile["total_columns"] == 4
    assert len(profile["columns"]) == 4

    # 2. Test aggregate by Region sum Revenue
    agg = data_engine.aggregate_data(str(csv_path), group_by="Region", metric_column="Revenue", aggregation="sum")
    assert "North" in agg["labels"]
    assert "South" in agg["labels"]
    assert len(agg["values"]) == 3

    # 3. Test chart spec
    chart = data_engine.build_chart_specification(str(csv_path), chart_type="bar", group_by="Region", metric_column="Revenue")
    assert chart["chart_type"] == "bar"
    assert len(chart["datasets"][0]["data"]) == 3


@pytest.mark.asyncio
async def test_data_api_flow(client: AsyncClient):
    reg_res = await client.post("/api/v1/auth/register", json={
        "email": "data_lead@corp.com",
        "password": "Password123!",
        "name": "Data Lead"
    })
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post("/api/v1/projects", json={
        "name": "Dự án Dữ liệu Doanh thu",
        "type": "data_analysis"
    }, headers=headers)
    project_id = proj_res.json()["id"]

    # Upload CSV file
    csv_content = b"Department,Budget,Staff\nSales,50000,20\nMarketing,30000,10\nEngineering,80000,35\n"
    files = {"file": ("departments.csv", csv_content, "text/csv")}
    data = {"project_id": project_id, "document_type": "dataset"}
    upload_res = await client.post("/api/v1/files/upload", data=data, files=files, headers=headers)
    file_id = upload_res.json()["id"]

    # Profile dataset
    profile_res = await client.get(f"/api/v1/data/profile/{file_id}", headers=headers)
    assert profile_res.status_code == 200
    assert profile_res.json()["total_rows"] == 3

    # Aggregate
    agg_res = await client.post("/api/v1/data/aggregate", json={
        "file_id": file_id,
        "group_by": "Department",
        "metric_column": "Budget",
        "aggregation": "sum"
    }, headers=headers)
    assert agg_res.status_code == 200
    assert "Engineering" in agg_res.json()["labels"]
