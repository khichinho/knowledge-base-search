import contextlib
import io
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from chromadb.config import Settings as ChromaSettings
from sentence_transformers import SentenceTransformer

# Disable HuggingFace tokenizers parallelism warnings
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Suppress ChromaDB telemetry errors - must be before importing chromadb
# Create a null handler to discard all messages
null_handler = logging.NullHandler()

# Suppress all ChromaDB-related loggers
for logger_name in [
    "chromadb",
    "posthog",
    "chromadb.telemetry",
    "chromadb.telemetry.product.posthog",
]:
    logger = logging.getLogger(logger_name)
    logger.setLevel(logging.CRITICAL)
    logger.propagate = False
    logger.addHandler(null_handler)

# Suppress ChromaDB telemetry errors during import
with contextlib.redirect_stderr(io.StringIO()):
    import chromadb


class VectorStore:
    """
    Manages vector embeddings and similarity search using ChromaDB.
    Supports incremental updates and efficient querying.
    """

    def __init__(self, persist_directory: str, embedding_model_name: str):
        """
        Initialize the vector store.

        Args:
            persist_directory: Directory to persist the database
            embedding_model_name: Name of the sentence-transformers model
        """
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Initialize ChromaDB with persistence and telemetry disabled
        # Suppress stderr during initialization to avoid telemetry errors
        with contextlib.redirect_stderr(io.StringIO()):
            self.client = chromadb.Client(
                ChromaSettings(
                    persist_directory=persist_directory,
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )

        # Get or create collection - suppress stderr during creation
        with contextlib.redirect_stderr(io.StringIO()):
            self.collection = self.client.get_or_create_collection(
                name="documents", metadata={"hnsw:space": "cosine"}
            )

    def add_documents(self, chunks: List[Dict[str, Any]], document_id: str) -> int:
        """
        Add document chunks to the vector store.

        Args:
            chunks: List of text chunks with metadata
            document_id: Unique document identifier

        Returns:
            Number of chunks added
        """
        if not chunks:
            return 0

        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.embedding_model.encode(texts, convert_to_numpy=True).tolist()

        # Generate unique IDs for each chunk
        chunk_ids = [f"{document_id}_chunk_{i}" for i in range(len(chunks))]

        # Prepare metadata
        metadatas = []
        for i, chunk in enumerate(chunks):
            metadata = chunk.get("metadata", {})
            metadata.update(
                {
                    "document_id": document_id,
                    "chunk_index": i,
                    "added_at": datetime.utcnow().isoformat(),
                }
            )
            metadatas.append(metadata)

        # Add to collection
        self.collection.add(
            ids=chunk_ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )

        return len(chunks)

    def search(
        self, query: str, top_k: int = 5, filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search.

        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters

        Returns:
            List of search results with scores
        """
        # Generate query embedding
        query_embedding = self.embedding_model.encode(query, convert_to_numpy=True).tolist()

        # Prepare where clause for filtering
        where = filter_metadata if filter_metadata else None

        # Perform search
        results = self.collection.query(
            query_embeddings=[query_embedding], n_results=top_k, where=where
        )

        # Format results
        formatted_results = []
        if results["ids"] and results["ids"][0]:
            for i in range(len(results["ids"][0])):
                formatted_results.append(
                    {
                        "chunk_id": results["ids"][0][i],
                        "content": results["documents"][0][i],
                        "metadata": results["metadatas"][0][i],
                        "distance": results["distances"][0][i] if "distances" in results else None,
                    }
                )

        return formatted_results

    def delete_document(self, document_id: str) -> int:
        """
        Delete all chunks belonging to a document (supports incremental updates).

        Args:
            document_id: Document identifier

        Returns:
            Number of chunks deleted
        """
        # Find all chunks for this document
        results = self.collection.get(where={"document_id": document_id})

        if results["ids"]:
            self.collection.delete(ids=results["ids"])
            return len(results["ids"])

        return 0

    def get_document_count(self) -> int:
        """Get total number of unique documents."""
        all_data = self.collection.get()
        if not all_data["metadatas"]:
            return 0

        unique_docs = set(meta.get("document_id") for meta in all_data["metadatas"])
        return len(unique_docs)

    def get_chunk_count(self) -> int:
        """Get total number of chunks."""
        return self.collection.count()

    def get_collection_status(self) -> Dict[str, Any]:
        """Get collection statistics."""
        return {
            "total_chunks": self.get_chunk_count(),
            "total_documents": self.get_document_count(),
            "embedding_dimension": self.embedding_model.get_sentence_embedding_dimension(),
        }
