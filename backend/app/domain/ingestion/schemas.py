import re
import uuid
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ParsedInvoiceRow(BaseModel):
    """Standardized representation of a single invoice row extracted from Excel/CSV."""
    doc_no: str = Field(..., description="Invoice / Document Number")
    supplier_gstin: str = Field(..., description="15-character Indian GSTIN")
    amount: Decimal = Field(..., description="Total Invoice Amount")
    gst_amount: Decimal = Field(..., description="Total GST Amount (IGST + CGST + SGST)")

    @field_validator("supplier_gstin")
    @classmethod
    def validate_indian_gstin(cls, v: str) -> str:
        """Verify that the GSTIN looks like a standard 15-character Indian format."""
        cleaned = v.strip().upper()
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        if not re.match(pattern, cleaned):
            raise ValueError(f"Invalid Indian GSTIN format: '{cleaned}'")
        return cleaned

    @field_validator("doc_no")
    @classmethod
    def clean_doc_no(cls, v: str) -> str:
        return v.strip().upper()


class IngestionJobResponse(BaseModel):
    """The Claim Ticket returned to the React UI immediately after file upload."""
    id: uuid.UUID = Field(validation_alias="id", serialization_alias="job_id")
    file_name: str
    status: str
    total_rows: int
    processed_rows: int
    error_message: str | None = None

    class Config:
        from_attributes = True