# PDF generation adapter
from app.adapters.pdf.interface import IPDFGenerator, PDFResult
from app.adapters.pdf.base import BasePDFGenerator
from app.adapters.pdf.registry import PDFGeneratorRegistry

# Import generators to auto-register them
from app.adapters.pdf import generators  # noqa: F401

__all__ = [
    # Interface
    "IPDFGenerator",
    "PDFResult",
    # Base class
    "BasePDFGenerator",
    # Registry
    "PDFGeneratorRegistry",
]
