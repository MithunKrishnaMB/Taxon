import uuid
# pyrefly: ignore [missing-import]
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_ca_user
from app.domain.audit_log.models import AuditLog
# pyrefly: ignore [missing-import]
from app.domain.audit_log.repositories import AuditLogRepository
from app.domain.audit_log.schemas import AuditLogResponse, AuditOverrideRequest
from app.domain.auth.models import CAUser

router = APIRouter()


@router.post(
    "/log-override",
    response_model=AuditLogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_statutory_override_log(
    payload: AuditOverrideRequest,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Record an immutable statutory override (e.g., CA overriding an AI GST rejection).

    Why this is required:
    ICAI guidelines require explicit attribution and justification whenever
    automated compliance decisions are overridden by human intervention.
    """
    repo = AuditLogRepository(session)
    log_entry = await repo.create({
        "firm_id": current_user.firm_id,
        "tenant_id": payload.tenant_id,
        "user_id": current_user.id,
        "action_type": payload.action_type,
        "entity_id": payload.entity_id,
        "old_state": payload.old_state,
        "new_state": payload.new_state,
        "reasoning": payload.reasoning,
    })
    return log_entry


@router.get("/logs", response_model=list[AuditLogResponse])
async def get_client_audit_trail(
    tenant_id: uuid.UUID,
    limit: int = 50,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Fetch recent statutory audit logs for a specific Client Company."""
    repo = AuditLogRepository(session)
    return await repo.list_by_tenant(
        tenant_id=tenant_id, firm_id=current_user.firm_id, limit=limit
    )


@router.get("/entity/{entity_id}", response_model=list[AuditLogResponse])
async def get_entity_history(
    entity_id: str,
    tenant_id: uuid.UUID,
    current_user: CAUser = Depends(get_current_ca_user),
    session: AsyncSession = Depends(get_db),
):
    """Fetch the full historical audit timeline for a specific invoice or document."""
    repo = AuditLogRepository(session)
    return await repo.list_by_entity(
        entity_id=entity_id, tenant_id=tenant_id, firm_id=current_user.firm_id
    )