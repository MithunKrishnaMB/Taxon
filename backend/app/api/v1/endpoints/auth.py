# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordRequestForm

from app.core.database import get_db
from app.core.security import (
    create_access_token,
    get_current_ca_user,
    get_password_hash,
    verify_password,
)
from app.domain.auth.models import CAUser
from app.domain.auth.repositories import CAFirmRepository, CAUserRepository
from app.domain.auth.schemas import (
    CAUserResponse,
    FirmRegisterRequest,
    FirmRegisterResponse,
    TokenResponse,
    UserLoginRequest,
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
    """Register a new CA Firm and create the initial CA Admin user."""
    firm_repo = CAFirmRepository(session)
    user_repo = CAUserRepository(session)

    # 1. Check for duplicates
    if await firm_repo.get_by_name(payload.firm_name):
        raise HTTPException(status_code=400, detail="An accounting firm with this name already exists.")
    if await user_repo.get_by_email(payload.email):
        raise HTTPException(status_code=400, detail="This email is already registered.")

    # 2. Create the CA Firm
    firm = await firm_repo.create({
        "name": payload.firm_name,
        "registration_number": payload.registration_number,
    })

    # 3. Create the CA User with a securely hashed password
    hashed_pwd = get_password_hash(payload.password)
    user = await user_repo.create({
        "firm_id": firm.id,
        "email": payload.email,
        "full_name": payload.full_name,
        "hashed_password": hashed_pwd,
    })

    return FirmRegisterResponse(
        firm_id=firm.id,
        firm_name=firm.name,
        user=user,
    )


@router.post("/login", response_model=TokenResponse)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: AsyncSession = Depends(get_db),
):
    """Authenticate with Email (typed in the username box) & Password to receive a JWT badge.
    
    Why OAuth2PasswordRequestForm?
    It allows FastAPI's interactive Swagger UI 'Authorize 🔒' button to log you in automatically!
    """
    user_repo = CAUserRepository(session)
    # Note: OAuth2 names the email field 'username', so we pass form_data.username
    user = await user_repo.get_by_email(form_data.username)

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        user_id=user.id,
        firm_id=user.firm_id,
        email=user.email,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        firm_id=user.firm_id,
        user_id=user.id,
    )


@router.get("/me", response_model=CAUserResponse)
async def get_current_user_profile(
    current_user: CAUser = Depends(get_current_ca_user),
):
    """Protected Endpoint: Returns profile details of the currently logged-in CA."""
    return current_user