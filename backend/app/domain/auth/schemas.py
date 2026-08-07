import uuid
from pydantic import BaseModel, EmailStr, Field


class FirmRegisterRequest(BaseModel):
    """Payload sent by a CA Partner to register a new Accounting Firm and Admin User."""
    firm_name: str = Field(..., example="Taxon Associates Kerala")
    registration_number: str | None = Field(None, example="FRN-012345S")
    full_name: str = Field(..., example="CA Mithun Sharma")
    email: EmailStr = Field(..., example="partner@taxon.in")
    password: str = Field(..., min_length=8, example="SecurePassword123!")


class UserLoginRequest(BaseModel):
    """Payload sent from the React frontend login form."""
    email: EmailStr = Field(..., example="partner@taxon.in")
    password: str = Field(..., example="SecurePassword123!")


class TokenResponse(BaseModel):
    """The digital badge returned after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    firm_id: uuid.UUID
    user_id: uuid.UUID


class CAUserResponse(BaseModel):
    """Safe user profile response (excluding the password hash!)."""
    id: uuid.UUID
    firm_id: uuid.UUID
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


class FirmRegisterResponse(BaseModel):
    """Response returned after successfully creating a firm."""
    firm_id: uuid.UUID
    firm_name: str
    user: CAUserResponse