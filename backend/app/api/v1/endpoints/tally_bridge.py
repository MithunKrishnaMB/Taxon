# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.domain.tally_bridge.repositories import TallyJobRepository
from app.domain.tally_bridge.schemas import NaturalLanguageQueryRequest, TallyJobResponse
from app.domain.tally_bridge.services import TallyBridgeService

router = APIRouter()


@router.post("/query-nl", response_model=TallyJobResponse, status_code=201)
async def submit_natural_language_query(
    payload: NaturalLanguageQueryRequest,
    session: AsyncSession = Depends(get_db),
):
    """Translate English audit questions into Tally XML via Gemini and Circuit Breaker."""
    job_repo = TallyJobRepository(session)
    service = TallyBridgeService(job_repo)

    try:
        job = await service.process_natural_language_query(
            tenant_id=str(payload.tenant_id),
            prompt_text=payload.query,
        )
        return job
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Tally Bridge error: {str(exc)}")