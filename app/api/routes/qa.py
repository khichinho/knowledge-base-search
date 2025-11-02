import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_llm_service, get_settings, get_vector_store
from app.core.config import Settings
from app.schemas import QAQuery, QAResponse, SourceCitation
from app.services import LLMService, VectorStore

router = APIRouter(prefix="/qa", tags=["Q&A"])


@router.post("", response_model=QAResponse)
async def question_answering(
    query: QAQuery,
    vector_store: VectorStore = Depends(get_vector_store),
    llm_service: LLMService = Depends(get_llm_service),
    settings: Settings = Depends(get_settings),
):
    """
    Answer questions using Retrieval-Augmented Generation (RAG).
    Retrieves relevant context and generates an answer with citations.
    """
    start_time = time.time()

    try:
        # Retrieve relevant context
        context_results = vector_store.search(
            query=query.question, top_k=query.top_k or settings.top_k_results
        )

        if not context_results:
            raise HTTPException(
                status_code=404,
                detail=("No relevant documents found. " "Please upload documents first."),
            )

        # Generate answer using LLM
        answer, confidence = llm_service.answer_question(
            question=query.question, context_chunks=context_results
        )

        # Build source citations
        sources = []
        for result in context_results:
            # Get metadata
            metadata = result["metadata"]
            doc_id = metadata.get("document_id", "unknown")
            filename = metadata.get("filename", "unknown")

            # Calculate relevance score
            distance = result.get("distance", 0.0)
            relevance = 1.0 - distance if distance else 0.0

            # Create citation with truncated content
            content = result["content"][:200] + "..."  # Truncate for brevity

            sources.append(
                SourceCitation(
                    document_id=doc_id,
                    filename=filename,
                    chunk_content=content,
                    relevance_score=relevance,
                )
            )

        processing_time = (time.time() - start_time) * 1000

        return QAResponse(
            question=query.question,
            answer=answer,
            sources=sources,
            confidence=confidence,
            processing_time_ms=round(processing_time, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Q&A failed: {str(e)}")
