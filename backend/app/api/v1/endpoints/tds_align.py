# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.tds_align.models import TdsLedger
from app.domain.tds_align.repositories import TdsAnomalyRepository, TdsLedgerRepository
from app.domain.tds_align.schemas import TdsAnomalyResponse, TdsInspectRequest
from app.domain.tds_align.services import TdsAlignService

router = APIRouter()


@router.post("/inspect-ledger", response_model=TdsAnomalyResponse, status_code=201)
async def inspect_tds_ledger(
    payload: TdsInspectRequest,
    session: AsyncSession = Depends(get_db),
):
    """Run Autoencoder anomaly detection on a vendor TDS ledger and draft RAG letter if flagged."""
    ledger_repo = TdsLedgerRepository(session)
    anomaly_repo = TdsAnomalyRepository(session)
    service = TdsAlignService(anomaly_repo)

    # 1. Create the ledger entry
    ledger = await ledger_repo.create({
        "tenant_id": payload.tenant_id,
        "pan": payload.pan,
        "section": payload.section,
        "amount_paid": payload.amount_paid,
        "tds_deducted": payload.tds_deducted,
    })

    # 2. Inspect with Autoencoder + Gemini RAG
    try:
        anomaly = await service.inspect_ledger_entry(ledger)
        return anomaly
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"TDS Inspection failed: {str(exc)}")