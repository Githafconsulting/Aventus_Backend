# Storage adapter
from app.adapters.storage.interface import (
    IStorageAdapter,
    StorageFile,
    UploadResult,
)
from app.adapters.storage.supabase_adapter import (
    SupabaseStorageAdapter,
    MemoryStorageAdapter,
)

__all__ = [
    # Interface
    "IStorageAdapter",
    "StorageFile",
    "UploadResult",
    # Implementations
    "SupabaseStorageAdapter",
    "MemoryStorageAdapter",
]
