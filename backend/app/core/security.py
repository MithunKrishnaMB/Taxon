# app/core/security.py
import datetime
import uuid
from typing import Any
# pyrefly: ignore [missing-import]
import jwt
# pyrefly: ignore [missing-import]
from fastapi import Depends, HTTPException, status
# pyrefly: ignore [missing-import]
from fastapi.security import OAuth2PasswordBearer
# pyrefly: ignore [missing-import]
from pwdlib import PasswordHash
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.domain.auth.models import CAUser

# 1. Setup Password Hashing Engine using bcrypt
pwd_context = PasswordHash.recommended()

# 2. Setup FastAPI OAuth2 Token Extractor (Looks for 'Authorization: Bearer <token>' header)
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_STR}/auth/login"
)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check if a typed plain-text password matches the scrambled database hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Scramble a plain-text password into a secure bcrypt hash string."""
    return pwd_context.hash(password)


def create_access_token(
    user_id: uuid.UUID,
    firm_id: uuid.UUID,
    email: str,
    role: str,  # <-- NEW: Accept the role
    expires_delta: datetime.timedelta | None = None,
) -> str:
    """Generate a signed JSON Web Token (JWT) access badge."""
    if expires_delta:
        expire = datetime.datetime.now(datetime.timezone.utc) + expires_delta
    else:
        expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode: dict[str, Any] = {
        "sub": str(user_id),
        "firm_id": str(firm_id),
        "email": email,
        "role": role,  #Embed the role into the tamper-proof token
        "exp": expire,
    }

    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM
    )
    return encoded_jwt


async def get_current_ca_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> CAUser:
    """The Security Checkpoint Guard for Protected API Routes.

    What it does:
    1. Extracts the Bearer JWT token from the incoming HTTP request header.
    2. Decodes and verifies the signature using our SECRET_KEY.
    3. Checks if the token is expired or tampered with.
    4. Fetches the active CAUser from PostgreSQL to ensure the account wasn't deleted.
    5. Returns the authenticated CAUser object to the route handler.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials - token invalid or expired",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode the token payload
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id_str: str | None = payload.get("sub")
        if user_id_str is None:
            raise credentials_exception
        user_id = uuid.UUID(user_id_str)
    except (jwt.PyJWTError, ValueError):
        raise credentials_exception

    # Query PostgreSQL to verify user still exists in the system
    query = select(CAUser).where(CAUser.id == user_id)
    result = await session.execute(query)
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user