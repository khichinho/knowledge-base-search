#!/bin/bash

# Simple script to run the Knowledge Base API

echo "🚀 Starting Knowledge Base API..."

# Check if Poetry is installed
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry is not installed!"
    echo "📦 Install it with:"
    echo "   curl -sSL https://install.python-poetry.org | python3 -"
    exit 1
fi

# Check if dependencies are installed
if [ ! -d ".venv" ] && [ ! -f "poetry.lock" ]; then
    echo "📥 Installing dependencies..."
    poetry install
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Create one from .env.example and add your OpenAI API key"
    exit 1
fi

# Check if .env file has OpenAI key
if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  Warning: Please add your OpenAI API key to .env file"
    echo "   Edit OPENAI_API_KEY in .env before proceeding"
    exit 1
fi

# Create necessary directories
mkdir -p uploads chroma_db

# Start the server
echo "✓ Starting server on http://localhost:8000"
echo "✓ API docs available at http://localhost:8000/docs"
poetry run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

