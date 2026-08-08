import uuid
from pydantic import BaseModel
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.auth.models import CAUser
from app.domain.ims_recon.models import ImsReconciliation, ReconStatus
from app.domain.audit_log.models import AuditLog

router = APIRouter()

class DashboardStatsResponse(BaseModel):
    total_invoices_reconciled: int
    pending_ai_reviews: int
    itc_blocked_17_5: int

class RecentAuditActivity(BaseModel):
    id: uuid.UUID
    action_type: str
    entity_id: str
    reasoning: str
    timestamp: str

class DashboardResponse(BaseModel):
    stats: DashboardStatsResponse
    recent_activity: list[RecentAuditActivity]
    
    class Config:
        from_attributes = True

@router.get("/stats", response_model=DashboardResponse)
async def get_dashboard_stats(
    tenant_id: uuid.UUID,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Fetch high-level dashboard metrics and recent activity for the selected tenant."""
    # 1. Total Invoices Reconciled (Status = ACCEPT or REJECT)
    # We will join with ErpInvoice to filter by tenant_id
    from app.domain.ims_recon.models import ErpInvoice
    
    total_reconciled = await session.scalar(
        select(func.count(ImsReconciliation.id))
        .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
        .where(ErpInvoice.tenant_id == tenant_id)
        .where(ImsReconciliation.status.in_([ReconStatus.ACCEPT, ReconStatus.REJECT]))
    )

    # 2. Pending AI Reviews
    pending_reviews = await session.scalar(
        select(func.count(ImsReconciliation.id))
        .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
        .where(ErpInvoice.tenant_id == tenant_id)
        .where(ImsReconciliation.status == ReconStatus.PENDING)
    )
    
    # 3. ITC Blocked (Section 17(5))
    itc_blocked = await session.scalar(
        select(func.count(ImsReconciliation.id))
        .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
        .where(ErpInvoice.tenant_id == tenant_id)
        .where(ImsReconciliation.cgst_17_5_flag == True)
    )
    
    # 4. Recent Audit Activity
    recent_audit_rows = await session.execute(
        select(AuditLog)
        .where(AuditLog.tenant_id == tenant_id)
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    )
    recent_audit = recent_audit_rows.scalars().all()
    
    activities = []
    for row in recent_audit:
        activities.append({
            "id": row.id,
            "action_type": row.action_type,
            "entity_id": row.entity_id,
            "reasoning": row.reasoning or "",
            "timestamp": row.created_at.isoformat()
        })
        
    return {
        "stats": {
            "total_invoices_reconciled": total_reconciled or 0,
            "pending_ai_reviews": pending_reviews or 0,
            "itc_blocked_17_5": itc_blocked or 0,
        },
        "recent_activity": activities
    }
