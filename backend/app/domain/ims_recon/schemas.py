import uuid
from decimal import Decimal
from pydantic import BaseModel, Field
from app.domain.ims_recon.models import ReconStatus


class InvoiceReconcileRequest(BaseModel):
    """What the user sends from the frontend to reconcile an invoice."""
    tenant_id: uuid.UUID
    doc_no: str = Field(..., example="INV-2026-001")
    amount: Decimal = Field(..., example="50000.00")
    gst_amount: Decimal = Field(..., example="9000.00")
    # For testing, we pass a sample 1536-dimensional vector (or we can generate it)
    vector_embed: list[float] = Field(
        default_factory=lambda: [0.1] * 1536,
        description="1536-dim embedding representing invoice metadata"
    )


class ReconciliationResponse(BaseModel):
    """What our API sends back to the frontend after AI evaluation."""
    id: uuid.UUID
    erp_id: uuid.UUID
    gstr2b_id: uuid.UUID | None
    status: ReconStatus
    cgst_17_5_flag: bool
    confidence_score: float

    class Config:
        from_attributes = True  # Allows Pydantic to read SQLAlchemy ORM objects directly