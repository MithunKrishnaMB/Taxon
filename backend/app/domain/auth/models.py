import uuid
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CAFirm(Base):
    """The Chartered Accountancy Firm (The Building).
    
    Every accountant (CAUser) and client company (Tenant) belongs to one CAFirm.
    """
    __tablename__ = "ca_firms"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    name: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False, doc="e.g., Taxon Associates Kerala"
    )
    registration_number: Mapped[str | None] = mapped_column(
        String(50), nullable=True, doc="ICAI Firm Registration Number (FRN)"
    )


class CAUser(Base):
    """An accountant logging into the system (The Employee).
    
    Notice: No roles are defined. Every user in the firm has equal clearance.
    """
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

    # ORM Relationship back to the firm
    firm: Mapped["CAFirm"] = relationship()


class Tenant(Base):
    """A Client Company managed by the CA Firm (e.g., Tata Motors, Infosys)."""
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        index=True,
    )
    # Link each Client Company to the CA Firm that manages its accounts
    firm_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ca_firms.id", ondelete="CASCADE"),
        nullable=True,  # Nullable=True for existing test records; can be enforced later
        index=True,
    )
    gstin: Mapped[str] = mapped_column(
        String(15),
        unique=True,
        nullable=False,
        index=True,
        doc="15-character Indian GST Identification Number",
    )
    legal_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    firm: Mapped["CAFirm"] = relationship()