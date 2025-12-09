"""
Storage adapter interface.

Defines the contract for file storage implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, List, BinaryIO
from dataclasses import dataclass
from datetime import datetime


@dataclass
class StorageFile:
    """
    Represents a file in storage.

    Attributes:
        key: Unique file identifier/path
        url: Public URL to access the file
        size: File size in bytes
        content_type: MIME type
        created_at: Upload timestamp
        metadata: Optional custom metadata
    """
    key: str
    url: str
    size: Optional[int] = None
    content_type: Optional[str] = None
    created_at: Optional[datetime] = None
    metadata: Optional[dict] = None


@dataclass
class UploadResult:
    """
    Result of an upload operation.

    Attributes:
        success: Whether upload succeeded
        file: StorageFile if successful
        error: Error message if failed
    """
    success: bool
    file: Optional[StorageFile] = None
    error: Optional[str] = None


class IStorageAdapter(ABC):
    """
    Abstract interface for file storage.

    Implementations can use different providers (Supabase, S3, local, etc.)
    while maintaining the same interface.

    Usage:
        storage = SupabaseStorageAdapter()
        result = await storage.upload(
            bucket="documents",
            key="contractor/123/passport.pdf",
            file=file_content,
        )
    """

    @abstractmethod
    async def upload(
        self,
        bucket: str,
        key: str,
        file: bytes | BinaryIO,
        content_type: Optional[str] = None,
        metadata: Optional[dict] = None,
    ) -> UploadResult:
        """
        Upload a file to storage.

        Args:
            bucket: Storage bucket name
            key: File key/path in the bucket
            file: File content (bytes or file-like object)
            content_type: MIME type (optional, auto-detected if not provided)
            metadata: Custom metadata (optional)

        Returns:
            UploadResult with success status and file info
        """
        pass

    @abstractmethod
    async def download(
        self,
        bucket: str,
        key: str,
    ) -> Optional[bytes]:
        """
        Download a file from storage.

        Args:
            bucket: Storage bucket name
            key: File key/path

        Returns:
            File content as bytes, or None if not found
        """
        pass

    @abstractmethod
    async def delete(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Delete a file from storage.

        Args:
            bucket: Storage bucket name
            key: File key/path

        Returns:
            True if deleted, False otherwise
        """
        pass

    @abstractmethod
    async def get_url(
        self,
        bucket: str,
        key: str,
        expires_in: Optional[int] = None,
    ) -> Optional[str]:
        """
        Get URL to access a file.

        Args:
            bucket: Storage bucket name
            key: File key/path
            expires_in: URL expiry in seconds (optional, for signed URLs)

        Returns:
            URL string or None if file not found
        """
        pass

    @abstractmethod
    async def exists(
        self,
        bucket: str,
        key: str,
    ) -> bool:
        """
        Check if a file exists.

        Args:
            bucket: Storage bucket name
            key: File key/path

        Returns:
            True if file exists, False otherwise
        """
        pass

    @abstractmethod
    async def list_files(
        self,
        bucket: str,
        prefix: Optional[str] = None,
        limit: int = 100,
    ) -> List[StorageFile]:
        """
        List files in a bucket.

        Args:
            bucket: Storage bucket name
            prefix: Filter by key prefix (optional)
            limit: Maximum files to return

        Returns:
            List of StorageFile objects
        """
        pass

    @abstractmethod
    async def get_signed_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in: int = 3600,
        content_type: Optional[str] = None,
    ) -> Optional[str]:
        """
        Get a signed URL for direct upload.

        Args:
            bucket: Storage bucket name
            key: File key/path
            expires_in: URL expiry in seconds
            content_type: Expected content type

        Returns:
            Signed upload URL or None
        """
        pass
