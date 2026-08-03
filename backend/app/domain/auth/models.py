import uuid
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Tenant(Base):
    __tablename__ = "tenants"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
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