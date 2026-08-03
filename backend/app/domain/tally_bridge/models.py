import enum
import uuid
from sqlalchemy import Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class JobStatus(str, enum.Enum):
    QUEUED = "QUEUED"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class CircuitBreakerState(str, enum.Enum):
    CLOSED = "CLOSED"  # Normal operations
    OPEN = "OPEN"      # Tally offline; requests paused
    HALF_OPEN = "HALF_OPEN"  # Testing connection recovery


class TallySyncJob(Base):
    __tablename__ = "tally_sync_jobs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    tenant_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("tenants.id", ondelete="CASCADE"), index=True
    )
    tdl_query_xml: Mapped[str] = mapped_column(
        Text, nullable=False, doc="Generated Tally Definition Language XML"
    )
    status: Mapped[JobStatus] = mapped_column(
        Enum(JobStatus, name="tally_job_status_enum"),
        default=JobStatus.QUEUED,
        index=True,
    )
    circuit_breaker_state: Mapped[CircuitBreakerState] = mapped_column(
        Enum(CircuitBreakerState, name="circuit_breaker_state_enum"),
        default=CircuitBreakerState.CLOSED,
    )