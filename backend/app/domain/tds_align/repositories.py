import uuid
from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.tds_align.models import TdsAnomaly, TdsLedger


class TdsLedgerRepository(BaseRepository[TdsLedger]):
    def __init__(self, session: AsyncSession):
        super().__init__(TdsLedger, session)

    async def get_by_pan_and_section(
        self, tenant_id: uuid.UUID, pan: str, section: str
    ) -> Sequence[TdsLedger]:
        """Fetch historical TDS deductions for a specific vendor PAN under a tax section."""
        query = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .where(self.model.pan == pan)
            .where(self.model.section == section)
        )
        result = await self.session.execute(query)
        return result.scalars().all()


class TdsAnomalyRepository(BaseRepository[TdsAnomaly]):
    def __init__(self, session: AsyncSession):
        super().__init__(TdsAnomaly, session)

    async def get_flagged_anomalies(self) -> Sequence[TdsAnomaly]:
        """Fetch only records flagged as anomalous (uses our fast Partial Index!)."""
        query = select(self.model).where(self.model.is_anomalous.is_(True))
        result = await self.session.execute(query)
        return result.scalars().all()