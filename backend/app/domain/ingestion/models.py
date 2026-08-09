import enum
import uuid
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class IngestionStatus(str, enum.Enum):
    """The lifecycle stages of a bulk file upload job."""
    QUEUED = "QUEUED"          # File uploaded; waiting for background worker
    PARSING = "PARSING"        # Reading spreadsheet and checking GSTIN regex rules
    EMBEDDING = "EMBEDDING"    # Generating 1536-dim vector embeddings via Gemini
    RECONCILING = "RECONCILING" # AI is evaluating the records
    COMPLETED = "COMPLETED"    # All rows successfully inserted into PostgreSQL
    FAILED = "FAILED"          # Job aborted due to corrupt file or schema mismatch


class IngestionJob(Base):
    """Tracks live progress of bulk Excel/CSV statement uploads.
    
    Why we need this:
    Instead of making the CA sit on a loading screen, our frontend can poll
    this table every 2 seconds to render a live progress bar:
    'processed_rows / total_rows (e.g., 25,000 / 50,000)'.
    """
    __tablename__ = "ingestion_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # Security: Link job to the CA Firm AND specific Client Company
    firm_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ca_firms.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    file_name: Mapped[str] = mapped_column(
        String(255), nullable=False, doc="Original uploaded filename (e.g., GSTR2B_April.xlsx)"
    )
    file_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of statement: 'GSTR2B', 'ERP_LEDGER'  or 'TDS_26AS'",
    )
    status: Mapped[IngestionStatus] = mapped_column(
        Enum(IngestionStatus, name="ingestion_status_enum"),
        default=IngestionStatus.QUEUED,
        index=True,
    )

    # Real-time progress counters
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    processed_rows: Mapped[int] = mapped_column(Integer, default=0)

    # Error reporting if the spreadsheet format is invalid
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )