# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    tenants,
    ims_recon,
    ingestion,
    audit_log,
    export,
    tds_align,
    tally_bridge,
    dashboard,
)

api_router = APIRouter()

# 1. Identity & Security Layer
api_router.include_router(
    auth.router, prefix="/auth", tags=["Authentication & CA Firm Identity"]
)
api_router.include_router(
    tenants.router, prefix="/tenants", tags=["Client Workspaces"]
)

# 2. Bulk ETL & File Ingestion
api_router.include_router(
    ingestion.router, prefix="/ingestion", tags=["Bulk ETL & File Ingestion"]
)

# 3. Statutory Audit Trail
api_router.include_router(
    audit_log.router, prefix="/audit", tags=["Statutory Audit Trail & Overrides"]
)

# 4. Government Portal Export Engine
api_router.include_router(
    export.router, prefix="/export", tags=["Government Portal Export Engine"]
)

# 5. Core Domain AI Endpoints
api_router.include_router(
    ims_recon.router, prefix="/ims", tags=["Auto-IMS Reconciliation"]
)
api_router.include_router(
    tds_align.router, prefix="/tds", tags=["TDS-Align Anomaly Detection"]
)
api_router.include_router(
    tally_bridge.router, prefix="/tally", tags=["Tally-Bridge Orchestrator"]
)
api_router.include_router(
    dashboard.router, prefix="/dashboard", tags=["Dashboard Metrics"]
)