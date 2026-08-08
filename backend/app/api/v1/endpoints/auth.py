import uuid
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_ca_user,
    get_password_hash,
    verify_password,
)
from app.domain.auth.models import CAFirm, CAUser, UserRole
from app.domain.auth.repositories import CAFirmRepository, CAUserRepository
from app.domain.auth.schemas import (
    CAUserResponse,
    FirmRegisterRequest,
    FirmRegisterResponse,
    RoleUpdateRequest,
    TokenResponse,
    UserRegisterRequest,
)

router = APIRouter()


@router.post(
    "/register-firm",
    response_model=FirmRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_ca_firm(
    payload: FirmRegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    """Register a new CA Firm. The creator becomes the sole OWNER."""
    firm_repo = CAFirmRepository(session)
    user_repo = CAUserRepository(session)

    if await firm_repo.get_by_name(payload.firm_name):
        raise HTTPException(status_code=400, detail="Firm name already exists.")
    if await user_repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email is already registered.")

    firm = await firm_repo.create({
        "name": payload.firm_name,
        "registration_number": payload.registration_number,
    })

    hashed_pwd = get_password_hash(payload.password)
    user = await user_repo.create({
        "firm_id": firm.id,
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hashed_pwd,
        "role": UserRole.OWNER,  # Explicitly assign top-tier clearance
    })

    return FirmRegisterResponse(
        firm_id=firm.id,
        firm_name=firm.name,
        user=user,
    )


@router.post(
    "/register-user",
    response_model=CAUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_team_member(
    payload: UserRegisterRequest,
    session: AsyncSession = Depends(get_db),
):
    """Register a new user into an existing firm. Defaults to CLERK."""
    user_repo = CAUserRepository(session)
    
    # 1. Verify firm exists
    firm = await session.get(CAFirm, payload.firm_id)
    if not firm:
        raise HTTPException(status_code=404, detail="Invalid Firm ID.")
        
    # 2. Verify email is unique
    if await user_repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="Email is already registered.")

    hashed_pwd = get_password_hash(payload.password)
    user = await user_repo.create({
        "firm_id": firm.id,
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hashed_pwd,
        "role": UserRole.CLERK,  # Default role for new signups
    })

    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """Authenticate and receive a JWT badge stamped with the user's role."""
    user_repo = CAUserRepository(session)
    user = await user_repo.get_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Embed the role in the JWT token
    access_token = create_access_token(
        user_id=user.id,
        firm_id=user.firm_id,
        email=user.email,
        role=user.role.value,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        firm_id=user.firm_id,
        user_id=user.id,
        role=user.role,
    )


@router.get("/me", response_model=CAUserResponse)
async def get_current_user_profile(
    current_user: CAUser = Depends(get_current_ca_user),
):
    return current_user


@router.put("/users/{target_user_id}/role", response_model=CAUserResponse)
async def update_user_role(
    target_user_id: uuid.UUID,
    payload: RoleUpdateRequest,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Promote or demote a team member based on strict hierarchy rules."""
    target_user = await session.get(CAUser, target_user_id)
    if not target_user or target_user.firm_id != current_user.firm_id:
        raise HTTPException(status_code=404, detail="User not found in your firm.")

    # Rule 1: The original OWNER cannot have their role changed
    if target_user.role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot modify the firm owner's role.")
        
    # Rule 2: There can be only one OWNER
    if payload.new_role == UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Cannot assign the OWNER role. Limit 1 per firm.")

    # Rule 3: Enforce specific actor permissions
    if current_user.role == UserRole.OWNER:
        pass # Owner can do anything to anyone below them
    elif current_user.role == UserRole.ADMIN:
        if target_user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=403, 
                detail="Admins cannot change the role of another Admin."
            )
    else:
        raise HTTPException(status_code=403, detail="Only Owners and Admins can manage roles.")

    # Apply the change
    target_user.role = payload.new_role
    await session.commit()
    await session.refresh(target_user)
    
    return target_user


@router.delete("/users/{target_user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    target_user_id: uuid.UUID,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Remove a CA from the firm. Restricted to OWNER only."""
    if current_user.role != UserRole.OWNER:
        raise HTTPException(status_code=403, detail="Only the Firm Owner can remove users.")

    if target_user_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot remove yourself.")

    target_user = await session.get(CAUser, target_user_id)
    if not target_user or target_user.firm_id != current_user.firm_id:
        raise HTTPException(status_code=404, detail="User not found in your firm.")

    await session.delete(target_user)
    await session.commit()
    return None