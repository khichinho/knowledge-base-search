import time

from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_settings, get_vector_store
from app.schemas import SearchQuery, SearchResponse, SearchResult

router = APIRouter(prefix="/search", tags=["Search"])


@router.post("", response_model=SearchResponse)
async def semantic_search(
    query: SearchQuery,
    vector_store=Depends(get_vector_store),
    settings=Depends(get_settings),
):
    """
    Perform semantic search across all documents.
    Returns most relevant text chunks.
    """
    start_time = time.time()

    try:
        # Perform vector search
        results = vector_store.search(
            query=query.query,
            top_k=query.top_k or settings.top_k_results,
            filter_metadata=query.filter_metadata,
        )

        # Format results
        search_results = []
        for result in results:
            search_results.append(
                SearchResult(
                    chunk_id=result["chunk_id"],
                    document_id=result["metadata"].get("document_id", "unknown"),
                    filename=result["metadata"].get("filename", "unknown"),
                    content=result["content"],
                    score=(
                        1.0 - result["distance"] if result.get("distance") else 0.0
                    ),  # Convert distance to similarity
                    metadata=result["metadata"],
                )
            )

        processing_time = (time.time() - start_time) * 1000  # Convert to ms

        return SearchResponse(
            query=query.query,
            results=search_results,
            total_results=len(search_results),
            processing_time_ms=round(processing_time, 2),
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")
