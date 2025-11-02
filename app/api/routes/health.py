from fastapi import APIRouter, Depends, HTTPException

from app.api.dependencies import get_settings, get_vector_store
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/")
async def root(settings=Depends(get_settings)):
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(
    vector_store=Depends(get_vector_store),
    settings=Depends(get_settings),
):
    """Health check endpoint with system status."""
    try:
        if vector_store is None:
            raise ValueError("Vector store not initialized")

        try:
            stats = vector_store.get_collection_status()
        except Exception as e:
            raise ValueError(f"Vector store error: {str(e)}")

        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            vector_db_status="connected",
            total_documents=stats["total_documents"],
            total_chunks=stats["total_chunks"],
        )
    except Exception as e:
        import traceback

        error_details = f"{str(e)}\n{traceback.format_exc()}"
        print(f"Health check error: {error_details}")  # For debugging
        raise HTTPException(
            status_code=503,
            detail=f"Service unhealthy: {str(e)}",
        )
