"""
Unit tests for storage adapters.
"""
import pytest
from unittest.mock import MagicMock, AsyncMock
from datetime import datetime
from app.adapters.storage.interface import StorageFile, UploadResult, IStorageAdapter


class InMemoryStorageAdapter(IStorageAdapter):
    """In-memory storage adapter for testing."""

    def __init__(self):
        self._storage: dict[str, dict[str, bytes]] = {}
        self._metadata: dict[str, dict[str, dict]] = {}

    async def upload(
        self,
        bucket: str,
        key: str,
        file,
        content_type=None,
        metadata=None,
    ) -> UploadResult:
        """Upload file to in-memory storage."""
        if bucket not in self._storage:
            self._storage[bucket] = {}
            self._metadata[bucket] = {}

        content = file.read() if hasattr(file, "read") else file
        self._storage[bucket][key] = content
        self._metadata[bucket][key] = {
            "content_type": content_type,
            "metadata": metadata,
            "size": len(content),
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

    async def download(self, bucket: str, key: str):
        """Download file from in-memory storage."""
        if bucket in self._storage and key in self._storage[bucket]:
            return self._storage[bucket][key]
        return None

    async def delete(self, bucket: str, key: str) -> bool:
        """Delete file from in-memory storage."""
        if bucket in self._storage and key in self._storage[bucket]:
            del self._storage[bucket][key]
            del self._metadata[bucket][key]
            return True
        return False

    async def get_url(self, bucket: str, key: str, expires_in=None):
        """Get URL for file."""
        if bucket in self._storage and key in self._storage[bucket]:
            return f"memory://{bucket}/{key}"
        return None

    async def exists(self, bucket: str, key: str) -> bool:
        """Check if file exists."""
        return bucket in self._storage and key in self._storage[bucket]

    async def list_files(self, bucket: str, prefix=None, limit=100):
        """List files in bucket."""
        if bucket not in self._storage:
            return []

        files = []
        for key, content in self._storage[bucket].items():
            if prefix is None or key.startswith(prefix):
                meta = self._metadata[bucket].get(key, {})
                files.append(StorageFile(
                    key=key,
                    url=f"memory://{bucket}/{key}",
                    size=len(content),
                    content_type=meta.get("content_type"),
                    created_at=meta.get("created_at"),
                    metadata=meta.get("metadata"),
                ))
                if len(files) >= limit:
                    break
        return files

    async def get_signed_upload_url(
        self,
        bucket: str,
        key: str,
        expires_in=3600,
        content_type=None,
    ):
        """Get signed upload URL."""
        return f"memory://{bucket}/{key}?signed=true&expires={expires_in}"


class TestInMemoryStorageAdapter:
    """Tests for InMemoryStorageAdapter."""

    @pytest.fixture
    def storage(self):
        return InMemoryStorageAdapter()

    @pytest.mark.asyncio
    async def test_upload_file(self, storage):
        """Test uploading a file."""
        result = await storage.upload(
            bucket="documents",
            key="test.txt",
            file=b"test content",
        )

        assert result.success is True
        assert result.file is not None
        assert "test.txt" in result.file.key

    @pytest.mark.asyncio
    async def test_upload_with_content_type(self, storage):
        """Test uploading with content type."""
        result = await storage.upload(
            bucket="pdfs",
            key="document.pdf",
            file=b"PDF content",
            content_type="application/pdf",
        )

        assert result.success is True
        assert result.file.content_type == "application/pdf"

    @pytest.mark.asyncio
    async def test_download_file(self, storage):
        """Test downloading a file."""
        # First upload
        await storage.upload(
            bucket="documents",
            key="test.txt",
            file=b"test content",
        )

        # Then download
        content = await storage.download("documents", "test.txt")

        assert content == b"test content"

    @pytest.mark.asyncio
    async def test_download_nonexistent_returns_none(self, storage):
        """Test downloading non-existent file returns None."""
        content = await storage.download("nonexistent", "file.txt")

        assert content is None

    @pytest.mark.asyncio
    async def test_delete_file(self, storage):
        """Test deleting a file."""
        # First upload
        await storage.upload(
            bucket="documents",
            key="test.txt",
            file=b"test content",
        )

        # Then delete
        result = await storage.delete("documents", "test.txt")

        assert result is True

        # Verify deleted
        content = await storage.download("documents", "test.txt")
        assert content is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, storage):
        """Test deleting non-existent file returns False."""
        result = await storage.delete("nonexistent", "file.txt")

        assert result is False

    @pytest.mark.asyncio
    async def test_exists(self, storage):
        """Test checking if file exists."""
        await storage.upload(
            bucket="documents",
            key="test.txt",
            file=b"test content",
        )

        assert await storage.exists("documents", "test.txt") is True
        assert await storage.exists("nonexistent", "file.txt") is False

    @pytest.mark.asyncio
    async def test_get_url(self, storage):
        """Test getting file URL."""
        await storage.upload(
            bucket="documents",
            key="test.txt",
            file=b"test content",
        )

        url = await storage.get_url("documents", "test.txt")

        assert url is not None
        assert "test.txt" in url

    @pytest.mark.asyncio
    async def test_list_files(self, storage):
        """Test listing files in bucket."""
        await storage.upload("folder", "file1.txt", b"content1")
        await storage.upload("folder", "file2.txt", b"content2")
        await storage.upload("other", "other.txt", b"content3")

        files = await storage.list_files("folder")

        assert len(files) == 2
        assert all(isinstance(f, StorageFile) for f in files)

    @pytest.mark.asyncio
    async def test_list_files_empty_bucket(self, storage):
        """Test listing files in empty bucket."""
        files = await storage.list_files("empty")

        assert files == []

    @pytest.mark.asyncio
    async def test_get_signed_upload_url(self, storage):
        """Test getting signed upload URL."""
        url = await storage.get_signed_upload_url(
            bucket="documents",
            key="upload.pdf",
            expires_in=3600,
        )

        assert url is not None
        assert "signed=true" in url


class TestStorageFile:
    """Tests for StorageFile dataclass."""

    def test_create_storage_file(self):
        """Test creating StorageFile."""
        file = StorageFile(
            key="documents/document.pdf",
            url="https://storage.example.com/document.pdf",
            size=1024,
            content_type="application/pdf",
        )

        assert file.key == "documents/document.pdf"
        assert file.size == 1024

    def test_storage_file_optional_fields(self):
        """Test StorageFile with optional fields."""
        file = StorageFile(
            key="documents/document.pdf",
            url="https://storage.example.com/document.pdf",
        )

        assert file.size is None
        assert file.content_type is None


class TestUploadResult:
    """Tests for UploadResult dataclass."""

    def test_success_result(self):
        """Test creating success upload result."""
        result = UploadResult(
            success=True,
            file=StorageFile(
                key="documents/file.pdf",
                url="https://storage.example.com/file.pdf",
            ),
        )

        assert result.success is True
        assert result.file is not None
        assert result.error is None

    def test_failure_result(self):
        """Test creating failure upload result."""
        result = UploadResult(
            success=False,
            error="Upload failed: connection timeout",
        )

        assert result.success is False
        assert result.error is not None
