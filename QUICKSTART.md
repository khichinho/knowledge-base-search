# Quick Start

## Setup (5 minutes)

### 1. Install Poetry
```bash
pip3 install poetry
```

### 2. Install Dependencies
```bash
poetry install
```

### 3. Configure API Key
```bash
# Edit .env file
cd knowledge-base-search
nano .env

# Set your OpenAI key
OPENAI_API_KEY=sk-your-key-here
```

### 4. Run Server
```bash
poetry run uvicorn app.main:app --reload
```

Open http://localhost:8000/docs

## First Test

1. Go to http://localhost:8000/docs
2. Try `POST /documents/upload` - upload `example_docs/introduction_to_ai.docx`
3. Wait 5 seconds
4. Try `POST /search` with query: "What is machine learning?"
5. Try `POST /qa` with question: "What are the types of AI?"


## Testing

```bash
poetry run pytest tests/ -v
```

---

For more details, see README.md
