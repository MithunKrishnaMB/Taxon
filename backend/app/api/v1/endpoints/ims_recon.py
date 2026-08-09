import uuid
from pydantic import BaseModel
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.ims_recon.models import ErpInvoice, ReconStatus
from app.domain.ims_recon.repositories import ErpInvoiceRepository, ImsReconciliationRepository
from app.domain.ims_recon.schemas import InvoiceReconcileRequest, ReconciliationResponse, ReconciliationListResponse
from app.domain.ims_recon.services import ImsReconciliationService
from app.domain.audit_log.models import AuditLog, AuditActionType

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


@router.get("/reconciliations", response_model=list[ReconciliationListResponse])
async def list_reconciliations(
    tenant_id: uuid.UUID,
    session: AsyncSession = Depends(get_db),
):
    """Fetch the table of invoices for reconciliation view."""
    repo = ImsReconciliationRepository(session)
    return await repo.get_reconciliations_for_tenant(tenant_id)


class OverrideRequest(BaseModel):
    new_status: ReconStatus
    reasoning: str

@router.put("/reconciliations/{recon_id}/override")
async def manual_override_reconciliation(
    recon_id: uuid.UUID,
    payload: OverrideRequest,
    current_user = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Manually override an AI reconciliation decision."""
    repo = ImsReconciliationRepository(session)
    recon = await repo.get_by_id(recon_id)
    if not recon:
        raise HTTPException(status_code=404, detail="Reconciliation not found")
        
    old_status = recon.status
    recon.status = payload.new_status
    
    erp_invoice = await session.get(ErpInvoice, recon.erp_id)
    if erp_invoice:
        audit = AuditLog(
            firm_id=current_user.firm_id,
            tenant_id=erp_invoice.tenant_id,
            user_id=current_user.id,
            action_type=AuditActionType.IMS_MANUAL_OVERRIDE,
            entity_id=f"{erp_invoice.doc_no}",
            old_state={"status": old_status.value},
            new_state={"status": payload.new_status.value},
            reasoning=payload.reasoning
        )
        session.add(audit)
        
    await session.commit()
    
    return {"success": True}