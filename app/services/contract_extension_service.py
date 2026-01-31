"""
Contract Extension Service.

Application service for managing contractor contract extensions.
Handles extension requests, approvals, and signature workflows.
"""
from typing import Optional, List
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal
import uuid
import secrets

from sqlalchemy.orm import Session

from app.models.contractor import Contractor, ContractorStatus
from app.models.contract_extension import ContractExtension, ExtensionStatus
from app.schemas.contract_extension import (
    RequestExtensionRequest,
    ExtensionSignatureRequest,
    ExtensionSigningPageResponse,
)
from app.telemetry.logger import get_logger

logger = get_logger(__name__)


class ContractExtensionService:
    """
    Service for managing contract extensions.

    Handles the full extension workflow including:
    - Creating extension requests
    - Approval/rejection
    - Document generation
    - Signature collection
    """

    def __init__(self, db: Session):
        """Initialize with database session."""
        self.db = db

    async def request_extension(
        self,
        contractor_id: str,
        request: RequestExtensionRequest,
        requested_by: str,
    ) -> ContractExtension:
        """
        Create a new contract extension request.

        Args:
            contractor_id: Contractor to extend
            request: Extension request details
            requested_by: User ID creating the request

        Returns:
            Created extension record

        Raises:
            ValueError: If contractor not found or invalid state
        """
        contractor = self.db.query(Contractor).filter(Contractor.id == contractor_id).first()
        if not contractor:
            raise ValueError(f"Contractor not found: {contractor_id}")

        # Check contractor is active
        if contractor.status not in [ContractorStatus.ACTIVE, ContractorStatus.EXTENSION_PENDING]:
            raise ValueError(f"Cannot extend contract for contractor in status: {contractor.status}")

        # Check for existing pending extension
        existing = self.db.query(ContractExtension).filter(
            ContractExtension.contractor_id == contractor_id,
            ContractExtension.status.notin_([ExtensionStatus.COMPLETED, ExtensionStatus.REJECTED])
        ).first()

        if existing:
            raise ValueError(f"Contractor already has pending extension: {existing.id}")

        # Parse original end date
        original_end_date_str = contractor.end_date
        try:
            original_end_date = datetime.strptime(original_end_date_str, "%Y-%m-%d").date() if original_end_date_str else date.today()
        except (ValueError, TypeError):
            original_end_date = date.today()

        # Create extension record
        extension = ContractExtension(
            id=str(uuid.uuid4()),
            contractor_id=contractor_id,
            original_end_date=original_end_date,
            new_end_date=request.new_end_date,
            extension_months=request.extension_months,
            new_monthly_rate=request.new_monthly_rate,
            new_day_rate=request.new_day_rate,
            rate_change_reason=request.rate_change_reason,
            status=ExtensionStatus.PENDING_APPROVAL,
            requested_by=requested_by,
            notes=request.notes,
        )

        self.db.add(extension)

        # Update contractor status
        contractor.status = ContractorStatus.EXTENSION_PENDING
        contractor.current_extension_id = extension.id

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Extension requested",
            extra={
                "contractor_id": contractor_id,
                "extension_id": extension.id,
                "new_end_date": str(request.new_end_date),
                "requested_by": requested_by,
            }
        )

        return extension

    async def approve_extension(
        self,
        extension_id: str,
        approved_by: str,
        notes: Optional[str] = None,
    ) -> ContractExtension:
        """
        Approve an extension request.

        Args:
            extension_id: Extension record ID
            approved_by: User ID approving
            notes: Optional approval notes

        Returns:
            Updated extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status != ExtensionStatus.PENDING_APPROVAL:
            raise ValueError(f"Cannot approve extension in status: {extension.status}")

        extension.status = ExtensionStatus.APPROVED
        extension.approved_by = approved_by
        extension.approved_date = datetime.now(timezone.utc)
        if notes:
            extension.notes = (extension.notes or "") + f"\nApproval notes: {notes}"

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Extension approved",
            extra={
                "extension_id": extension_id,
                "approved_by": approved_by,
            }
        )

        return extension

    async def reject_extension(
        self,
        extension_id: str,
        rejected_by: str,
        reason: str,
    ) -> ContractExtension:
        """
        Reject an extension request.

        Args:
            extension_id: Extension record ID
            rejected_by: User ID rejecting
            reason: Rejection reason

        Returns:
            Updated extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status not in [ExtensionStatus.PENDING_APPROVAL, ExtensionStatus.APPROVED]:
            raise ValueError(f"Cannot reject extension in status: {extension.status}")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == extension.contractor_id
        ).first()

        extension.status = ExtensionStatus.REJECTED
        extension.rejected_by = rejected_by
        extension.rejected_date = datetime.now(timezone.utc)
        extension.rejection_reason = reason

        # Restore contractor to active
        if contractor:
            contractor.status = ContractorStatus.ACTIVE
            contractor.current_extension_id = None

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Extension rejected",
            extra={
                "extension_id": extension_id,
                "rejected_by": rejected_by,
                "reason": reason,
            }
        )

        return extension

    async def generate_extension_document(
        self,
        extension_id: str,
    ) -> str:
        """
        Generate extension agreement document.

        Args:
            extension_id: Extension record ID

        Returns:
            URL to generated document
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status not in [ExtensionStatus.APPROVED, ExtensionStatus.PENDING_SIGNATURE]:
            raise ValueError(f"Cannot generate document in status: {extension.status}")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == extension.contractor_id
        ).first()

        if not contractor:
            raise ValueError(f"Contractor not found: {extension.contractor_id}")

        # Document generation would go here
        # For now, we'll set a placeholder URL
        # In production, use PDF generators and upload to storage

        document_url = None  # Would be actual URL from storage

        extension.extension_document_url = document_url
        self.db.commit()

        logger.info(
            "Extension document generated",
            extra={
                "extension_id": extension_id,
                "contractor_id": contractor.id,
            }
        )

        return document_url

    async def send_for_signature(
        self,
        extension_id: str,
    ) -> ContractExtension:
        """
        Send extension for contractor signature.

        Generates signature token and updates status.

        Args:
            extension_id: Extension record ID

        Returns:
            Updated extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status != ExtensionStatus.APPROVED:
            raise ValueError(f"Cannot send for signature in status: {extension.status}")

        # Generate signature token (7 days expiry)
        extension.signature_token = secrets.token_urlsafe(32)
        extension.token_expiry = datetime.now(timezone.utc) + timedelta(days=7)
        extension.status = ExtensionStatus.PENDING_SIGNATURE

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Extension sent for signature",
            extra={
                "extension_id": extension_id,
                "token_expiry": str(extension.token_expiry),
            }
        )

        return extension

    async def get_signing_page_data(
        self,
        token: str,
    ) -> ExtensionSigningPageResponse:
        """
        Get data for public signing page.

        Args:
            token: Signature token

        Returns:
            Signing page data
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.signature_token == token
        ).first()

        if not extension:
            raise ValueError("Invalid or expired token")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == extension.contractor_id
        ).first()

        if not contractor:
            raise ValueError("Contractor not found")

        # Check token expiry
        token_expired = False
        if extension.token_expiry and extension.token_expiry < datetime.now(timezone.utc):
            token_expired = True

        return ExtensionSigningPageResponse(
            extension_id=extension.id,
            contractor_name=f"{contractor.first_name} {contractor.surname}",
            client_name=contractor.client_name,
            original_end_date=extension.original_end_date,
            new_end_date=extension.new_end_date,
            extension_months=extension.extension_months,
            new_monthly_rate=extension.new_monthly_rate,
            new_day_rate=extension.new_day_rate,
            rate_change_reason=extension.rate_change_reason,
            extension_document_url=extension.extension_document_url,
            already_signed=extension.contractor_signed_date is not None,
            token_expired=token_expired,
        )

    async def process_contractor_signature(
        self,
        token: str,
        signature: ExtensionSignatureRequest,
    ) -> ContractExtension:
        """
        Process contractor signature on extension.

        Args:
            token: Signature token
            signature: Signature data

        Returns:
            Updated extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.signature_token == token
        ).first()

        if not extension:
            raise ValueError("Invalid or expired token")

        if extension.token_expiry and extension.token_expiry < datetime.now(timezone.utc):
            raise ValueError("Token has expired")

        if extension.contractor_signed_date:
            raise ValueError("Extension already signed")

        if extension.status != ExtensionStatus.PENDING_SIGNATURE:
            raise ValueError(f"Cannot sign extension in status: {extension.status}")

        extension.contractor_signature_type = signature.signature_type
        extension.contractor_signature_data = signature.signature_data
        extension.contractor_signed_date = datetime.now(timezone.utc)
        extension.status = ExtensionStatus.SIGNED

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Contractor signed extension",
            extra={
                "extension_id": extension.id,
                "contractor_id": extension.contractor_id,
            }
        )

        return extension

    async def process_aventus_signature(
        self,
        extension_id: str,
        signed_by: str,
        signature_type: str,
        signature_data: str,
    ) -> ContractExtension:
        """
        Process Aventus counter-signature on extension.

        Args:
            extension_id: Extension record ID
            signed_by: User ID signing
            signature_type: "typed" or "drawn"
            signature_data: Signature data

        Returns:
            Updated extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status != ExtensionStatus.SIGNED:
            raise ValueError(f"Cannot counter-sign extension in status: {extension.status}")

        if not extension.contractor_signed_date:
            raise ValueError("Contractor must sign first")

        extension.aventus_signature_type = signature_type
        extension.aventus_signature_data = signature_data
        extension.aventus_signed_by = signed_by
        extension.aventus_signed_date = datetime.now(timezone.utc)

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Aventus signed extension",
            extra={
                "extension_id": extension_id,
                "signed_by": signed_by,
            }
        )

        return extension

    async def complete_extension(
        self,
        extension_id: str,
    ) -> ContractExtension:
        """
        Complete extension and update contractor.

        Args:
            extension_id: Extension record ID

        Returns:
            Completed extension record
        """
        extension = self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

        if not extension:
            raise ValueError(f"Extension not found: {extension_id}")

        if extension.status != ExtensionStatus.SIGNED:
            raise ValueError(f"Cannot complete extension in status: {extension.status}")

        if not extension.aventus_signed_date:
            raise ValueError("Aventus must counter-sign before completing")

        contractor = self.db.query(Contractor).filter(
            Contractor.id == extension.contractor_id
        ).first()

        if not contractor:
            raise ValueError(f"Contractor not found: {extension.contractor_id}")

        # Update extension status
        extension.status = ExtensionStatus.COMPLETED

        # Update contractor
        contractor.end_date = extension.new_end_date.strftime("%Y-%m-%d")
        contractor.status = ContractorStatus.ACTIVE
        contractor.current_extension_id = None

        # Update rates if changed
        if extension.new_monthly_rate:
            contractor.gross_salary = str(extension.new_monthly_rate)
            contractor.charge_rate_month = str(extension.new_monthly_rate)
        if extension.new_day_rate:
            contractor.day_rate = str(extension.new_day_rate)
            contractor.charge_rate_day = str(extension.new_day_rate)

        # Increment extension count
        current_count = int(contractor.total_extensions or "0")
        contractor.total_extensions = str(current_count + 1)

        self.db.commit()
        self.db.refresh(extension)

        logger.info(
            "Extension completed",
            extra={
                "extension_id": extension_id,
                "contractor_id": contractor.id,
                "new_end_date": str(extension.new_end_date),
            }
        )

        return extension

    async def get_extension_by_id(
        self,
        extension_id: str,
    ) -> Optional[ContractExtension]:
        """Get extension record by ID."""
        return self.db.query(ContractExtension).filter(
            ContractExtension.id == extension_id
        ).first()

    async def get_extensions_for_contractor(
        self,
        contractor_id: str,
    ) -> List[ContractExtension]:
        """Get all extensions for a contractor."""
        return self.db.query(ContractExtension).filter(
            ContractExtension.contractor_id == contractor_id
        ).order_by(ContractExtension.requested_date.desc()).all()

    async def list_extensions(
        self,
        status: Optional[ExtensionStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> List[ContractExtension]:
        """List extension records with optional filtering."""
        query = self.db.query(ContractExtension)

        if status:
            query = query.filter(ContractExtension.status == status)

        return query.order_by(ContractExtension.requested_date.desc()).offset(skip).limit(limit).all()
