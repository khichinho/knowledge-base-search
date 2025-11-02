from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_llm_service, get_vector_store
from app.schemas import CompletenessQuery, CompletenessResult

router = APIRouter(prefix="/completeness", tags=["Analysis"])


@router.post("", response_model=CompletenessResult)
async def check_completeness(
    query: CompletenessQuery,
    vector_store=Depends(get_vector_store),
    llm_service=Depends(get_llm_service),
):
    """
    Check if the knowledge base has sufficient information on a topic.
    Useful for identifying gaps in documentation.
    """
    try:
        # Search for relevant documents
        context_results = vector_store.search(
            query=query.topic, top_k=10  # Use more context for completeness check
        )

        if not context_results:
            return CompletenessResult(
                topic=query.topic,
                overall_score=0.0,
                has_sufficient_info=False,
                covered_aspects=[],
                missing_aspects=["No documents found related to this topic"],
                recommendations=["Upload relevant documents to build knowledge base"],
                supporting_documents=[],
            )

        # Use LLM to assess completeness
        assessment = llm_service.check_completeness(
            topic=query.topic,
            context_chunks=context_results,
            required_aspects=query.required_aspects,
        )

        # Extract supporting documents
        supporting_docs = list(
            set(
                result["metadata"].get("filename", "unknown")
                for result in context_results
            )
        )

        return CompletenessResult(
            topic=query.topic,
            overall_score=assessment["score"],
            has_sufficient_info=assessment["score"] >= 0.7,
            covered_aspects=assessment["covered_aspects"],
            missing_aspects=assessment["missing_aspects"],
            recommendations=assessment["recommendations"],
            supporting_documents=supporting_docs,
        )

    except Exception as e:
        error_msg = str(e)
        # Check for OpenAI API errors
        if "RateLimitError" in error_msg or "rate_limit" in error_msg.lower():
            detail = (
                "OpenAI API rate limit exceeded.\n"
                "Please wait a moment and try again,\n"
                "or check your rate limits at https://platform.openai.com/account/rate-limits"
            )
        elif "quota" in error_msg.lower() or "billing" in error_msg.lower():
            detail = (
                "OpenAI API quota exceeded.\n"
                "Please set up billing or increase your\n"
                "spending limit at https://platform.openai.com/account/billing"
            )
        else:
            detail = f"Completeness check failed: {error_msg}"

        raise HTTPException(status_code=503, detail=detail)
