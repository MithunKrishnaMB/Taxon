import enum
import uuid
from datetime import datetime, timezone
from typing import Any
from sqlalchemy import DateTime, Enum, ForeignKey, JSON, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class AuditActionType(str, enum.Enum):
    """Statutory audit event categories."""
    IMS_MANUAL_OVERRIDE = "IMS_MANUAL_OVERRIDE"      # CA overrode an AI Section 17(5) decision
    TDS_RECTIFICATION_SENT = "TDS_RECTIFICATION_SENT"  # CA drafted & copied a vendor notice
    BATCH_UPLOAD_COMPLETED = "BATCH_UPLOAD_COMPLETED"  # 50k-row ingestion finalized
    TDL_QUERY_EXECUTED = "TDL_QUERY_EXECUTED"          # Natural language Tally query run


class AuditLog(Base):
    """Append-only statutory audit trail required for ICAI & CGST compliance.
    
    Why we need this:
    If a tax officer inspects a client's GST credit claim, the CA can produce
    this log proving: 'On August 7, CA Mithun overrode Invoice INV-101 to ACCEPT 
    because the vehicle was used for freight transport, exempting it from 17(5) blocking.'
    """
    __tablename__ = "audit_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True
    )
    # Multi-tenant isolation: Which Firm, which Client Company, and WHICH Accountant?
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
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ca_users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    action_type: Mapped[AuditActionType] = mapped_column(
        Enum(AuditActionType, name="audit_action_type_enum"),
        nullable=False,
        index=True,
    )
    
    # Target entity being modified (e.g., Invoice UUID or doc_no string)
    entity_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # JSON snapshots of the record BEFORE and AFTER the human override
    old_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    new_state: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)

    # Human-readable justification or Arize Phoenix AI Trace reference
    reasoning: Mapped[str] = mapped_column(Text, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
    )