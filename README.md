# AI-Powered Knowledge Base

Semantic search and question-answering system built with FastAPI, ChromaDB, and OpenAI.

## Features

- **Document Ingestion** - Upload PDF, DOCX, and TXT files (multi-format support)
- **Semantic Search** - Natural language queries across documents
- **RAG Q&A** - Get answers with source citations
- **Completeness Check** - Assess knowledge base coverage
- **Incremental Updates** - Add/delete documents without reindexing

## Quick Start

```bash
# Install Poetry if needed
curl -sSL https://install.python-poetry.org | python3 -

# Install dependencies
poetry install

# Add your OpenAI API key to .env
echo "OPENAI_API_KEY=sk-your-key" > .env

# Run server
poetry run uvicorn app.main:app --reload
```

Visit http://localhost:8000/docs for API documentation.

## Architecture

```
app/
├── api/          # Route handlers
├── core/         # Configuration
├── schemas/      # Request/response models
├── services/     # Business logic
└── models/       # Database models (future)
```

**Tech Stack:**
- FastAPI for async API
- ChromaDB for vector storage
- Sentence-Transformers for local embeddings
- OpenAI GPT-3.5 for Q&A
- Poetry for dependency management

## API Endpoints

- `POST /documents/upload` - Upload document
- `GET /documents` - List documents
- `DELETE /documents/{id}` - Delete document
- `POST /search` - Semantic search
- `POST /qa` - Question answering
- `POST /completeness` - Check topic coverage
- `GET /health` - System status

## Usage Examples

### Upload Document
```bash
curl -X POST "http://localhost:8000/documents/upload" \
  -F "file=@document.pdf"
```

### Search
```bash
curl -X POST "http://localhost:8000/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?", "top_k": 5}'
```

### Ask Question
```bash
curl -X POST "http://localhost:8000/qa" \
  -H "Content-Type: application/json" \
  -d '{"question": "Explain neural networks"}'
```

## Design Decisions

**ChromaDB** - Local vector DB, easy setup, good for thousands of documents. Would use Pinecone for millions.

**Local Embeddings** - Sentence-transformers (all-MiniLM-L6-v2) for speed and cost. No API calls for search.

**Chunking** - Fixed 500 char chunks with 50 char overlap. Keeps context, works for most content. Could improve with semantic boundaries.

**Background Processing** - Document ingestion runs async to avoid timeouts on large files.

**In-Memory Metadata** - Simple dict for document tracking. Production would use PostgreSQL.

## Trade-offs (24h Constraint)

- Metadata in memory (not persistent) - Would use PostgreSQL
- Simple chunking strategy - Could use semantic splitting
- No caching layer - Would add Redis for common queries
- No authentication - Would add JWT tokens
- Basic error messages - Could be more detailed

## Performance

- **Search**: 200-500ms
- **Q&A**: 2-5 seconds (includes LLM call)
- **Scale**: Tested with 100+ documents (1000+ pages)
- **Memory**: ~500MB for 1000 documents

## Testing

```bash
poetry run pytest tests/ -v
```

## What I'd Add With More Time

**Week 1:**
- PostgreSQL for metadata
- Redis caching
- Better error handling
- More file formats

**Month 1:**
- User authentication
- Document versioning
- Admin dashboard
- Query analytics

**Month 3:**
- Multi-modal search (images)
- Fine-tuned embeddings
- Distributed processing

## Development

```bash
# Run server
poetry run uvicorn app.main:app --reload

# Run tests
poetry run pytest

# Format code
poetry run black app/

# Check dependencies
poetry show
```

---
