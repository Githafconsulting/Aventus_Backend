"""
PDF generator interface.

Defines the contract for PDF generation implementations.
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, BinaryIO
from dataclasses import dataclass
from io import BytesIO


@dataclass
class PDFResult:
    """
    Result of a PDF generation operation.

    Attributes:
        success: Whether generation succeeded
        content: PDF content as bytes
        filename: Suggested filename
        error: Error message if failed
    """
    success: bool
    content: Optional[bytes] = None
    filename: Optional[str] = None
    error: Optional[str] = None

    def to_bytesio(self) -> Optional[BytesIO]:
        """Convert content to BytesIO for streaming."""
        if self.content:
            buffer = BytesIO(self.content)
            buffer.seek(0)
            return buffer
        return None


class IPDFGenerator(ABC):
    """
    Abstract interface for PDF generation.

    Each document type (contract, COHF, work order, etc.) implements
    this interface with its specific layout and content.

    Usage:
        generator = ContractPDFGenerator()
        result = generator.generate({"contractor_name": "John", ...})
    """

    @property
    @abstractmethod
    def document_type(self) -> str:
        """
        Return the document type identifier.

        Returns:
            Document type string (e.g., "contract", "cohf", "work_order")
        """
        pass

    @abstractmethod
    def generate(self, data: Dict[str, Any]) -> PDFResult:
        """
        Generate a PDF document.

        Args:
            data: Document data dictionary

        Returns:
            PDFResult with content or error
        """
        pass

    @abstractmethod
    def generate_with_signature(
        self,
        data: Dict[str, Any],
        signature: bytes,
        signature_position: Optional[Dict[str, int]] = None,
    ) -> PDFResult:
        """
        Generate a PDF with an embedded signature.

        Args:
            data: Document data dictionary
            signature: Signature image as bytes
            signature_position: Position dict with x, y, width, height

        Returns:
            PDFResult with signed document
        """
        pass

    @abstractmethod
    def get_template_fields(self) -> list:
        """
        Get list of required template fields.

        Returns:
            List of field names required for this document
        """
        pass

    def validate_data(self, data: Dict[str, Any]) -> list:
        """
        Validate that all required fields are present.

        Args:
            data: Data dictionary to validate

        Returns:
            List of missing field names (empty if valid)
        """
        required = self.get_template_fields()
        missing = [field for field in required if field not in data or data[field] is None]
        return missing
