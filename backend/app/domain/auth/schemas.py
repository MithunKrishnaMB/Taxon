import uuid
from pydantic import BaseModel, EmailStr, Field
from app.domain.auth.models import UserRole


class FirmRegisterRequest(BaseModel):
    """Payload sent by a Founding Partner to register a new Firm (Gets OWNER role)."""
    firm_name: str = Field(..., example="Kerala Tax Partners")
    registration_number: str | None = Field(None, example="FRN-202")
    full_name: str = Field(..., example="CA Priya")
    email: EmailStr = Field(..., example="priya@keralatax.in")
    password: str = Field(..., min_length=8)


class UserRegisterRequest(BaseModel):
    """Payload sent by a new team member joining an existing firm (Gets CLERK role)."""
    full_name: str = Field(..., example="CA Rahul")
    email: EmailStr = Field(..., example="rahul@keralatax.in")
    password: str = Field(..., min_length=8)
    firm_id: uuid.UUID = Field(..., description="The unique ID of the firm they are joining")


class UserLoginRequest(BaseModel):
    email: EmailStr = Field(...)
    password: str = Field(...)


class TokenResponse(BaseModel):
    """The digital badge returned after successful authentication."""
    access_token: str
    token_type: str = "bearer"
    firm_id: uuid.UUID
    user_id: uuid.UUID
    role: UserRole  # <-- NEW: The React frontend needs to know the role to hide/show UI buttons!


class CAUserResponse(BaseModel):
    """Safe user profile response (excluding the password hash)."""
    id: uuid.UUID
    firm_id: uuid.UUID
    email: EmailStr
    full_name: str
    role: UserRole  # <-- NEW

    class Config:
        from_attributes = True


class FirmRegisterResponse(BaseModel):
    firm_id: uuid.UUID
    firm_name: str
    user: CAUserResponse


class RoleUpdateRequest(BaseModel):
    """Payload used by OWNER or ADMIN to change a user's role."""
    new_role: UserRole = Field(..., description="The role to assign to the user")