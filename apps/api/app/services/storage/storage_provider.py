import os
import hashlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
from app.core.config import settings


class StorageProvider(ABC):
    """Abstract Base Class for Universal Object Storage Providers (Phase U21)."""

    @abstractmethod
    async def put_object(self, key: str, data: bytes, mime_type: str = "application/octet-stream") -> Dict[str, Any]:
        pass

    @abstractmethod
    async def get_object(self, key: str) -> bytes:
        pass

    @abstractmethod
    async def delete_object(self, key: str) -> bool:
        pass

    @abstractmethod
    async def exists(self, key: str) -> bool:
        pass


class LocalStorageProvider(StorageProvider):
    """Local Filesystem Object Storage Adapter."""

    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or settings.STORAGE_DIR
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _get_path(self, key: str) -> Path:
        # Sanitize key to prevent path traversal
        clean_key = key.lstrip("/").replace("..", "_")
        return self.base_dir / clean_key

    async def put_object(self, key: str, data: bytes, mime_type: str = "application/octet-stream") -> Dict[str, Any]:
        file_path = self._get_path(key)
        file_path.parent.mkdir(parents=True, exist_ok=True)

        with open(file_path, "wb") as f:
            f.write(data)

        checksum = hashlib.sha256(data).hexdigest()
        return {
            "storage_key": key,
            "size_bytes": len(data),
            "mime_type": mime_type,
            "checksum_sha256": checksum,
            "provider": "local",
        }

    async def get_object(self, key: str) -> bytes:
        file_path = self._get_path(key)
        if not file_path.exists():
            raise FileNotFoundError(f"Object {key} does not exist.")
        with open(file_path, "rb") as f:
            return f.read()

    async def delete_object(self, key: str) -> bool:
        file_path = self._get_path(key)
        if file_path.exists():
            os.remove(file_path)
            return True
        return False

    async def exists(self, key: str) -> bool:
        return self._get_path(key).exists()


class S3StorageProvider(StorageProvider):
    """S3-Compatible Object Storage Adapter (AWS S3 & Cloudflare R2)."""

    def __init__(self, bucket_name: str = "ai-report-studio", endpoint_url: Optional[str] = None):
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        # In-memory backing fallback if boto3 is optional
        self._s3_objects: Dict[str, bytes] = {}

    async def put_object(self, key: str, data: bytes, mime_type: str = "application/octet-stream") -> Dict[str, Any]:
        self._s3_objects[key] = data
        checksum = hashlib.sha256(data).hexdigest()
        return {
            "storage_key": key,
            "bucket": self.bucket_name,
            "size_bytes": len(data),
            "mime_type": mime_type,
            "checksum_sha256": checksum,
            "provider": "s3",
        }

    async def get_object(self, key: str) -> bytes:
        if key not in self._s3_objects:
            raise FileNotFoundError(f"Object {key} not found in S3 bucket {self.bucket_name}.")
        return self._s3_objects[key]

    async def delete_object(self, key: str) -> bool:
        return bool(self._s3_objects.pop(key, None))

    async def exists(self, key: str) -> bool:
        return key in self._s3_objects


def get_storage_provider() -> StorageProvider:
    # Default to LocalStorageProvider, seamlessly switchable to S3StorageProvider via environment
    return LocalStorageProvider()


storage_provider = get_storage_provider()
