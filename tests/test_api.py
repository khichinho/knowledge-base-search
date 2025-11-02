"""API endpoint tests."""


def test_root_endpoint(client):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "total_documents" in data


def test_upload_document(client):
    """Test document upload."""
    # Create a simple test file
    test_content = b"This is a test document for knowledge base testing."

    files = {"file": ("test.txt", test_content, "text/plain")}
    response = client.post("/documents/upload", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "document_id" in data
    assert data["filename"] == "test.txt"
    assert data["status"] in ["pending", "processing"]


def test_list_documents(client):
    """Test listing documents."""
    response = client.get("/documents")
    assert response.status_code == 200
    data = response.json()
    assert "documents" in data
    assert "total_count" in data


def test_search_without_documents(client):
    """Test search with no documents uploaded."""
    response = client.post("/search", json={"query": "test query", "top_k": 5})
    assert response.status_code == 200
    data = response.json()
    assert data["query"] == "test query"
    assert isinstance(data["results"], list)


# TODO: Add more comprehensive tests for Q&A and completeness check
# These would require actual documents to be processed first
