import pytest
import time
from unittest.mock import Mock
from fastapi import HTTPException, Request
from src.heatshield.security import verify_api_key, RateLimiter, VALID_API_KEY

@pytest.mark.asyncio
async def test_verify_api_key_valid():
    assert await verify_api_key(VALID_API_KEY) == VALID_API_KEY

@pytest.mark.asyncio
async def test_verify_api_key_invalid():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key("wrong-key")
    assert exc_info.value.status_code == 401
    assert "Invalid or missing" in exc_info.value.detail

@pytest.mark.asyncio
async def test_verify_api_key_missing():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(None)
    assert exc_info.value.status_code == 401
    assert "Invalid or missing" in exc_info.value.detail

@pytest.mark.asyncio
async def test_verify_api_key_case_sensitive():
    with pytest.raises(HTTPException) as exc_info:
        await verify_api_key(VALID_API_KEY.upper())
    assert exc_info.value.status_code == 401

@pytest.mark.asyncio
async def test_rate_limiter_allows_requests():
    limiter = RateLimiter(requests_per_minute=5)
    req = Mock(spec=Request)
    req.client = Mock()
    req.client.host = "192.168.1.1"

    # Should allow 5 requests
    for _ in range(5):
        assert await limiter(req) is True

@pytest.mark.asyncio
async def test_rate_limiter_blocks_excess_requests():
    limiter = RateLimiter(requests_per_minute=5)
    req = Mock(spec=Request)
    req.client = Mock()
    req.client.host = "192.168.1.2"

    for _ in range(5):
        await limiter(req)

    # 6th request should fail
    with pytest.raises(HTTPException) as exc_info:
        await limiter(req)
    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail

@pytest.mark.asyncio
async def test_rate_limiter_sliding_window(monkeypatch):
    limiter = RateLimiter(requests_per_minute=5)
    req = Mock(spec=Request)
    req.client = Mock()
    req.client.host = "192.168.1.3"

    current_time = time.time()
    
    def mock_time():
        return current_time

    monkeypatch.setattr(time, "time", mock_time)

    for _ in range(5):
        await limiter(req)

    with pytest.raises(HTTPException):
        await limiter(req)

    # Move time forward by 61 seconds
    current_time += 61
    assert await limiter(req) is True

@pytest.mark.asyncio
async def test_rate_limiter_ip_extraction_none():
    limiter = RateLimiter(requests_per_minute=5)
    req = Mock(spec=Request)
    req.client = None # Client is None

    # Should work, falls back to 'unknown'
    assert await limiter(req) is True

@pytest.mark.asyncio
async def test_rate_limiter_shared_instance():
    limiter = RateLimiter(requests_per_minute=5)
    req1 = Mock(spec=Request)
    req1.client = Mock()
    req1.client.host = "10.0.0.1"

    req2 = Mock(spec=Request)
    req2.client = Mock()
    req2.client.host = "10.0.0.2"

    for _ in range(5):
        await limiter(req1)
        await limiter(req2)
    
    with pytest.raises(HTTPException):
        await limiter(req1)
        
    with pytest.raises(HTTPException):
        await limiter(req2)
