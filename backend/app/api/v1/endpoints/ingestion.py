# app/api/v1/endpoints/ingestion.py
import shutil
import tempfile
import uuid
from pathlib import Path

# pyrefly: ignore [missing-import]
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.auth.models import CAUser
from app.domain.ingestion.models import IngestionStatus
from app.domain.ingestion.repositories import IngestionJobRepository
from app.domain.ingestion.schemas import IngestionJobResponse
from app.domain.ingestion.services import process_ingestion_job_background

router = APIRouter()


@router.post(
    "/upload",
    response_model=IngestionJobResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_statement_file(
    background_tasks: BackgroundTasks,
    tenant_id: uuid.UUID = Form(..., description="Target Client Company UUID"),
    file_type: str = Form(
        "GSTR2B", description="'GSTR2B' or 'ERP_LEDGER'"
    ),
    file: UploadFile = File(...),
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Upload an Excel (.xlsx), CSV (.csv)  or JSON statement for async bulk ingestion.
    
    Returns 202 Accepted immediately with a Job Ticket ID.
    """
    extension = Path(file.filename or "").suffix.lower()
    if extension not in [".xlsx", ".csv", ".json"]:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file format. Please upload .xlsx, .csv  or .json.",
        )

    # 1. Save uploaded file to a temporary disk path
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=extension)
    try:
        shutil.copyfileobj(file.file, temp_file)
        temp_file.close()
    finally:
        file.file.close()

    # 2. Create the IngestionJob ticket in PostgreSQL
    repo = IngestionJobRepository(session)
    job = await repo.create({
        "firm_id": current_user.firm_id,
        "tenant_id": tenant_id,
        "file_name": file.filename or "statement_upload",
        "file_type": file_type.upper(),
        "status": IngestionStatus.QUEUED,
        "total_rows": 0,
        "processed_rows": 0,
    })

    await session.commit()
    await session.refresh(job)

    # 3. Trigger background worker
    background_tasks.add_task(
        process_ingestion_job_background,
        job_id=job.id,
        file_path=temp_file.name,
        file_type=file_type.upper(),
        tenant_id=tenant_id,
    )

    return job


@router.get("/jobs/{job_id}", response_model=IngestionJobResponse)
async def get_ingestion_job_status(
    job_id: uuid.UUID,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Poll real-time ingestion progress (processed_rows / total_rows)."""
    repo = IngestionJobRepository(session)
    job = await repo.get_by_id(job_id)
    if not job or job.firm_id != current_user.firm_id:
        raise HTTPException(status_code=404, detail="Ingestion job ticket not found.")
    return job


@router.get("/jobs", response_model=list[IngestionJobResponse])
async def list_ingestion_jobs(
    tenant_id: uuid.UUID,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """List recent file upload jobs for a specific Client Company."""
    repo = IngestionJobRepository(session)
    return await repo.list_by_tenant(tenant_id)