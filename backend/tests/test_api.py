# pyrefly: ignore [missing-import]
import pytest
# pyrefly: ignore [missing-import]
from httpx import AsyncClient
from tests.conftest import TEST_TENANT_ID

# Mark all tests in this file as async so pytest handles await calls correctly
pytestmark = pytest.mark.asyncio


async def test_health_check(async_client: AsyncClient):
    """Test that the /health endpoint returns ONLINE status."""
    response = await async_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ONLINE"
    assert data["project"] == "Taxon API"


async def test_tally_natural_language_query(async_client: AsyncClient):
    """Test that Tally-Bridge translates English queries and returns 201 Created."""
    payload = {
        "tenant_id": TEST_TENANT_ID,
        "query": "Find all cash payments over Rs 10000 made to unregistered vendors"
    }
    
    response = await async_client.post("/api/v1/tally/query-nl", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "COMPLETED"
    assert data["circuit_breaker_state"] == "CLOSED"
    assert "<ENVELOPE>" in data["tdl_query_xml"]  # Verifies TDL XML was generated!


async def test_tds_ledger_anomaly_detection(async_client: AsyncClient):
    """Test that TDS-Align flags a 90% under-deduction error as anomalous."""
    payload = {
        "tenant_id": TEST_TENANT_ID,
        "pan": "ABCDE1234F",
        "section": "194C",
        "amount_paid": 100000.00,
        "tds_deducted": 100.00  # Intentional error to trigger Autoencoder flag
    }
    
    response = await async_client.post("/api/v1/tds/inspect-ledger", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["is_anomalous"] is True
    assert data["reconstruction_loss"] > 0.15  # Ensures MSE loss threshold tripped
    assert "PAN" in data["rag_rectification_draft"]  # Verifies RAG letter was drafted!


async def test_ims_invoice_reconciliation_default_vector(async_client: AsyncClient):
    """Test Auto-IMS reconciliation using Pydantic's default 1536-dim vector."""
    payload = {
        "tenant_id": TEST_TENANT_ID,
        "doc_no": "INV-PYTEST-001",
        "amount": 75000.00,
        "gst_amount": 13500.00
        # Omitting vector_embed so schema generates valid 1536-dim array
    }
    
    response = await async_client.post("/api/v1/ims/reconcile-single", json=payload)
    print(response.text)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "PENDING"  # Correct behavior when no GSTR-2B match exists
    assert data["cgst_17_5_flag"] is False