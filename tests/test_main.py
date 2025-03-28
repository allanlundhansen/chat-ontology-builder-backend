import pytest
import pytest_asyncio
from httpx import AsyncClient

@pytest.mark.asyncio
async def test_read_root(async_client: AsyncClient):
    """ Tests the root welcome endpoint. """
    print("\nTesting GET /")
    response = await async_client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the Chat Ontology Builder API"}

@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient):
    """ Tests the health check endpoint. """
    print("\nTesting GET /health")
    response = await async_client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"} 