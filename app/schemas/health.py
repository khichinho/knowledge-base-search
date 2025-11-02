from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    version: str
    vector_db_status: str
    total_documents: int
    total_chunks: int
