# tests/conftest.py
from collections.abc import AsyncGenerator
# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
import pytest_asyncio
# pyrefly: ignore [missing-import]
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.core.database import engine

# Fixed UUID for our test tenant so all tests use the same CA firm ID
TEST_TENANT_ID = "11111111-1111-1111-1111-111111111111"


@pytest_asyncio.fixture(scope="function")
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create a fresh async HTTP client for each individual test function.

    Why function scope?
    1. Prevents anyio and ASGITransport from closing their internal communication
       pipes ('NoneType has no attribute send') between tests.
    2. Ensures every test starts with a clean slate.
    """
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport, base_url="http://test"
    ) as client:
        yield client

    # Cleanly dispose of any lingering asyncpg database connections
    # so the next test gets a fresh, unblocked connection pool!
    await engine.dispose()