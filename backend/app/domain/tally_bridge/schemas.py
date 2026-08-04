import uuid
from pydantic import BaseModel, Field
from app.domain.tally_bridge.models import CircuitBreakerState, JobStatus


class NaturalLanguageQueryRequest(BaseModel):
    """Request payload containing an English audit question."""
    tenant_id: uuid.UUID
    query: str = Field(
        ...,
        example="Find all cash payments over Rs 10000 made to unregistered vendors"
    )


class TallyJobResponse(BaseModel):
    """Response returning the generated Tally XML and Circuit Breaker health."""
    id: uuid.UUID
    status: JobStatus
    circuit_breaker_state: CircuitBreakerState
    tdl_query_xml: str

    class Config:
        from_attributes = True