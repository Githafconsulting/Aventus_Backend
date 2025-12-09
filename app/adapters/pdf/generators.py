"""
PDF Generator Wrappers.

Wraps existing PDF generators for use with the registry pattern.
These are thin wrappers that delegate to the original generators.
"""
from typing import Dict, Any, List
from app.adapters.pdf.interface import IPDFGenerator, PDFResult
from app.adapters.pdf.registry import PDFGeneratorRegistry


@PDFGeneratorRegistry.register("contract")
class ContractPDFGenerator(IPDFGenerator):
    """Wrapper for contract PDF generation."""

    document_type = "contract"
    required_fields = ["contractor_name"]

    def get_template_fields(self) -> List[str]:
        return self.required_fields

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        from app.utils.contract_pdf_generator import generate_consultant_contract_pdf
        try:
            pdf_bytes = generate_consultant_contract_pdf(data)
            return PDFResult(success=True, content=pdf_bytes, filename="contract.pdf")
        except Exception as e:
            return PDFResult(success=False, error=str(e))

    def generate_with_signature(self, data, signature, signature_position=None) -> PDFResult:
        data["signature"] = signature
        return self.generate(data)


@PDFGeneratorRegistry.register("work_order")
class WorkOrderPDFGenerator(IPDFGenerator):
    """Wrapper for work order PDF generation."""

    document_type = "work_order"
    required_fields = ["contractor_name"]

    def get_template_fields(self) -> List[str]:
        return self.required_fields

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        from app.utils.work_order_pdf_generator import generate_work_order_pdf
        try:
            pdf_bytes = generate_work_order_pdf(data)
            return PDFResult(success=True, content=pdf_bytes, filename="work_order.pdf")
        except Exception as e:
            return PDFResult(success=False, error=str(e))

    def generate_with_signature(self, data, signature, signature_position=None) -> PDFResult:
        data["signature"] = signature
        return self.generate(data)


@PDFGeneratorRegistry.register("cohf")
class COHFPDFGenerator(IPDFGenerator):
    """Wrapper for COHF PDF generation."""

    document_type = "cohf"
    required_fields = ["contractor_name"]

    def get_template_fields(self) -> List[str]:
        return self.required_fields

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        from app.utils.cohf_pdf_generator import generate_cohf_pdf
        try:
            pdf_bytes = generate_cohf_pdf(data)
            return PDFResult(success=True, content=pdf_bytes, filename="cohf.pdf")
        except Exception as e:
            return PDFResult(success=False, error=str(e))

    def generate_with_signature(self, data, signature, signature_position=None) -> PDFResult:
        data["signature"] = signature
        return self.generate(data)


@PDFGeneratorRegistry.register("quote_sheet")
class QuoteSheetPDFGenerator(IPDFGenerator):
    """Wrapper for quote sheet PDF generation."""

    document_type = "quote_sheet"
    required_fields = ["contractor_name"]

    def get_template_fields(self) -> List[str]:
        return self.required_fields

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        from app.utils.quote_sheet_pdf_generator import generate_quote_sheet_pdf
        try:
            pdf_bytes = generate_quote_sheet_pdf(data)
            return PDFResult(success=True, content=pdf_bytes, filename="quote_sheet.pdf")
        except Exception as e:
            return PDFResult(success=False, error=str(e))

    def generate_with_signature(self, data, signature, signature_position=None) -> PDFResult:
        data["signature"] = signature
        return self.generate(data)


@PDFGeneratorRegistry.register("timesheet")
class TimesheetPDFGenerator(IPDFGenerator):
    """Wrapper for timesheet PDF generation."""

    document_type = "timesheet"
    required_fields = ["contractor_name"]

    def get_template_fields(self) -> List[str]:
        return self.required_fields

    def generate(self, data: Dict[str, Any]) -> PDFResult:
        from app.utils.timesheet_pdf_generator import generate_timesheet_pdf
        try:
            pdf_bytes = generate_timesheet_pdf(data)
            return PDFResult(success=True, content=pdf_bytes, filename="timesheet.pdf")
        except Exception as e:
            return PDFResult(success=False, error=str(e))

    def generate_with_signature(self, data, signature, signature_position=None) -> PDFResult:
        data["signature"] = signature
        return self.generate(data)
