import uuid
from pydantic import BaseModel, Field


class GstnImsActionItem(BaseModel):
    """Single invoice action formatted for the official GSTN IMS JSON upload."""
    doc_no: str = Field(..., description="Invoice / Document Number")
    supplier_gstin: str = Field(..., description="15-character Supplier GSTIN")
    irn: str | None = Field(None, description="Invoice Reference Number (if e-Invoiced)")
    action: str = Field(
        ...,
        description="Statutory Action: 'ACCEPT', 'REJECT', or 'PENDING'",
    )
    reason_code: str | None = Field(
        None,
        description="Optional statutory rejection code (e.g., '17(5)_BLOCKED')",
    )


class GstnImsExportPayload(BaseModel):
    """The master JSON file payload required by the GST Portal / Offline Utility."""
    gstin: str = Field(..., description="Client Company's 15-character GSTIN")
    return_period: str = Field(..., example="072026", description="MMYYYY format")
    total_records: int
    accepted_count: int
    rejected_count: int
    pending_count: int
    action_items: list[GstnImsActionItem]

    class Config:
        from_attributes = True