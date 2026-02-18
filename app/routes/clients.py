from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.client import Client, ClientDocument, ClientProject
from app.models.contractor import Contractor
from app.models.invoice import Invoice
from app.models.proposal import Proposal
from app.schemas.client import ClientCreate, ClientUpdate, ClientResponse
from app.models.user import User, UserRole
from app.utils.auth import get_current_active_user, require_role
from app.utils.storage import storage
from datetime import datetime
import uuid

router = APIRouter(prefix="/api/v1/clients", tags=["clients"])


@router.post("/", response_model=ClientResponse, status_code=status.HTTP_201_CREATED)
async def create_client(
    client_data: ClientCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Create a new client company (Consultant/Admin/Superadmin only)
    """
    # Check if company name already exists
    existing = db.query(Client).filter(Client.company_name == client_data.company_name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A client company with this name already exists"
        )

    data = client_data.model_dump()
    projects_data = data.pop("projects", []) or []
    client = Client(**data)
    db.add(client)
    db.flush()

    for p in projects_data:
        proj = ClientProject(
            client_id=client.id,
            name=p.get("name", ""),
            description=p.get("description"),
            status=p.get("status", "Planning"),
            third_party_id=p.get("third_party_id"),
            third_party_name=p.get("third_party_name"),
        )
        db.add(proj)

    db.commit()
    db.refresh(client)

    return client


@router.get("/", response_model=List[ClientResponse])
async def get_clients(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get all client companies
    """
    query = db.query(Client)

    if not include_inactive:
        query = query.filter(Client.is_active == True)

    clients = query.order_by(Client.company_name).all()
    return clients


@router.get("/{client_id}", response_model=ClientResponse)
async def get_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get a specific client company by ID
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client company not found"
        )

    return client


@router.put("/{client_id}", response_model=ClientResponse)
async def update_client(
    client_id: str,
    client_data: ClientUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Update a client company (Consultant/Admin/Superadmin only)
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client company not found"
        )

    # Check if updating company name to an existing one
    if client_data.company_name and client_data.company_name != client.company_name:
        existing = db.query(Client).filter(
            Client.company_name == client_data.company_name,
            Client.id != client_id
        ).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A client company with this name already exists"
            )

    # Update fields
    update_data = client_data.model_dump(exclude_unset=True)
    projects_data = update_data.pop("projects", None)
    for field, value in update_data.items():
        setattr(client, field, value)

    # Replace projects if provided
    if projects_data is not None:
        for p in list(client.client_projects):
            db.delete(p)
        db.flush()
        for p in projects_data:
            proj = ClientProject(
                client_id=client.id,
                name=p.get("name", ""),
                description=p.get("description"),
                status=p.get("status", "Planning"),
                third_party_id=p.get("third_party_id"),
                third_party_name=p.get("third_party_name"),
            )
            db.add(proj)

    db.commit()
    db.refresh(client)

    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Delete a client company (Admin/Superadmin only)
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client company not found"
        )

    # Check for linked records that prevent deletion
    linked = []

    contractor_count = db.query(Contractor).filter(Contractor.client_id == client_id).count()
    if contractor_count:
        linked.append(f"{contractor_count} contractor(s)")

    proposal_count = db.query(Proposal).filter(Proposal.client_id == client_id).count()
    if proposal_count:
        linked.append(f"{proposal_count} proposal(s)")

    invoice_count = db.query(Invoice).filter(Invoice.client_id == client_id).count()
    if invoice_count:
        linked.append(f"{invoice_count} invoice(s)")

    if linked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete '{client.company_name}'. It is linked to {', '.join(linked)}. Remove or reassign these records first."
        )

    db.delete(client)
    db.commit()

    return None


@router.post("/{client_id}/upload-document")
async def upload_client_document(
    client_id: str,
    file: UploadFile = File(...),
    document_type: str = Form(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Upload a document for a client company (Consultant/Admin/Superadmin only)
    """
    client = db.query(Client).filter(Client.id == client_id).first()

    if not client:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Client company not found"
        )

    # Upload file to storage
    try:
        # Generate unique filename
        file_ext = file.filename.split('.')[-1] if '.' in file.filename else ''
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        unique_id = str(uuid.uuid4())[:8]
        filename = f"clients/{client_id}/{document_type}_{timestamp}_{unique_id}.{file_ext}"

        # Read file content
        content = await file.read()

        # Upload to Supabase Storage
        response = storage.client.storage.from_(storage.bucket).upload(
            filename,
            content,
            file_options={"content-type": file.content_type}
        )

        # Get public URL
        file_url = storage.client.storage.from_(storage.bucket).get_public_url(filename)

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload document: {str(e)}"
        )

    # Add document to child table
    doc = ClientDocument(
        client_id=client.id,
        document_type=document_type,
        filename=file.filename,
        url=file_url,
        uploaded_at=datetime.utcnow(),
    )
    db.add(doc)
    db.commit()

    return {"message": "Document uploaded successfully", "url": file_url}


@router.delete("/{client_id}/documents/{document_index}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client_document(
    client_id: str,
    document_index: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role([UserRole.CONSULTANT, UserRole.ADMIN, UserRole.SUPERADMIN]))
):
    """
    Delete a document from a client company (Consultant/Admin/Superadmin only)
    """
    docs = (
        db.query(ClientDocument)
        .filter(ClientDocument.client_id == client_id)
        .order_by(ClientDocument.id)
        .all()
    )

    if document_index >= len(docs):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Document not found"
        )

    db.delete(docs[document_index])
    db.commit()

    return None
