import uuid
from collections.abc import Sequence

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation


class ErpInvoiceRepository(BaseRepository[ErpInvoice]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErpInvoice, session)

    async def get_unreconciled_erp_invoices(
        self, tenant_id: uuid.UUID
    ) -> Sequence[ErpInvoice]:
        """Fetch all ERP invoices that have not been reconciled yet or are still PENDING."""
        from sqlalchemy import or_
        from app.domain.ims_recon.models import ReconStatus
        query = (
            select(ErpInvoice)
            .outerjoin(ImsReconciliation, ImsReconciliation.erp_id == ErpInvoice.id)
            .where(ErpInvoice.tenant_id == tenant_id)
            .where(
                or_(
                    ImsReconciliation.id.is_(None),
                    ImsReconciliation.status == ReconStatus.PENDING
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def find_gstr2b_match_by_fields(
        self,
        tenant_id: uuid.UUID,
        supplier_gstin: str,
        doc_no: str,
    ) -> Gstr2bInvoice | None:
        """Deterministic matching: find a GSTR-2B invoice by supplier GSTIN + doc number.
        
        This is the primary matching strategy — exact join on business keys,
        case-insensitive to handle minor formatting differences.
        """
        query = (
            select(Gstr2bInvoice)
            .where(Gstr2bInvoice.tenant_id == tenant_id)
            .where(func.upper(Gstr2bInvoice.supplier_gstin) == supplier_gstin.strip().upper())
            .where(func.upper(Gstr2bInvoice.doc_no) == doc_no.strip().upper())
            .limit(1)
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def find_similar_gstr2b(
        self,
        tenant_id: uuid.UUID,
        embedding: list[float],
        top_k: int = 3,
        similarity_threshold: float = 0.82,
    ) -> Sequence[tuple[Gstr2bInvoice, float]]:
        """Perform HNSW Vector Cosine Similarity Search in PostgreSQL.

        What it does:
        1. Uses pgvector's cosine distance operator `<=>` to find GSTR-2B invoices
           whose embeddings are mathematically closest to our ERP invoice embedding.
        2. Converts 'cosine distance' (where 0 is identical) into 'similarity score' (where 1 is identical):
           Similarity = 1 - Distance.
        3. Filters out matches below our threshold (0.82) to avoid false positives.

        Why we use this:
        Instead of Python looping through 50,000 invoices in memory (slow),
        PostgreSQL's HNSW graph index finds the top-k matches in <5 milliseconds.
        """
        # Cosine distance operator in pgvector is `.cosine_distance()`
        distance_expr = Gstr2bInvoice.vector_embed.cosine_distance(embedding)
        similarity_expr = (1 - distance_expr).label("similarity_score")

        query = (
            select(Gstr2bInvoice, similarity_expr)
            .where(Gstr2bInvoice.tenant_id == tenant_id)
            .where(similarity_expr >= similarity_threshold)
            .order_by(distance_expr)  # Smallest distance = highest similarity
            .limit(top_k)
        )

        result = await self.session.execute(query)
        # Returns a list of tuples: [(Gstr2bInvoice_object, 0.94), (Gstr2bInvoice_object, 0.86), ...]
        return result.all()  # type: ignore


class ImsReconciliationRepository(BaseRepository[ImsReconciliation]):
    def __init__(self, session: AsyncSession):
        super().__init__(ImsReconciliation, session)

    async def get_reconciliation_by_erp_id(self, erp_id: uuid.UUID) -> ImsReconciliation | None:
        """Fetch an existing reconciliation row for a given ERP invoice."""
        query = select(ImsReconciliation).where(ImsReconciliation.erp_id == erp_id)
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_reconciliations_for_tenant(self, tenant_id: uuid.UUID) -> Sequence[dict]:
        # We need to join ErpInvoice to filter by tenant and get doc_no/amount, 
        # and Gstr2bInvoice for supplier_gstin
        query = (
            select(
                ImsReconciliation.id,
                ImsReconciliation.status,
                ImsReconciliation.cgst_17_5_flag,
                ImsReconciliation.reasoning,
                ErpInvoice.doc_no.label("invoice_number"),
                ErpInvoice.amount.label("amount"),
                ErpInvoice.gst_amount.label("gst_amount"),
                ErpInvoice.supplier_gstin.label("erp_supplier_gstin"),
                Gstr2bInvoice.supplier_gstin.label("gstr_supplier_gstin"),
            )
            .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
            .outerjoin(Gstr2bInvoice, ImsReconciliation.gstr2b_id == Gstr2bInvoice.id)
            .where(ErpInvoice.tenant_id == tenant_id)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        res = []
        for row in rows:
            # Use the persisted AI reasoning if available, otherwise generate from flags
            ai_reasoning = row.reasoning
            if not ai_reasoning:
                if row.cgst_17_5_flag:
                    ai_reasoning = "Blocked under Section 17(5) - Ineligible ITC"
                elif row.status == "REJECT":
                    ai_reasoning = "Invoice metadata mismatch or missing in GSTR-2B"
                elif row.status == "PENDING":
                    ai_reasoning = "Not yet reported by vendor on government portal (missing from GSTR-2B)"
            
            res.append({
                "id": row.id,
                "invoice_number": row.invoice_number,
                "supplier_gstin": row.gstr_supplier_gstin or row.erp_supplier_gstin,
                "amount": row.amount,
                "gst_amount": row.gst_amount,
                "status": row.status,
                "ai_reasoning": ai_reasoning
            })
        return res