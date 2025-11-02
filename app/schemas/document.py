from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel


class DocumentStatus(str, Enum):
    """Document processing status."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class DocumentMetadata(BaseModel):
    """Metadata for uploaded documents."""

    id: str
    filename: str
    file_size: int
    content_type: str
    uploaded_at: datetime
    status: DocumentStatus
    chunk_count: Optional[int] = None
    error_message: Optional[str] = None


class UploadResponse(BaseModel):
    """Response after document upload."""

    document_id: str
    filename: str
    message: str
    status: DocumentStatus


class DocumentListResponse(BaseModel):
    """List of documents."""

    documents: List[DocumentMetadata]
    total_count: int
