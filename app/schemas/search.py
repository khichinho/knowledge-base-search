from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query request."""

    query: str = Field(
        ...,
        min_length=1,
        description="Search query text",
        example="What is machine learning?",
    )
    top_k: Optional[int] = Field(
        5, ge=1, le=20, description="Number of results to return", example=3
    )
    filter_metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Optional metadata filters (e.g., filter by filename)",
        example={"filename": "machine_learning_guide.pdf"},
    )


class SearchResult(BaseModel):
    """Individual search result."""

    chunk_id: str = Field(..., example="doc123_chunk_0")
    document_id: str = Field(..., example="doc123")
    filename: str = Field(..., example="machine_learning_guide.pdf")
    content: str = Field(..., example="Machine Learning is a subset of AI...")
    score: float = Field(..., ge=0.0, le=1.0, example=0.827)
    metadata: Dict[str, Any] = Field(
        ..., example={"chunk_index": 0, "added_at": "2025-11-02T06:25:45"}
    )


class SearchResponse(BaseModel):
    """Search results response."""

    query: str = Field(..., example="What is machine learning?")
    results: List[SearchResult] = Field(..., example=[])
    total_results: int = Field(..., example=3, description="Number of results returned")
    processing_time_ms: float = Field(
        ..., example=49.02, description="Query processing time in milliseconds"
    )
