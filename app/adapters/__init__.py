# Adapter Layer - External service integrations
from app.adapters.email import (
    IEmailSender,
    EmailMessage,
    EmailResult,
    ResendEmailSender,
    MockEmailSender,
    EmailTemplateEngine,
    email_template_engine,
)
from app.adapters.storage import (
    IStorageAdapter,
    StorageFile,
    UploadResult,
    SupabaseStorageAdapter,
    MemoryStorageAdapter,
)
from app.adapters.pdf import (
    IPDFGenerator,
    PDFResult,
    BasePDFGenerator,
    PDFGeneratorRegistry,
)

__all__ = [
    # Email
    "IEmailSender",
    "EmailMessage",
    "EmailResult",
    "ResendEmailSender",
    "MockEmailSender",
    "EmailTemplateEngine",
    "email_template_engine",
    # Storage
    "IStorageAdapter",
    "StorageFile",
    "UploadResult",
    "SupabaseStorageAdapter",
    "MemoryStorageAdapter",
    # PDF
    "IPDFGenerator",
    "PDFResult",
    "BasePDFGenerator",
    "PDFGeneratorRegistry",
]
