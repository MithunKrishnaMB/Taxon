import uuid
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.auth.models import CAUser, Tenant

router = APIRouter()

# --- Schemas ---
class TenantCreate(BaseModel):
    gstin: str = Field(..., description="15-character Indian GSTIN")
    legal_name: str = Field(..., description="Client Company Name")

class TenantResponse(BaseModel):
    id: uuid.UUID
    firm_id: uuid.UUID
    gstin: str
    legal_name: str

    class Config:
        from_attributes = True

# --- Endpoints ---
@router.post("", response_model=TenantResponse, status_code=status.HTTP_201_CREATED)
async def create_tenant(
    payload: TenantCreate,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Create a new Client Workspace for the current CA Firm."""
    # Ensure GSTIN is unique globally (or at least per firm)
    query = select(Tenant).where(Tenant.gstin == payload.gstin)
    result = await session.execute(query)
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="A client with this GSTIN already exists.")

    new_tenant = Tenant(
        id=uuid.uuid4(),
        firm_id=current_user.firm_id,
        gstin=payload.gstin.upper(),
        legal_name=payload.legal_name,
    )
    session.add(new_tenant)
    await session.commit()
    await session.refresh(new_tenant)
    
    return new_tenant

@router.get("", response_model=list[TenantResponse])
async def get_tenants(
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """List all Client Workspaces belonging to the current CA Firm."""
    query = select(Tenant).where(Tenant.firm_id == current_user.firm_id)
    result = await session.execute(query)
    return list(result.scalars().all())