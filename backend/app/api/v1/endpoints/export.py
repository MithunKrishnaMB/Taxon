import uuid
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.auth.models import CAUser
from app.domain.export.schemas import GstnImsExportPayload
from app.domain.export.services import generate_gstn_ims_json

router = APIRouter()


@router.get(
    "/gstn-json",
    response_model=GstnImsExportPayload,
    status_code=status.HTTP_200_OK,
)
async def export_gstn_ims_action_json(
    tenant_id: uuid.UUID = Query(..., description="Target Client Company UUID"),
    return_period: str = Query("072026", description="Tax return period in MMYYYY format"),
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Generate and export official GSTN IMS Action JSON for statutory filing.

    Security rule:
    Ensures the user is an authenticated CA Partner/Manager before exposing
    official statutory filing data.
    """
    try:
        payload = await generate_gstn_ims_json(
            tenant_id=tenant_id,
            return_period=return_period,
            session=session,
        )
        return payload
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        )