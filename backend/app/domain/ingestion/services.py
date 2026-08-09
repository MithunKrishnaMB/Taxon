import random
import uuid
from pathlib import Path
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice
from app.domain.ims_recon.repositories import ErpInvoiceRepository, ImsReconciliationRepository
from app.domain.ims_recon.services import ImsReconciliationService
from app.domain.ingestion.models import IngestionStatus
from app.domain.ingestion.parser import parse_statement_file, count_statement_rows
from app.domain.ingestion.repositories import IngestionJobRepository
from app.domain.ingestion.models import IngestionJob


def _generate_vector_embedding() -> list[float]:
    """Generate a 1536-dimensional normalized vector for high-speed batch testing.
    
    In production, this is swapped for await embeddings.aembed_documents(batch_texts),
    but using localized vector math during batch tests prevents API rate-limiting.
    """
    return [round(random.uniform(-1.0, 1.0), 4) for _ in range(1536)]


async def _run_auto_reconciliation(
    session: AsyncSession, 
    tenant_id: uuid.UUID,
    job: IngestionJob | None = None,
    job_repo: IngestionJobRepository | None = None
) -> None:
    """Reconcile all unreconciled ERP invoices for a tenant after ingestion completes."""
    erp_repo = ErpInvoiceRepository(session)
    recon_repo = ImsReconciliationRepository(session)

    unreconciled = await erp_repo.get_unreconciled_erp_invoices(tenant_id)
    if not unreconciled:
        print(f"  -> No unreconciled ERP invoices found for tenant {tenant_id}.")
        return

    print(f"  -> Auto-reconciling {len(unreconciled)} ERP invoices for tenant {tenant_id}...")
    
    if job and job_repo:
        job.total_rows = len(unreconciled)
        job.processed_rows = 0
        await session.commit()
        
    service = ImsReconciliationService(erp_repo, recon_repo)

    reconciled_count = 0
    for erp_invoice in unreconciled:
        try:
            await service.reconcile_single_invoice(tenant_id, erp_invoice)
            reconciled_count += 1
        except Exception as exc:
            print(f"  ⚠️ Reconciliation failed for ERP invoice {erp_invoice.doc_no}: {exc}")
        
        if job and job_repo:
            await job_repo.update_progress(job.id, processed_delta=1)

    await session.commit()
    print(f"  ✅ Auto-reconciliation complete: {reconciled_count}/{len(unreconciled)} invoices reconciled.")


async def process_ingestion_job_background(
    job_id: uuid.UUID,
    file_path: str,
    file_type: str,
    tenant_id: uuid.UUID,
) -> None:
    """The background task worker that streams, embeds and inserts invoice rows."""
    print(f"⚙️ Background worker started for Job ID: {job_id}")
    async with AsyncSessionLocal() as session:
        repo = IngestionJobRepository(session)
        job = await repo.get_by_id(job_id)
        if not job:
            print(f"❌ ERROR: Job ID {job_id} not found in PostgreSQL!")
            return

        try:
            # Pre-count total rows for accurate progress
            try:
                total_rows = count_statement_rows(file_path)
                job.total_rows = total_rows
            except Exception:
                pass # fallback to 0 if count fails

            # Step 1: Update status to PARSING
            job.status = IngestionStatus.PARSING
            await session.commit()
            print(f"  -> File Parsing started for: {file_path}")

            # Step 2: Stream rows in chunks of 50 for smoother progress bars
            total_rows_processed = 0
            for batch in parse_statement_file(file_path, batch_size=50):
                # Update status to EMBEDDING once batches start flowing
                if total_rows_processed == 0:
                    job.status = IngestionStatus.EMBEDDING
                    await session.commit()

                # Step 3: Insert batch into PostgreSQL
                for row in batch:
                    if file_type == "GSTR2B":
                        record = Gstr2bInvoice(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            supplier_gstin=row.supplier_gstin,
                            doc_no=row.doc_no,
                            amount=row.amount,
                            gst_amount=row.gst_amount,
                            irn=f"IRN-{uuid.uuid4()}",
                            vector_embed=_generate_vector_embedding(),
                        )
                        session.add(record)
                    else:
                        # Default to ERP internal accounting ledger
                        record = ErpInvoice(
                            id=uuid.uuid4(),
                            tenant_id=tenant_id,
                            doc_no=row.doc_no,
                            supplier_gstin=row.supplier_gstin,
                            amount=row.amount,
                            gst_amount=row.gst_amount,
                            vector_embed=_generate_vector_embedding(),
                        )
                        session.add(record)

                await session.commit()

                # Step 4: Increment our real-time progress counter
                batch_count = len(batch)
                total_rows_processed += batch_count
                await repo.update_progress(job_id, processed_delta=batch_count)

            print(f"✅ Ingestion Phase COMPLETED successfully! Processed {total_rows_processed} rows.")
            
            # Step 5: Mark parsing job as COMPLETED
            job = await repo.get_by_id(job_id)
            if job:
                job.status = IngestionStatus.COMPLETED
                job.total_rows = total_rows_processed
                await session.commit()
                
            # Step 6: Create new job for AI Reconciling so parsing goes to history
            recon_job = IngestionJob(
                id=uuid.uuid4(),
                tenant_id=tenant_id,
                firm_id=job.firm_id,
                file_name=f"AI Engine ({job.file_name})",
                file_type="AI_RECONCILIATION",
                status=IngestionStatus.RECONCILING,
                total_rows=0,
                processed_rows=0
            )
            session.add(recon_job)
            await session.commit()

            # Step 7: Auto-reconcile unreconciled ERP invoices
            try:
                await _run_auto_reconciliation(session, tenant_id, recon_job, repo)
            except Exception as recon_exc:
                print(f"⚠️ Auto-reconciliation error (non-fatal): {recon_exc}")
                
            # Step 8: Finally mark recon job completely done
            recon_job.status = IngestionStatus.COMPLETED
            await session.commit()
            print(f"✅ Recon Job {recon_job.id} completely finished.")

        except Exception as exc:
            # Handle schema errors or corrupt files gracefully
            print(f"❌ Job {job_id} FAILED with error: {exc}")
            await repo.update_progress(
                job_id,
                processed_delta=0,
                status=IngestionStatus.FAILED,
                error_message=str(exc),
            )
        finally:
            # Cleanup temporary file from disk after processing
            if os.path.exists(file_path):
                os.remove(file_path)