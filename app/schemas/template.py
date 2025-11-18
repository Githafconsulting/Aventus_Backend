from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.template import TemplateType


class TemplateBase(BaseModel):
    name: str
    template_type: TemplateType
    description: Optional[str] = None
    content: str
    country: Optional[str] = None
    is_active: Optional[bool] = True


class TemplateCreate(TemplateBase):
    pass


class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    template_type: Optional[TemplateType] = None
    description: Optional[str] = None
    content: Optional[str] = None
    country: Optional[str] = None
    is_active: Optional[bool] = None


class TemplateResponse(TemplateBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
