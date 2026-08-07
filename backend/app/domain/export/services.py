import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.auth.models import Tenant
from app.domain.export.schemas import GstnImsActionItem, GstnImsExportPayload
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation, ReconStatus


async def generate_gstn_ims_json(
    tenant_id: uuid.UUID,
    return_period: str,
    session: AsyncSession,
) -> GstnImsExportPayload:
    """Generate the official statutory GSTN IMS Action JSON payload for a client.
    
    What it does:
    1. Fetches the Client Company's GSTIN.
    2. Queries all ImsReconciliation records for this tenant.
    3. Maps internal database states (e.g., ReconStatus.ACCEPT) to GST Portal strings.
    4. Calculates aggregate counts for statutory validation.
    """
    # 1. Verify tenant exists and fetch their official GSTIN
    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        raise ValueError("Client Company (Tenant) not found.")

    # 2. Query all reconciled records for this tenant
    query = (
        select(ImsReconciliation, ErpInvoice, Gstr2bInvoice)
        .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
        .outerjoin(Gstr2bInvoice, ImsReconciliation.gstr2b_id == Gstr2bInvoice.id)
        .where(ErpInvoice.tenant_id == tenant_id)
    )
    result = await session.execute(query)
    rows = result.all()

    action_items: list[GstnImsActionItem] = []
    accepted_count = 0
    rejected_count = 0
    pending_count = 0

    # 3. Format each record into statutory GSTN schema
    for recon, erp_inv, gstr_inv in rows:
        action_str = recon.status.value.upper()
        
        if action_str == "ACCEPT":
            accepted_count += 1
        elif action_str == "REJECT":
            rejected_count += 1
        else:
            pending_count += 1
            action_str = "PENDING"

        action_items.append(
            GstnImsActionItem(
                doc_no=erp_inv.doc_no,
                supplier_gstin=gstr_inv.supplier_gstin if gstr_inv else "UNREGISTERED",
                irn=gstr_inv.irn if gstr_inv else None,
                action=action_str,
                reason_code="17(5)_BLOCKED" if recon.cgst_17_5_flag else None,
            )
        )

    # 4. Return the complete statutory filing payload
    return GstnImsExportPayload(
        gstin=tenant.gstin,
        return_period=return_period,
        total_records=len(action_items),
        accepted_count=accepted_count,
        rejected_count=rejected_count,
        pending_count=pending_count,
        action_items=action_items,
    )