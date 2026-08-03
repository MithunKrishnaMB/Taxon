from collections.abc import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# 1. Create the Asynchronous Engine using asyncpg
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True if you want to see raw SQL logs during debug
    future=True,
    pool_size=20,
    max_overflow=10,
)

# 2. Configure the Async Session Factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


# 3. Modern SQLAlchemy 2.0 Base Class for ORM Models
class Base(DeclarativeBase):
    pass


# 4. FastAPI Dependency to yield database sessions per request
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()