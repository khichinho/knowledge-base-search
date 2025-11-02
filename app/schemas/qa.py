from typing import List, Optional

from pydantic import BaseModel, Field


class QAQuery(BaseModel):
    """Question-answering query."""

    question: str = Field(
        ...,
        min_length=1,
        description="Question to answer",
        example="What are REST APIs and how do they work?",
    )
    top_k: Optional[int] = Field(5, ge=1, le=10, description="Number of context chunks to use")


class SourceCitation(BaseModel):
    """Source citation for an answer."""

    document_id: str = Field(..., example="doc123")
    filename: str = Field(..., example="web_development_basics.txt")
    chunk_content: str = Field(..., example="REST APIs are a way to...")
    relevance_score: float = Field(..., ge=0.0, le=1.0, example=0.85)


class QAResponse(BaseModel):
    """Question-answering response."""

    question: str = Field(..., example="What are REST APIs and how do they work?")
    answer: str = Field(
        ...,
        example="REST APIs (Representational State Transfer) are a set of architectural principles for building web services...",
    )
    sources: List[SourceCitation] = Field(..., example=[])
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.92)
    processing_time_ms: float = Field(..., example=1250.5)
