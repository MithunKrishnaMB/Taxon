import uuid
from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field

from app.domain.audit_log.models import AuditActionType


class AuditOverrideRequest(BaseModel):
    """Payload submitted when a CA overrides an AI compliance decision."""
    tenant_id: uuid.UUID = Field(..., description="Client Company UUID")
    action_type: AuditActionType = Field(
        default=AuditActionType.IMS_MANUAL_OVERRIDE,
        description="Category of audit action",
    )
    entity_id: str = Field(
        ...,
        example="INV-2026-00001",
        description="Invoice number, PAN or target document identifier",
    )
    old_state: dict[str, Any] = Field(
        ...,
        example={"status": "REJECT", "reason": "Section 17(5) blocked credit"},
        description="Snapshot of the record BEFORE the change",
    )
    new_state: dict[str, Any] = Field(
        ...,
        example={"status": "ACCEPT", "reason": "CA verified freight transport exception"},
        description="Snapshot of the record AFTER the change",
    )
    reasoning: str = Field(
        ...,
        min_length=10,
        example="Verified transport exception under CGST Section 17(5)(a)(B). Approved for ITC.",
        description="Statutory justification for the manual override",
    )


class AuditLogResponse(BaseModel):
    """Immutable audit log entry returned to the React frontend or auditor."""
    id: uuid.UUID
    firm_id: uuid.UUID
    tenant_id: uuid.UUID
    user_id: uuid.UUID
    action_type: AuditActionType
    entity_id: str
    old_state: dict[str, Any] | None = None
    new_state: dict[str, Any] | None = None
    reasoning: str
    created_at: datetime

    class Config:
        from_attributes = True