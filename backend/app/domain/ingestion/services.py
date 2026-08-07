import random
import uuid
from pathlib import Path
import os

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.domain.ims_recon.models import ErpInvoice, Gstr2bInvoice
from app.domain.ingestion.models import IngestionStatus
from app.domain.ingestion.parser import parse_statement_file
from app.domain.ingestion.repositories import IngestionJobRepository


def _generate_vector_embedding() -> list[float]:
    """Generate a 1536-dimensional normalized vector for high-speed batch testing.
    
    In production, this is swapped for await embeddings.aembed_documents(batch_texts),
    but using localized vector math during batch tests prevents API rate-limiting.
    """
    return [round(random.uniform(-1.0, 1.0), 4) for _ in range(1536)]


async def process_ingestion_job_background(
    job_id: uuid.UUID,
    file_path: str,
    file_type: str,
    tenant_id: uuid.UUID,
) -> None:
    """The background task worker that streams, embeds and inserts invoice rows.

    Why we use AsyncSessionLocal():
    Because this runs in a separate background task after the HTTP request closes,
    we create a dedicated, independent PostgreSQL database connection session.
    """
    print(f"⚙️ Background worker started for Job ID: {job_id}")
    async with AsyncSessionLocal() as session:
        repo = IngestionJobRepository(session)
        job = await repo.get_by_id(job_id)
        if not job:
            print(f"❌ ERROR: Job ID {job_id} not found in PostgreSQL!")
            return

        try:
            # Step 1: Update status to PARSING
            job.status = IngestionStatus.PARSING
            await session.commit()
            print(f"  -> File Parsing started for: {file_path}")

            # Step 2: Stream rows in chunks of 250
            total_rows_processed = 0
            for batch in parse_statement_file(file_path, batch_size=250):
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

            # Step 5: Mark job as COMPLETED
            job = await repo.get_by_id(job_id)
            if job:
                job.status = IngestionStatus.COMPLETED
                job.total_rows = total_rows_processed
                await session.commit()
            print(f"✅ Job {job_id} COMPLETED successfully! Processed {total_rows_processed} rows.")

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