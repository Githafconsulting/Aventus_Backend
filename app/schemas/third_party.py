from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


class ThirdPartyBase(BaseModel):
    company_name: str
    registered_address: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_reg_no: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = True


class ThirdPartyCreate(ThirdPartyBase):
    pass


class ThirdPartyUpdate(BaseModel):
    company_name: Optional[str] = None
    registered_address: Optional[str] = None
    company_vat_no: Optional[str] = None
    company_reg_no: Optional[str] = None
    contact_person_name: Optional[str] = None
    contact_person_email: Optional[EmailStr] = None
    contact_person_phone: Optional[str] = None
    bank_name: Optional[str] = None
    account_number: Optional[str] = None
    iban_number: Optional[str] = None
    swift_code: Optional[str] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class ThirdPartyResponse(ThirdPartyBase):
    id: str
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
