"""
Supabase storage adapter.

Implementation of file storage using Supabase Storage.
"""
from typing import Optional, List, BinaryIO
from datetime import datetime
import mimetypes
from supabase import create_client, Client
from app.adapters.storage.interface import (
    IStorageAdapter,
    StorageFile,
    UploadResult,
)
from app.config.settings import settings
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class SupabaseStorageAdapter(IStorageAdapter):
    """
    Supabase Storage implementation.

    Uses Supabase SDK to manage file storage.
    """

    def __init__(
        self,
        supabase_url: Optional[str] = None,
        supabase_key: Optional[str] = None,
    ):
        """
        Initialize Supabase storage adapter.

        Args:
            supabase_url: Supabase project URL
            supabase_key: Supabase API key (anon or service role)
        """
        self.url = supabase_url or settings.supabase_url
        self.key = supabase_key or settings.supabase_key
        self.client: Client = create_client(self.url, self.key)

    async def upload(
        self,
        bucket: str,
        key: str,
        file: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UploadResult:
        """Upload file to Supabase Storage."""
        try:
            # Get file content as bytes
            if hasattr(file, "read"):
                content = file.read()
            else:
                content = file

            # Auto-detect content type if not provided
            if not content_type:
                content_type, _ = mimetypes.guess_type(key)
                content_type = content_type or "application/octet-stream"

            # Upload to Supabase
            response = self.client.storage.from_(bucket).upload(
                path=key,
                file=content,
                file_options={
                    "content-type": content_type,
                    "upsert": "true",
                }
            )

            # Get public URL
            url = self.client.storage.from_(bucket).get_public_url(key)

            logger.info(
                "File uploaded successfully",
                extra={
                    "bucket": bucket,
                    "key": key,
                    "size": len(content),
                }
            )

            return UploadResult(
                success=True,
                file=StorageFile(
                    key=key,
                    url=url,
                    size=len(content),
                    content_type=content_type,
                    created_at=datetime.utcnow(),
                    metadata=metadata,
                ),
            )

        except Exception as e:
            logger.error(
                "Failed to upload file",
                extra={
                    "bucket": bucket,
                    "key": key,
                    "error": str(e),
                }
            )
            return UploadResult(
                success=False,
                error=str(e),
            )

    async def download(
        self,
        bucket: str,
        key: str,
    ) -> Optional[bytes]:
        """Download file from Supabase Storage."""
        try:
            response = self.client.storage.from_(bucket).download(key)
            return response
        except Exception as e:
            logger.error(
                "Failed to download file",
                extra={"bucket": bucket, "key": key, "error": str(e)}
            )
            return None

    async def delete(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """Delete file from Supabase Storage."""
        try:
            self.client.storage.from_(bucket).remove([key])
            logger.info(
                "File deleted",
                extra={"bucket": bucket, "key": key}
            )
            return True
        except Exception as e:
            logger.error(
                "Failed to delete file",
                extra={"bucket": bucket, "key": key, "error": str(e)}
            )
            return False

    async def get_url(
        self,
        bucket: str,
        key: str,
        expires_in: Optional[int] = None,
    ) -> Optional[str]:
        """Get URL for file access."""
        try:
            if expires_in:
                # Get signed URL
                response = self.client.storage.from_(bucket).create_signed_url(
                    path=key,
                    expires_in=expires_in,
                )
                return response.get("signedURL")
            else:
                # Get public URL
                return self.client.storage.from_(bucket).get_public_url(key)
        except Exception as e:
            logger.error(
                "Failed to get file URL",
                extra={"bucket": bucket, "key": key, "error": str(e)}
            )
            return None

    async def exists(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """Check if file exists in Supabase Storage."""
        try:
            # List files with the exact key as prefix
            response = self.client.storage.from_(bucket).list(path=key)
            return len(response) > 0
        except Exception:
            return False

    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> List[StorageFile]:
        """List files in Supabase Storage bucket."""
        try:
            response = self.client.storage.from_(bucket).list(
                path=prefix or "",
                options={"limit": limit}
            )

            files = []
            for item in response:
                if item.get("name"):
                    key = f"{prefix}/{item['name']}" if prefix else item["name"]
                    url = self.client.storage.from_(bucket).get_public_url(key)
                    files.append(StorageFile(
                        key=key,
                        url=url,
                        size=item.get("metadata", {}).get("size"),
                        content_type=item.get("metadata", {}).get("mimetype"),
                        created_at=item.get("created_at"),
                    ))

            return files
        except Exception as e:
            logger.error(
                "Failed to list files",
                extra={"bucket": bucket, "prefix": prefix, "error": str(e)}
            )
            return []

    async def get_signed_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """Get signed URL for direct upload."""
        try:
            response = self.client.storage.from_(bucket).create_signed_upload_url(
                path=key,
            )
            return response.get("signedURL")
        except Exception as e:
            logger.error(
                "Failed to create signed upload URL",
                extra={"bucket": bucket, "key": key, "error": str(e)}
            )
            return None


class MemoryStorageAdapter(IStorageAdapter):
    """
    In-memory storage adapter for testing.

    Stores files in memory dictionary.
    """

    def __init__(self):
        self.storage: dict = {}  # {bucket: {key: {"content": bytes, "metadata": dict}}}

    async def upload(
        self,
        bucket: str,
        key: str,
        file: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UploadResult:
        """Store file in memory."""
        if bucket not in self.storage:
            self.storage[bucket] = {}

        content = file.read() if hasattr(file, "read") else file
        content_type = content_type or "application/octet-stream"

        self.storage[bucket][key] = {
            "content": content,
            "content_type": content_type,
            "metadata": metadata or {},
            "created_at": datetime.utcnow(),
        }

        return UploadResult(
            success=True,
            file=StorageFile(
                key=key,
                url=f"memory://{bucket}/{key}",
                size=len(content),
                content_type=content_type,
                created_at=datetime.utcnow(),
                metadata=metadata,
            ),
        )

    async def download(self, bucket: str, key: str) -> Optional[bytes]:
        """Get file from memory."""
        if bucket in self.storage and key in self.storage[bucket]:
            return self.storage[bucket][key]["content"]
        return None

    async def delete(self, bucket: str, key: str) -> bool:
        """Delete file from memory."""
        if bucket in self.storage and key in self.storage[bucket]:
            del self.storage[bucket][key]
            return True
        return False

    async def get_url(
        self,
        bucket: str,
        key: str,
        expires_in: Optional[int] = None,
    ) -> Optional[str]:
        """Get memory URL."""
        if bucket in self.storage and key in self.storage[bucket]:
            return f"memory://{bucket}/{key}"
        return None

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if file exists in memory."""
        return bucket in self.storage and key in self.storage[bucket]

    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> List[StorageFile]:
        """List files in memory bucket."""
        if bucket not in self.storage:
            return []

        files = []
        for key, data in self.storage[bucket].items():
            if prefix is None or key.startswith(prefix):
                files.append(StorageFile(
                    key=key,
                    url=f"memory://{bucket}/{key}",
                    size=len(data["content"]),
                    content_type=data["content_type"],
                    created_at=data["created_at"],
                    metadata=data["metadata"],
                ))
                if len(files) >= limit:
                    break

        return files

    async def get_signed_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """Get memory upload URL."""
        return f"memory://{bucket}/{key}?upload=true"

    def clear(self):
        """Clear all stored files."""
        self.storage.clear()
