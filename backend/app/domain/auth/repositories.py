import uuid
from typing import Sequence
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repository import BaseRepository
from app.domain.auth.models import CAFirm, CAUser


class CAFirmRepository(BaseRepository[CAFirm]):
    def __init__(self, session: AsyncSession):
        super().__init__(CAFirm, session)

    async def get_by_name(self, name: str) -> CAFirm | None:
        """Check if an accounting firm with this legal name already exists."""
        query = select(CAFirm).where(CAFirm.name == name)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()


class CAUserRepository(BaseRepository[CAUser]):
    def __init__(self, session: AsyncSession):
        super().__init__(CAUser, session)

    async def get_by_email(self, email: str) -> CAUser | None:
        """Look up an accountant by their login email address."""
        query = select(CAUser).where(CAUser.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def get_users_by_firm(self, firm_id: uuid.UUID) -> Sequence[CAUser]:
        """Fetch all users belonging to a specific CA Firm."""
        query = select(CAUser).where(CAUser.firm_id == firm_id)
        result = await self.session.execute(query)
        return result.scalars().all()