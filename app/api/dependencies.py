"""
Dependency injection for FastAPI routes.
Provides access to services and shared state.
"""
from typing import Dict

from app.core.config import Settings
from app.core.config import get_settings as config_get_settings
from app.schemas import DocumentMetadata
from app.services import DocumentProcessor, LLMService, VectorStore

# Global state (in production, use a proper database)
documents_db: Dict[str, DocumentMetadata] = {}

# Service instances (initialized in main.py startup)
_document_processor = None
_vector_store = None
_llm_service = None
_settings: Settings = None


def set_document_processor(processor: DocumentProcessor):
    """Set the document processor instance."""
    global _document_processor
    _document_processor = processor


def set_vector_store(store: VectorStore):
    """Set the vector store instance."""
    global _vector_store
    _vector_store = store
    # Allow None for cleanup in tests


def set_llm_service(service: LLMService):
    """Set the LLM service instance."""
    global _llm_service
    _llm_service = service


def get_document_processor() -> DocumentProcessor:
    """Get the document processor dependency."""
    if _document_processor is None:
        raise RuntimeError("Document processor not initialized")
    return _document_processor


def get_vector_store() -> VectorStore:
    """Get the vector store dependency."""
    if _vector_store is None:
        raise RuntimeError("Vector store not initialized")
    return _vector_store


def get_llm_service() -> LLMService:
    """Get the LLM service dependency."""
    if _llm_service is None:
        raise RuntimeError("LLM service not initialized")
    return _llm_service


def get_documents_db() -> Dict[str, DocumentMetadata]:
    """Get the documents database dependency."""
    return documents_db


def get_settings() -> Settings:
    """Get application settings."""
    global _settings
    if _settings is None:
        _settings = config_get_settings()
    return _settings
