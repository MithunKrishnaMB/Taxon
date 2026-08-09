import asyncio
from app.core.database import AsyncSessionLocal
from sqlalchemy import text

async def update_enum():
    async with AsyncSessionLocal() as session:
        try:
            # First, check if we need to manually bypass the transaction block error that sometimes happens with ALTER TYPE
            # PostgreSQL requires ALTER TYPE to be outside a transaction block if possible, or commit it explicitly.
            # Usually `await session.commit()` works, but let's try raw execute with autocommit on the connection if needed.
            await session.execute(text("ALTER TYPE ingestion_status_enum ADD VALUE 'RECONCILING' AFTER 'EMBEDDING'"))
            await session.commit()
            print('Enum updated successfully')
        except Exception as e:
            if "DuplicateObject" in str(e) or "already exists" in str(e):
                print("Enum value already exists")
            else:
                print('Error updating enum:', e)

if __name__ == "__main__":
    asyncio.run(update_enum())
