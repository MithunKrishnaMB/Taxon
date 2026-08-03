import enum
import uuid
from decimal import Decimal
# pyrefly: ignore [missing-import]
from pgvector.sqlalchemy import Vector
from sqlalchemy import Boolean, Enum, Float, ForeignKey, Index, Numeric, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ReconStatus(str, enum.Enum):
    PENDING = "PENDING"
    ACCEPT = "ACCEPT"
    REJECT = "REJECT"


class ErpInvoice(Base):
    __tablename__ = "erp_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    doc_no: Mapped[str] = mapped_column(String(100), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    gst_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)

    # 1536-dimensional vector embedding of invoice metadata
    vector_embed: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    # Define HNSW Cosine Index for sub-millisecond similarity search
    __table_args__ = (
        Index(
            "idx_erp_invoices_hnsw",
            "vector_embed",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vector_embed": "vector_cosine_ops"},
        ),
    )


class Gstr2bInvoice(Base):
    __tablename__ = "gstr2b_invoices"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    supplier_gstin: Mapped[str] = mapped_column(String(15), nullable=False, index=True)
    irn: Mapped[str] = mapped_column(String(64), unique=True, nullable=True)

    vector_embed: Mapped[list[float]] = mapped_column(Vector(1536), nullable=False)

    __table_args__ = (
        Index(
            "idx_gstr2b_invoices_hnsw",
            "vector_embed",
            postgresql_using="hnsw",
            postgresql_with={"m": 16, "ef_construction": 64},
            postgresql_ops={"vector_embed": "vector_cosine_ops"},
        ),
    )


class ImsReconciliation(Base):
    __tablename__ = "ims_reconciliations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    erp_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("erp_invoices.id", ondelete="CASCADE"),
        unique=True,
    )
    gstr2b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("gstr2b_invoices.id", ondelete="CASCADE"),
        nullable=True,
    )

    status: Mapped[ReconStatus] = mapped_column(
        Enum(ReconStatus, name="recon_status_enum"),
        default=ReconStatus.PENDING,
        index=True,
    )
    cgst_17_5_flag: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        doc="True if flagged as Blocked Credit under Section 17(5)",
    )
    confidence_score: Mapped[float] = mapped_column(Float, default=0.0)

    # ORM Relationships
    erp_invoice: Mapped["ErpInvoice"] = relationship()
    gstr2b_invoice: Mapped["Gstr2bInvoice"] = relationship()