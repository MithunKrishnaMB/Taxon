import uuid
from decimal import Decimal
from sqlalchemy import Boolean, Float, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class TdsLedger(Base):
    __tablename__ = "tds_ledgers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    pan: Mapped[str] = mapped_column(String(10), nullable=False, index=True)
    section: Mapped[str] = mapped_column(
        String(10), nullable=False, doc="e.g., 194C, 194J"
    )
    amount_paid: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    tds_deducted: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    __table_args__ = (
        Index("idx_tds_tenant_pan_sec", "tenant_id", "pan", "section"),
    )


class TdsAnomaly(Base):
    __tablename__ = "tds_anomalies"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    ledger_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tds_ledgers.id", ondelete="CASCADE"),
        unique=True,
    )
    reconstruction_loss: Mapped[float] = mapped_column(
        Float, nullable=False, doc="MSE loss from Autoencoder model"
    )
    is_anomalous: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    rag_rectification_draft: Mapped[str | None] = mapped_column(Text, nullable=True)

    ledger: Mapped["TdsLedger"] = relationship()

    # Partial Index: Only index rows where is_anomalous is TRUE
    __table_args__ = (
        Index(
            "idx_active_tds_anomalies",
            "is_anomalous",
            postgresql_where=(is_anomalous.is_(True)),
        ),
    )