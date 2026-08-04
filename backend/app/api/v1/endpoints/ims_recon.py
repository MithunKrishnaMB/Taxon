# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.ims_recon.models import ErpInvoice
from app.domain.ims_recon.repositories import ErpInvoiceRepository, ImsReconciliationRepository
from app.domain.ims_recon.schemas import InvoiceReconcileRequest, ReconciliationResponse
from app.domain.ims_recon.services import ImsReconciliationService

router = APIRouter()


@router.post("/reconcile-single", response_model=ReconciliationResponse, status_code=201)
async def reconcile_invoice(
    payload: InvoiceReconcileRequest,
    session: AsyncSession = Depends(get_db),
):
    """Reconcile a single ERP invoice against GSTR-2B using pgvector and LangGraph."""
    
    # 1. Initialize Repositories and Service
    erp_repo = ErpInvoiceRepository(session)
    recon_repo = ImsReconciliationRepository(session)
    service = ImsReconciliationService(erp_repo, recon_repo)

    # 2. Save incoming ERP invoice to database
    erp_invoice = await erp_repo.create({
        "tenant_id": payload.tenant_id,
        "doc_no": payload.doc_no,
        "amount": payload.amount,
        "gst_amount": payload.gst_amount,
        "vector_embed": payload.vector_embed,
    })

    # 3. Run AI reconciliation pipeline
    try:
        reconciliation = await service.reconcile_single_invoice(
            tenant_id=payload.tenant_id,
            erp_invoice=erp_invoice,
        )
        return reconciliation
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"AI Reconciliation Pipeline failed: {str(exc)}"
        )