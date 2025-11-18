from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.template import Template, TemplateType
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse
from app.routes.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


@router.get("/", response_model=List[TemplateResponse])
def get_templates(
    template_type: Optional[TemplateType] = None,
    country: Optional[str] = None,
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all templates with optional filters"""
    query = db.query(Template)

    # Filter by template type
    if template_type:
        query = query.filter(Template.template_type == template_type)

    # Filter by country
    if country:
        query = query.filter(
            (Template.country == country) | (Template.country == None)
        )

    # Filter by active status
    if not include_inactive:
        query = query.filter(Template.is_active == True)

    templates = query.order_by(Template.created_at.desc()).all()
    return templates


@router.get("/{template_id}", response_model=TemplateResponse)
def get_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get a specific template by ID"""
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )
    return template


@router.post("/", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new template"""
    # Check if template with same name and type already exists
    existing = (
        db.query(Template)
        .filter(
            Template.name == template.name,
            Template.template_type == template.template_type,
        )
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Template with name '{template.name}' and type '{template.template_type}' already exists",
        )

    db_template = Template(**template.model_dump())
    db.add(db_template)
    db.commit()
    db.refresh(db_template)
    return db_template


@router.put("/{template_id}", response_model=TemplateResponse)
def update_template(
    template_id: str,
    template: TemplateUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update a template"""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Update fields
    update_data = template.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_template, field, value)

    db.commit()
    db.refresh(db_template)
    return db_template


@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a template"""
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    db.delete(db_template)
    db.commit()
    return None


@router.post("/{template_id}/duplicate", response_model=TemplateResponse)
def duplicate_template(
    template_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Duplicate an existing template"""
    original = db.query(Template).filter(Template.id == template_id).first()
    if not original:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Template not found"
        )

    # Create a copy
    duplicate = Template(
        name=f"{original.name} (Copy)",
        template_type=original.template_type,
        description=original.description,
        content=original.content,
        country=original.country,
        is_active=original.is_active,
    )

    db.add(duplicate)
    db.commit()
    db.refresh(duplicate)
    return duplicate
