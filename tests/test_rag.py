import pytest
import os
import json
from unittest.mock import patch, MagicMock
from heatshield.rag import chunk_text, ingest_document, query_protocols

def test_chunk_text():
    # Empty string
    assert chunk_text("", 100, 20) == []
    
    # Shorter than chunk size
    assert chunk_text("Hello", 100, 20) == ["Hello"]
    
    # Exact chunk size
    assert chunk_text("a" * 10, 10, 2) == ["a" * 10, "aa"]
    
    # Overlap behavior
    text = "abcdefghij"
    chunks = chunk_text(text, chunk_size=6, overlap=2)
    # chunks:
    # 1. abcdef
    # 2. efghij
    assert len(chunks) == 3
    assert chunks[0] == "abcdef"
    assert chunks[1] == "efghij"
    assert chunks[2] == "ij"

@pytest.fixture
def render_env():
    os.environ["RENDER"] = "1"
    yield
    del os.environ["RENDER"]

@pytest.fixture
def mock_chroma():
    with patch("heatshield.rag.get_chroma_collection") as mock_get_col:
        yield mock_get_col

@pytest.fixture
def mock_sentence_transformer():
    with patch("heatshield.rag.get_embedding_model") as mock_get_model:
        yield mock_get_model

@pytest.fixture
def mock_download():
    with patch("heatshield.rag.download_and_extract_pdf") as mock_dl:
        yield mock_dl

@pytest.mark.asyncio
async def test_ingest_document_render_guard(render_env):
    result = await ingest_document("http://test.com")
    data = json.loads(result)
    assert "error" in data

@pytest.mark.asyncio
async def test_query_protocols_render_guard(render_env):
    result = await query_protocols("query")
    data = json.loads(result)
    assert "error" in data

@pytest.mark.asyncio
async def test_ingest_document_success(mock_chroma, mock_sentence_transformer, mock_download):
    if "RENDER" in os.environ:
        del os.environ["RENDER"]
        
    mock_download.return_value = "This is a test document that should be ingested correctly."
    
    mock_model = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.tolist.return_value = [[0.1, 0.2]]
    mock_model.encode.return_value = mock_embeddings
    mock_sentence_transformer.return_value = mock_model
    
    mock_collection = MagicMock()
    mock_chroma.return_value = mock_collection
    
    result = await ingest_document("http://test.com")
    data = json.loads(result)
    
    assert data.get("status") == "success" or "chunks" in data
    mock_collection.add.assert_called()

@pytest.mark.asyncio
async def test_query_protocols_success(mock_chroma, mock_sentence_transformer):
    if "RENDER" in os.environ:
        del os.environ["RENDER"]
        
    mock_model = MagicMock()
    mock_embeddings = MagicMock()
    mock_embeddings.tolist.return_value = [[0.1, 0.2]]
    mock_model.encode.return_value = mock_embeddings
    mock_sentence_transformer.return_value = mock_model
    
    mock_collection = MagicMock()
    mock_collection.query.return_value = {
        "documents": [["Result 1", "Result 2"]],
        "metadatas": [[{"source": "http://test1.com"}, {"source": "http://test2.com"}]]
    }
    
    mock_chroma.return_value = mock_collection
    
    result = await query_protocols("test query", n_results=2)
    data = json.loads(result)
    
    assert len(data["results"]) == 2
    # Can refine based on exact return format
