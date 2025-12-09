"""
PDF Generator Registry.

Provides dynamic registration and lookup of PDF generators.
"""
from typing import Dict, Type, List, Optional
from app.adapters.pdf.interface import IPDFGenerator


class PDFGeneratorRegistry:
    """
    Registry for PDF generators.

    Allows dynamic registration and lookup of generators by document type.

    Usage:
        # Register a generator
        PDFGeneratorRegistry.register("contract", ContractPDFGenerator)

        # Get a generator
        generator = PDFGeneratorRegistry.get("contract")
        result = generator.generate(data)
    """

    _generators: Dict[str, Type[IPDFGenerator]] = {}
    _instances: Dict[str, IPDFGenerator] = {}

    @classmethod
    def register(cls, document_type: str):
        """
        Decorator to register a generator class.

        Args:
            document_type: Document type identifier

        Usage:
            @PDFGeneratorRegistry.register("contract")
            class ContractPDFGenerator(BasePDFGenerator):
                ...
        """
        def decorator(generator_class: Type[IPDFGenerator]):
            cls._generators[document_type] = generator_class
            return generator_class
        return decorator

    @classmethod
    def register_class(
        cls,
        document_type: str,
        generator_class: Type[IPDFGenerator],
    ) -> None:
        """
        Programmatically register a generator class.

        Args:
            document_type: Document type identifier
            generator_class: Generator class to register
        """
        cls._generators[document_type] = generator_class

    @classmethod
    def get(cls, document_type: str) -> IPDFGenerator:
        """
        Get a generator instance for a document type.

        Args:
            document_type: Document type identifier

        Returns:
            IPDFGenerator instance

        Raises:
            KeyError: If document type is not registered
        """
        if document_type not in cls._generators:
            available = ", ".join(cls._generators.keys())
            raise KeyError(
                f"No generator registered for document type: '{document_type}'. "
                f"Available types: {available}"
            )

        # Return cached instance or create new one
        if document_type not in cls._instances:
            cls._instances[document_type] = cls._generators[document_type]()

        return cls._instances[document_type]

    @classmethod
    def get_or_none(cls, document_type: str) -> Optional[IPDFGenerator]:
        """Get generator or None if not found."""
        try:
            return cls.get(document_type)
        except KeyError:
            return None

    @classmethod
    def available_types(cls) -> List[str]:
        """Get list of registered document types."""
        return list(cls._generators.keys())

    @classmethod
    def is_registered(cls, document_type: str) -> bool:
        """Check if a document type is registered."""
        return document_type in cls._generators

    @classmethod
    def clear(cls) -> None:
        """Clear all registered generators (for testing)."""
        cls._generators.clear()
        cls._instances.clear()
