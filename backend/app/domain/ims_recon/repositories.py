import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice, ImsReconciliation


class ErpInvoiceRepository(BaseRepository[ErpInvoice]):
    def __init__(self, session: AsyncSession):
        super().__init__(ErpInvoice, session)

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

    async def get_reconciliations_for_tenant(self, tenant_id: uuid.UUID) -> Sequence[dict]:
        from sqlalchemy.orm import aliased
        
        # We need to join ErpInvoice to filter by tenant and get doc_no/amount, 
        # and Gstr2bInvoice for supplier_gstin
        query = (
            select(
                ImsReconciliation.id,
                ImsReconciliation.status,
                ImsReconciliation.cgst_17_5_flag,
                ErpInvoice.doc_no.label("invoice_number"),
                ErpInvoice.amount.label("amount"),
                ErpInvoice.gst_amount.label("gst_amount"),
                Gstr2bInvoice.supplier_gstin.label("supplier_gstin"),
            )
            .join(ErpInvoice, ImsReconciliation.erp_id == ErpInvoice.id)
            .outerjoin(Gstr2bInvoice, ImsReconciliation.gstr2b_id == Gstr2bInvoice.id)
            .where(ErpInvoice.tenant_id == tenant_id)
        )
        
        result = await self.session.execute(query)
        rows = result.all()
        
        res = []
        for row in rows:
            reasoning = None
            if row.cgst_17_5_flag:
                reasoning = "Blocked under Section 17(5) - Ineligible ITC"
            elif row.status == "REJECT":
                reasoning = "Invoice metadata mismatch or missing in GSTR-2B"
            
            res.append({
                "id": row.id,
                "invoice_number": row.invoice_number,
                "supplier_gstin": row.supplier_gstin,
                "amount": row.amount,
                "gst_amount": row.gst_amount,
                "status": row.status,
                "ai_reasoning": reasoning
            })
        return res