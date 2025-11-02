import re
from typing import Any, Dict, List

import docx
import PyPDF2


class DocumentProcessor:
    """Handles document parsing and text extraction."""

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def extract_text(self, file_path: str, content_type: str) -> str:
        """
        Extract text from various document formats.

        Args:
            file_path: Path to the document
            content_type: MIME type of the document

        Returns:
            Extracted text content
        """
        if content_type == "application/pdf" or file_path.endswith(".pdf"):
            return self._extract_from_pdf(file_path)
        elif content_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ] or file_path.endswith((".docx", ".doc")):
            return self._extract_from_docx(file_path)
        elif content_type.startswith("text/") or file_path.endswith(".txt"):
            return self._extract_from_txt(file_path)
        else:
            # Fallback: try to read as text
            return self._extract_from_txt(file_path)

    def _extract_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF files."""
        text = []
        try:
            with open(file_path, "rb") as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _extract_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX files."""
        try:
            doc = docx.Document(file_path)
            text = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text.append(paragraph.text)
            return "\n".join(text)
        except Exception as e:
            raise ValueError(f"Failed to extract text from DOCX: {str(e)}")

    def _extract_from_txt(self, file_path: str) -> str:
        """Extract text from plain text files."""
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return file.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, "r", encoding="latin-1") as file:
                return file.read()
        except Exception as e:
            raise ValueError(f"Failed to extract text from file: {str(e)}")

    def chunk_text(self, text: str, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Split text into overlapping chunks for better context preservation.

        Args:
            text: Full document text
            metadata: Document metadata to attach to chunks

        Returns:
            List of chunks with metadata
        """
        # Clean and normalize text
        text = self._clean_text(text)

        # Split into sentences for better chunk boundaries
        sentences = self._split_into_sentences(text)

        chunks = []
        current_chunk = []
        current_length = 0

        for sentence in sentences:
            sentence_length = len(sentence)

            # If adding this sentence exceeds chunk size, save current chunk
            if current_length + sentence_length > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk)
                chunks.append(
                    {
                        "content": chunk_text,
                        "metadata": {
                            **metadata,
                            "chunk_index": len(chunks),
                            "char_count": len(chunk_text),
                        },
                    }
                )

                # Keep last few sentences for overlap
                overlap_sentences = []
                overlap_length = 0

                # Build overlap from the end
                for s in reversed(current_chunk):
                    if overlap_length + len(s) <= self.chunk_overlap:
                        overlap_sentences.insert(0, s)
                        overlap_length += len(s)
                    else:
                        break

                current_chunk = overlap_sentences
                current_length = overlap_length

            current_chunk.append(sentence)
            current_length += sentence_length

        # Add the last chunk
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            chunks.append(
                {
                    "content": chunk_text,
                    "metadata": {
                        **metadata,
                        "chunk_index": len(chunks),
                        "char_count": len(chunk_text),
                    },
                }
            )

        return chunks

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text)
        # Remove special characters but keep punctuation
        text = re.sub(r"[^\w\s\.\,\!\?\;\:\-\(\)\[\]\{\}\"\']+", "", text)
        return text.strip()

    def _split_into_sentences(self, text: str) -> List[str]:
        """Split text into sentences using simple heuristics."""
        # Simple sentence splitting (can be improved with NLTK for production)
        sentences = re.split(r"(?<=[.!?])\s+", text)
        return [s.strip() for s in sentences if s.strip()]
