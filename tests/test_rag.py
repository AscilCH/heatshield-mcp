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
    assert len(chunks) == 3
    assert chunks[0] == "abcdef"
    assert chunks[1] == "efghij"
    assert chunks[2] == "ij"

@pytest.fixture
def render_env():
    os.environ["RENDER"] = "1"
    yield
    del os.environ["RENDER"]

@pytest.mark.asyncio
async def test_query_protocols_render_guard(render_env):
    result = await query_protocols("query")
    data = json.loads(result)
    assert "results" in data
    assert len(data["results"]) > 0

@pytest.mark.asyncio
async def test_query_protocols_standard():
    result = await query_protocols("heat stroke symptoms")
    data = json.loads(result)
    assert "results" in data
    assert len(data["results"]) > 0
