from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.tally_bridge.models import TallySyncJob


class TallyJobRepository(BaseRepository[TallySyncJob]):
    def __init__(self, session: AsyncSession):
        super().__init__(TallySyncJob, session)