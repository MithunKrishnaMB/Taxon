import uuid
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.ingestion.models import IngestionJob, IngestionStatus


class IngestionJobRepository(BaseRepository[IngestionJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(IngestionJob, session)

    async def get_by_id(self, job_id: uuid.UUID) -> IngestionJob | None:
        """Fetch a specific ingestion job ticket by its ID."""
        query = select(IngestionJob).where(IngestionJob.id == job_id)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def list_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 20
    ) -> list[IngestionJob]:
        """Fetch the most recent ingestion jobs for a specific Client Company."""
        query = (
            select(IngestionJob)
            .where(IngestionJob.tenant_id == tenant_id)
            .order_by(IngestionJob.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_progress(
        self,
        job_id: uuid.UUID,
        processed_delta: int,
        status: IngestionStatus | None = None,
        error_message: str | None = None,
    ) -> None:
        """Atomically increment processed_rows and update the status badge."""
        stmt = (
            update(IngestionJob)
            .where(IngestionJob.id == job_id)
            .values(
                processed_rows=IngestionJob.processed_rows + processed_delta,
                **({"status": status} if status else {}),
                **({"error_message": error_message} if error_message else {}),
            )
        )
        await self.session.execute(stmt)
        await self.session.commit()