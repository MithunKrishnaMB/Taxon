import uuid
from collections.abc import Sequence
from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base

# TypeT represents any of our SQLAlchemy model classes (Tenant, ErpInvoice, etc.)
ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic CRUD repository for asynchronous database operations.

    Why we use this:
    It provides standard Create, Read, Update and Delete methods automatically
    for any model class we pass to it, keeping code clean and DRY (Don't Repeat Yourself).
    """

    def __init__(self, model: type[ModelType], session: AsyncSession):
        self.model = model
        self.session = session

    async def get_by_id(self, record_id: uuid.UUID) -> ModelType | None:
        """Fetch a single record by its UUID primary key."""
        return await self.session.get(self.model, record_id)

    async def get_all_by_tenant(
        self, tenant_id: uuid.UUID, limit: int = 100, offset: int = 0
    ) -> Sequence[ModelType]:
        """Fetch all records belonging to a specific CA/Tenant with pagination."""
        query = (
            select(self.model)
            .where(self.model.tenant_id == tenant_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def create(self, attributes: dict[str, Any]) -> ModelType:
        """Create a new record in the database."""
        instance = self.model(**attributes)
        self.session.add(instance)
        await self.session.flush()  # Push to Postgres to generate UUIDs without committing
        await self.session.refresh(instance)
        return instance