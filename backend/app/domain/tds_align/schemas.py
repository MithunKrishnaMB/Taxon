import uuid
from decimal import Decimal
from pydantic import BaseModel, Field


class TdsInspectRequest(BaseModel):
    """Request payload to inspect a vendor TDS ledger entry."""
    tenant_id: uuid.UUID
    pan: str = Field(..., min_length=10, max_length=10, example="ABCDE1234F")
    section: str = Field(..., example="194C")
    amount_paid: Decimal = Field(..., example="100000.00")
    tds_deducted: Decimal = Field(..., example="1000.00")  # Intentional 1% under-deduction


class TdsAnomalyResponse(BaseModel):
    """Response returning the AI Autoencoder MSE score and RAG draft letter."""
    id: uuid.UUID
    reconstruction_loss: float
    is_anomalous: bool
    rag_rectification_draft: str | None

    class Config:
        from_attributes = True