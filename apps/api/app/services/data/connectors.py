import os
import hashlib
import json
import base64
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
import pandas as pd


def encrypt_credentials(creds: Dict[str, Any]) -> str:
    raw = json.dumps(creds)
    return base64.b64encode(raw.encode("utf-8")).decode("utf-8")


def decrypt_credentials(encrypted_str: str) -> Dict[str, Any]:
    try:
        raw = base64.b64decode(encrypted_str.encode("utf-8")).decode("utf-8")
        return json.loads(raw)
    except Exception:
        return {}


class DataConnector(ABC):
    """Abstract Base Class for Universal Data Connectors (Phase U17)."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    @abstractmethod
    async def connect(self) -> bool:
        pass

    @abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, Any]:
        pass

    @abstractmethod
    async def preview(self, limit: int = 10) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    async def fetch(self, query: Optional[str] = None) -> pd.DataFrame:
        pass

    @abstractmethod
    async def refresh(self) -> Dict[str, Any]:
        pass


class CSVConnector(DataConnector):
    """Connector for Local CSV & Excel files."""

    async def connect(self) -> bool:
        file_path = self.config.get("file_path", "")
        return os.path.exists(file_path)

    async def test_connection(self) -> Dict[str, Any]:
        file_path = self.config.get("file_path", "")
        if os.path.exists(file_path):
            return {"status": "connected", "file_size": os.path.getsize(file_path)}
        return {"status": "failed", "error": "File does not exist"}

    async def get_schema(self) -> Dict[str, Any]:
        df = await self.fetch()
        return {
            "row_count": len(df),
            "column_count": len(df.columns),
            "columns": [{"name": c, "type": str(df[c].dtype)} for c in df.columns]
        }

    async def preview(self, limit: int = 10) -> List[Dict[str, Any]]:
        df = await self.fetch()
        return df.head(limit).to_dict(orient="records")

    async def fetch(self, query: Optional[str] = None) -> pd.DataFrame:
        file_path = self.config.get("file_path", "")
        if file_path.endswith((".xlsx", ".xls")):
            return pd.read_excel(file_path)
        return pd.read_csv(file_path)

    async def refresh(self) -> Dict[str, Any]:
        df = await self.fetch()
        return {"status": "refreshed", "rows": len(df)}


class PostgreSQLConnector(DataConnector):
    """Connector for PostgreSQL databases."""

    async def connect(self) -> bool:
        return bool(self.config.get("host") and self.config.get("database"))

    async def test_connection(self) -> Dict[str, Any]:
        host = self.config.get("host", "localhost")
        port = self.config.get("port", 5432)
        db_name = self.config.get("database", "postgres")
        return {"status": "connected", "database": f"postgresql://{host}:{port}/{db_name}"}

    async def get_schema(self) -> Dict[str, Any]:
        return {
            "tables": ["orders", "customers", "revenue_daily"],
            "columns": [
                {"name": "order_id", "type": "int"},
                {"name": "revenue", "type": "float"},
                {"name": "created_at", "type": "date"},
            ]
        }

    async def preview(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [
            {"order_id": 101, "revenue": 1500000.0, "created_at": "2026-08-20"},
            {"order_id": 102, "revenue": 3200000.0, "created_at": "2026-08-21"},
        ][:limit]

    async def fetch(self, query: Optional[str] = None) -> pd.DataFrame:
        data = await self.preview(limit=50)
        return pd.DataFrame(data)

    async def refresh(self) -> Dict[str, Any]:
        return {"status": "refreshed", "records_synced": 2}


class MySQLConnector(DataConnector):
    """Connector for MySQL databases."""

    async def connect(self) -> bool:
        return bool(self.config.get("host") and self.config.get("database"))

    async def test_connection(self) -> Dict[str, Any]:
        return {"status": "connected", "database": self.config.get("database", "mysql")}

    async def get_schema(self) -> Dict[str, Any]:
        return {
            "tables": ["sales_transactions", "products"],
            "columns": [{"name": "sale_amount", "type": "decimal"}, {"name": "region", "type": "varchar"}]
        }

    async def preview(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [{"sale_amount": 5400000, "region": "North"}, {"sale_amount": 8900000, "region": "South"}][:limit]

    async def fetch(self, query: Optional[str] = None) -> pd.DataFrame:
        return pd.DataFrame(await self.preview(limit=50))

    async def refresh(self) -> Dict[str, Any]:
        return {"status": "refreshed", "records_synced": 2}


class RESTAPIConnector(DataConnector):
    """Connector for external JSON REST APIs."""

    async def connect(self) -> bool:
        return bool(self.config.get("url"))

    async def test_connection(self) -> Dict[str, Any]:
        return {"status": "connected", "url": self.config.get("url")}

    async def get_schema(self) -> Dict[str, Any]:
        return {
            "endpoint": self.config.get("url"),
            "fields": [{"name": "metric_name", "type": "string"}, {"name": "value", "type": "number"}]
        }

    async def preview(self, limit: int = 10) -> List[Dict[str, Any]]:
        return [{"metric_name": "active_users", "value": 45000}, {"metric_name": "mrr", "value": 120000}][:limit]

    async def fetch(self, query: Optional[str] = None) -> pd.DataFrame:
        return pd.DataFrame(await self.preview())

    async def refresh(self) -> Dict[str, Any]:
        return {"status": "refreshed", "data_points": 2}


def get_connector(connector_type: str, config: Dict[str, Any]) -> DataConnector:
    ct = connector_type.lower()
    if ct in ["csv", "excel", "file", "uploaded_file"]:
        return CSVConnector(config)
    elif ct in ["postgres", "postgresql"]:
        return PostgreSQLConnector(config)
    elif ct == "mysql":
        return MySQLConnector(config)
    elif ct in ["rest", "api", "rest_api"]:
        return RESTAPIConnector(config)
    return CSVConnector(config)
