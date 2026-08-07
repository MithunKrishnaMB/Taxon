# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.api.v1.endpoints import auth, ims_recon, ingestion, tds_align, tally_bridge

api_router = APIRouter()

# Register Authentication & Firm endpoints
api_router.include_router(
    auth.router, prefix="/auth", tags=["Authentication & CA Firm Identity"]
)

# Bulk ETL & File Ingestion
api_router.include_router(
    ingestion.router, prefix="/ingestion", tags=["Bulk ETL & File Ingestion"]
)

api_router.include_router(
    ims_recon.router, prefix="/ims", tags=["Auto-IMS Reconciliation"]
)
api_router.include_router(
    tds_align.router, prefix="/tds", tags=["TDS-Align Anomaly Detection"]
)
api_router.include_router(
    tally_bridge.router, prefix="/tally", tags=["Tally-Bridge Orchestrator"]
)