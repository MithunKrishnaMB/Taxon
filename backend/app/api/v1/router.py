# pyrefly: ignore [missing-import]
from fastapi import APIRouter
from app.api.v1.endpoints import ims_recon, tds_align, tally_bridge

api_router = APIRouter()

# Register our three domain endpoints under clean API prefixes
api_router.include_router(
    ims_recon.router, prefix="/ims", tags=["Auto-IMS Reconciliation"]
)
api_router.include_router(
    tds_align.router, prefix="/tds", tags=["TDS-Align Anomaly Detection"]
)
api_router.include_router(
    tally_bridge.router, prefix="/tally", tags=["Tally-Bridge Orchestrator"]
)