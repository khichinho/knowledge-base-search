"""
Pytest configuration and fixtures for testing.
"""
import contextlib
import io
import tempfile
import uuid
from pathlib import Path

import chromadb
import pytest
from fastapi.testclient import TestClient

from app.api import dependencies
from app.core.config import get_settings
from app.main import app
from app.services import DocumentProcessor, LLMService, VectorStore


@pytest.fixture(scope="function")
def temp_dirs():
    """Create temporary directories for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_dir = Path(tmpdir) / "uploads"
        # Use unique directory name to avoid ChromaDB client caching issues
        chroma_dir = Path(tmpdir) / f"chroma_db_{uuid.uuid4().hex[:8]}"
        upload_dir.mkdir(parents=True, exist_ok=True)
        chroma_dir.mkdir(parents=True, exist_ok=True)
        yield str(upload_dir), str(chroma_dir)


@pytest.fixture(scope="function")
def initialized_services(temp_dirs):
    """Initialize services for testing."""
    # Clear ChromaDB client cache before each test
    try:
        if hasattr(chromadb.Client, "_identifer_to_system"):
            chromadb.Client._identifer_to_system.clear()
        # Also try SharedSystemClient
        from chromadb.api.client import SharedSystemClient

        if hasattr(SharedSystemClient, "_identifer_to_system"):
            SharedSystemClient._identifer_to_system.clear()
    except (AttributeError, ImportError):
        pass

    upload_dir, chroma_dir = temp_dirs
    settings = get_settings()

    # Override settings with temp directories
    settings.upload_dir = upload_dir
    settings.chroma_persist_dir = chroma_dir

    # Initialize document processor
    document_processor = DocumentProcessor(
        chunk_size=settings.chunk_size, chunk_overlap=settings.chunk_overlap
    )
    dependencies.set_document_processor(document_processor)

    # Initialize vector store - suppress stderr during initialization
    with contextlib.redirect_stderr(io.StringIO()):
        vector_store = VectorStore(
            persist_directory=settings.chroma_persist_dir,
            embedding_model_name=settings.embedding_model,
        )
    dependencies.set_vector_store(vector_store)

    # Initialize LLM service
    llm_service = LLMService(
        api_key=settings.openai_api_key or "test-key",
        model=settings.llm_model,
        max_tokens=settings.max_tokens,
        temperature=settings.temperature,
    )
    dependencies.set_llm_service(llm_service)

    yield

    # Cleanup - reset ChromaDB client cache
    try:
        # Clear ChromaDB client cache between tests
        chromadb.Client._identifer_to_system.clear()
    except AttributeError:
        pass

    # Cleanup services
    dependencies.set_document_processor(None)
    dependencies.set_vector_store(None)
    dependencies.set_llm_service(None)


@pytest.fixture(scope="function")
def client(initialized_services):
    """Create a test client with initialized services."""
    return TestClient(app)
