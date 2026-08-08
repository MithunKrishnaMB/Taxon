import enum
import uuid
from sqlalchemy import Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class UserRole(str, enum.Enum):
    """Strict 4-tier hierarchy for CA Firm permissions."""
    OWNER = "OWNER"      # Highest clearance, registers the firm
    ADMIN = "ADMIN"      # Can promote/demote Managers and Clerks
    MANAGER = "MANAGER"  # Operational workflows
    CLERK = "CLERK"      # Default role for new users; view-only + upload


class CAFirm(Base):
    """The Chartered Accountancy Firm (The Building)."""
    __tablename__ = "ca_firms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    registration_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True
    )


class CAUser(Base):
    """An accountant logging into the system."""
    __tablename__ = "ca_users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    firm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ca_firms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    email: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, index=True
    )
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # NEW: Role-Based Access Control column
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, name="user_role_enum"),
        default=UserRole.CLERK,
        server_default="CLERK", # Ensures existing DB records default to CLERK
        nullable=False,
    )

    firm: Mapped["CAFirm"] = relationship()


class Tenant(Base):
    """A Client Company managed by the CA Firm."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    firm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ca_firms.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    gstin: Mapped[str] = mapped_column(
        String(15), unique=True, nullable=False, index=True
    )
    legal_name: Mapped[str] = mapped_column(String(255), nullable=False)

    firm: Mapped["CAFirm"] = relationship()