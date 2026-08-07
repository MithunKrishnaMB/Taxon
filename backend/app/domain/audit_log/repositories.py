import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.audit_log.models import AuditLog


class AuditLogRepository(BaseRepository[AuditLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(AuditLog, session)

    async def list_by_tenant(
        self,
        tenant_id: uuid.UUID,
        firm_id: uuid.UUID,
        limit: int = 50,
    ) -> list[AuditLog]:
        """Fetch the most recent statutory audit logs for a specific Client Company.

        Security enforcement:
        We filter by BOTH tenant_id and firm_id so a user can never inspect
        an audit trail belonging to another CA Firm.
        """
        query = (
            select(AuditLog)
            .where(AuditLog.tenant_id == tenant_id, AuditLog.firm_id == firm_id)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def list_by_entity(
        self,
        entity_id: str,
        tenant_id: uuid.UUID,
        firm_id: uuid.UUID,
    ) -> list[AuditLog]:
        """Fetch the full change history of a specific invoice or tax ledger."""
        query = (
            select(AuditLog)
            .where(
                AuditLog.entity_id == entity_id,
                AuditLog.tenant_id == tenant_id,
                AuditLog.firm_id == firm_id,
            )
            .order_by(AuditLog.created_at.asc())
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())