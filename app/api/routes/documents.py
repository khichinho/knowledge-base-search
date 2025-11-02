import os
import uuid
from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, File, HTTPException, UploadFile

from app.api.dependencies import (
    get_document_processor,
    get_documents_db,
    get_settings,
    get_vector_store,
)
from app.schemas import DocumentListResponse, DocumentMetadata, DocumentStatus, UploadResponse

router = APIRouter(prefix="/documents", tags=["Documents"])


def process_document_background(
    document_id: str,
    file_path: str,
    filename: str,
    content_type: str,
    document_processor,
    vector_store,
    documents_db,
):
    """Background task to process uploaded document."""
    try:
        # Update status to processing
        documents_db[document_id].status = DocumentStatus.PROCESSING

        # Extract text
        text = document_processor.extract_text(file_path, content_type)

        # Create chunks
        chunks = document_processor.chunk_text(
            text,
            {
                "document_id": document_id,
                "filename": filename,
                "content_type": content_type,
            },
        )

        # Add to vector store
        chunk_count = vector_store.add_documents(chunks, document_id)

        # Update metadata
        documents_db[document_id].status = DocumentStatus.COMPLETED
        documents_db[document_id].chunk_count = chunk_count

        print(f"✓ Processed document {filename}: {chunk_count} chunks")

    except Exception as e:
        documents_db[document_id].status = DocumentStatus.FAILED
        documents_db[document_id].error_message = str(e)
        print(f"✗ Failed to process document {filename}: {str(e)}")


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    settings=Depends(get_settings),
    document_processor=Depends(get_document_processor),
    vector_store=Depends(get_vector_store),
    documents_db=Depends(get_documents_db),
):
    """
    Upload a document for ingestion.
    Supports PDF, DOCX, and TXT files.
    """
    # Validate file type
    allowed_types = [
        "application/pdf",
        "text/plain",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]

    if file.content_type not in allowed_types and not any(
        file.filename.endswith(ext) for ext in [".pdf", ".txt", ".docx", ".doc"]
    ):
        raise HTTPException(
            status_code=400, detail="Unsupported file type. Allowed: PDF, TXT, DOCX"
        )

    # Generate unique document ID
    document_id = str(uuid.uuid4())

    # Save file
    file_path = os.path.join(settings.upload_dir, f"{document_id}_{file.filename}")

    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # Create metadata
        metadata = DocumentMetadata(
            id=document_id,
            filename=file.filename,
            file_size=len(content),
            content_type=file.content_type or "application/octet-stream",
            uploaded_at=datetime.utcnow(),
            status=DocumentStatus.PENDING,
        )

        documents_db[document_id] = metadata

        # Process document in background
        background_tasks.add_task(
            process_document_background,
            document_id,
            file_path,
            file.filename,
            file.content_type or "",
            document_processor,
            vector_store,
            documents_db,
        )

        return UploadResponse(
            document_id=document_id,
            filename=file.filename,
            message="Document uploaded successfully. Processing in background.",
            status=DocumentStatus.PENDING,
        )

    except Exception as e:
        # Clean up on error
        if os.path.exists(file_path):
            os.remove(file_path)
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("", response_model=DocumentListResponse)
async def list_documents(documents_db=Depends(get_documents_db)):
    """List all uploaded documents."""
    return DocumentListResponse(
        documents=list(documents_db.values()), total_count=len(documents_db)
    )


@router.get("/{document_id}", response_model=DocumentMetadata)
async def get_document_status(document_id: str, documents_db=Depends(get_documents_db)):
    """Get status of a specific document."""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    return documents_db[document_id]


@router.delete("/{document_id}")
async def delete_document(
    document_id: str,
    settings=Depends(get_settings),
    vector_store=Depends(get_vector_store),
    documents_db=Depends(get_documents_db),
):
    """Delete a document and its embeddings (supports incremental updates)."""
    if document_id not in documents_db:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        # Delete from vector store
        deleted_count = vector_store.delete_document(document_id)

        # Delete file
        metadata = documents_db[document_id]
        file_path = os.path.join(settings.upload_dir, f"{document_id}_{metadata.filename}")
        if os.path.exists(file_path):
            os.remove(file_path)

        # Remove from metadata
        del documents_db[document_id]

        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "chunks_deleted": deleted_count,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")
