#!/bin/bash

# Demo script to test the API endpoints

BASE_URL="http://localhost:8000"

echo "🧪 Testing Knowledge Base API"
echo "================================"

# 1. Health Check
echo -e "\n1️⃣ Health Check"
curl -s "$BASE_URL/health" | jq

# 2. Upload Sample Documents (multiple formats - showcasing support for TXT, DOCX, PDF)
echo -e "\n2️⃣ Uploading sample documents (TXT, DOCX, PDF)..."

echo -e "\n📄 Uploading TXT file (web_development_basics.txt)..."
UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/documents/upload" \
  -F "file=@example_docs/web_development_basics.txt")

DOCUMENT_ID=$(echo $UPLOAD_RESPONSE | jq -r '.document_id')
echo "Document ID: $DOCUMENT_ID"
echo $UPLOAD_RESPONSE | jq

echo -e "\n📄 Uploading DOCX file (introduction_to_ai.docx)..."
UPLOAD_RESPONSE2=$(curl -s -X POST "$BASE_URL/documents/upload" \
  -F "file=@example_docs/introduction_to_ai.docx")
echo $UPLOAD_RESPONSE2 | jq

echo -e "\n📄 Uploading PDF file (machine_learning_guide.pdf)..."
UPLOAD_RESPONSE3=$(curl -s -X POST "$BASE_URL/documents/upload" \
  -F "file=@example_docs/machine_learning_guide.pdf")
echo $UPLOAD_RESPONSE3 | jq

# Wait for processing
echo -e "\n⏳ Waiting for document processing (10 seconds)..."
sleep 10

# 3. Check Document Status
echo -e "\n3️⃣ Checking document status"
curl -s "$BASE_URL/documents/$DOCUMENT_ID" | jq

# 4. List All Documents
echo -e "\n4️⃣ Listing all documents"
curl -s "$BASE_URL/documents" | jq

# 5. Semantic Search (searching across all three formats)
echo -e "\n5️⃣ Performing semantic search (across TXT, DOCX, PDF)"
curl -s -X POST "$BASE_URL/search" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is machine learning?",
    "top_k": 3
  }' | jq

# 6. Question Answering (RAG from all document types)
echo -e "\n6️⃣ Asking a question (using content from all formats)"
curl -s -X POST "$BASE_URL/qa" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What are REST APIs and how do they work?"
  }' | jq

# 7. Completeness Check
echo -e "\n7️⃣ Checking completeness"
curl -s -X POST "$BASE_URL/completeness" \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "deep learning",
    "required_aspects": ["neural networks", "training methods", "applications"]
  }' | jq

echo -e "\n✅ Demo complete!"

