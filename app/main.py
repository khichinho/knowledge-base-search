import os
import warnings
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import dependencies
from app.api.routes import completeness, documents, health, qa, search
from app.core.config import get_settings
from app.services import DocumentProcessor, LLMService, VectorStore

# Disable HuggingFace tokenizers parallelism warnings
# (must be before any imports)
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress ChromaDB telemetry warnings
warnings.filterwarnings("ignore", category=UserWarning, module="chromadb")

# Initialize settings
settings = get_settings()

# Initialize FastAPI app
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AI-Powered Knowledge Base Search & Enrichment API",
)


@app.get("/")
async def root():
    """Root endpoint."""
    return {"message": "Knowledge Base API is running"}


# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(qa.router)
app.include_router(completeness.router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    # Create necessary directories
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    Path(settings.chroma_persist_dir).mkdir(parents=True, exist_ok=True)

    # Initialize document processor
    document_processor = DocumentProcessor(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    dependencies.set_document_processor(document_processor)

    # Initialize vector store - suppress stderr during initialization
    import contextlib
    import io

    with contextlib.redirect_stderr(io.StringIO()):
        vector_store = VectorStore(
            persist_directory=settings.chroma_persist_dir,
            embedding_model_name=settings.embedding_model,
        )
    dependencies.set_vector_store(vector_store)

    # Initialize LLM service
    llm_service = LLMService(
        api_key=settings.openai_api_key,
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
    )
    dependencies.set_llm_service(llm_service)

    print(f"✓ {settings.app_name} started successfully")
    print("✓ API Documentation: http://localhost:8000/docs")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
