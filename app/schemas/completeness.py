from typing import List, Optional

from pydantic import BaseModel, Field


class CompletenessQuery(BaseModel):
    """Completeness check query."""

    topic: str = Field(
        ...,
        min_length=1,
        description="Topic to check coverage for",
        example="deep learning",
    )
    required_aspects: Optional[List[str]] = Field(
        None,
        description="Specific aspects to verify",
        example=["neural networks", "training methods", "applications"],
    )


class CompletenessResult(BaseModel):
    """Completeness assessment result."""

    topic: str = Field(..., example="deep learning")
    overall_score: float = Field(..., ge=0.0, le=1.0, example=0.75)
    has_sufficient_info: bool = Field(..., example=True)
    covered_aspects: List[str] = Field(..., example=["neural networks", "applications"])
    missing_aspects: List[str] = Field(..., example=["training methods"])
    recommendations: List[str] = Field(
        ...,
        example=[
            "Add more information about backpropagation",
            "Include details on different activation functions",
        ],
    )
    supporting_documents: List[str] = Field(
        ..., example=["machine_learning_guide.pdf", "introduction_to_ai.docx"]
    )
