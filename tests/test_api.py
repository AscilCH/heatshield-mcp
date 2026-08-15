import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
import asyncio

from api import app, app_state, contacts_db, manager

def _make_func_mock(tool_name, arguments='{}'):
    """Helper to create a function mock with .name set correctly.
    Mock(name=...) is intercepted by Mock's constructor as an internal label,
    so we must set .name after construction."""
    func = Mock()
    func.name = tool_name
    func.arguments = arguments
    return func

# Reset contacts_db before tests
@pytest.fixture(autouse=True)
def reset_contacts_db():
    contacts_db.clear()
    contacts_db.update({
        "mounira": {
            "id": "mounira",
            "name": "Mounira, grandmother",
            "status": "alert",
            "last_update": "No response to check-in · 3 hrs",
            "initials": "MK"
        },
        "youssef": {
            "id": "youssef",
            "name": "Youssef, neighbor",
            "status": "ok",
            "last_update": "Checked in fine · 40 min ago",
            "initials": "YT"
        }
    })

@pytest.fixture
def mock_session():
    session = AsyncMock()
    # Mocking call_tool
    session.call_tool = AsyncMock()
    return session

@pytest.fixture
def app_with_mocked_state(mock_session):
    app_state['session'] = mock_session
    app_state['llm_tools'] = []
    yield app
    app_state.clear()

@pytest.mark.asyncio
async def test_cors_configuration(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.options(
            "/api/contacts",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "GET",
            }
        )
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == "http://localhost:3000"
        assert response.headers["access-control-allow-credentials"] == "true"

@pytest.mark.asyncio
async def test_contacts_get(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.get("/api/contacts")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        ids = [c["id"] for c in data]
        assert "mounira" in ids
        assert "youssef" in ids

@pytest.mark.asyncio
async def test_sms_reply_valid_ok(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post("/webhook/sms-reply", json={"id": "mounira", "message": "I am ok!"})
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "Contact updated to OK"}
        assert contacts_db["mounira"]["status"] == "ok"

@pytest.mark.asyncio
async def test_sms_reply_valid_alert(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post("/webhook/sms-reply", json={"id": "youssef", "message": "help bad"})
        assert response.status_code == 200
        assert response.json() == {"status": "success", "message": "Contact updated to Alert"}
        assert contacts_db["youssef"]["status"] == "alert"

@pytest.mark.asyncio
async def test_sms_reply_invalid_contact(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post("/webhook/sms-reply", json={"id": "nobody", "message": "ok"})
        assert response.status_code == 200
        assert response.json() == {"status": "error", "message": "Contact not found"}

@pytest.mark.asyncio
async def test_chat_security_valid_key(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post(
            "/api/chat", 
            json={"message": "hi"},
            headers={"X-API-Key": "heatshield-demo-key"}
        )
        assert response.status_code == 200

@pytest.mark.asyncio
async def test_chat_security_missing_key(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post("/api/chat", json={"message": "hi"})
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_security_wrong_key(app_with_mocked_state):
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        response = await ac.post(
            "/api/chat", 
            json={"message": "hi"},
            headers={"X-API-Key": "wrong-key"}
        )
        assert response.status_code == 401

@pytest.mark.asyncio
async def test_chat_rate_limiting(app_with_mocked_state):
    from api import chat_rate_limiter
    chat_rate_limiter.ip_records.clear()
    chat_rate_limiter.requests_per_minute = 5
    
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        headers = {"X-API-Key": "heatshield-demo-key", "X-Forwarded-For": "10.0.0.99"}
        
        # 5 requests should pass
        for _ in range(5):
            response = await ac.post("/api/chat", json={"message": "hi"}, headers=headers)
            assert response.status_code == 200
            
        # 6th should fail
        response = await ac.post("/api/chat", json={"message": "hi"}, headers=headers)
        assert response.status_code == 429

@pytest.mark.asyncio
async def test_chat_stream_generator_flow(app_with_mocked_state):
    from api import chat_rate_limiter
    chat_rate_limiter.ip_records.clear()
    
    async with AsyncClient(transport=ASGITransport(app=app_with_mocked_state), base_url="http://test") as ac:
        res = await ac.post("/api/chat", json={"message": "hi"}, headers={"X-API-Key": "heatshield-demo-key"})
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_websocket_broadcast(app_with_mocked_state):
    from fastapi.websockets import WebSocketDisconnect
    # Testing manager broadcast directly or via TestClient websocket
    with TestClient(app_with_mocked_state) as client:
        with client.websocket_connect("/ws/alerts") as websocket1, \
             client.websocket_connect("/ws/alerts") as websocket2:
             
             # Trigger an alert via REST
             client.post("/api/trigger-alert", json={"severity": "high", "message": "Test alert"})
             
             # Check if websockets received it
             msg1 = websocket1.receive_json()
             msg2 = websocket2.receive_json()
             
             assert msg1 == {"type": "emergency_alert", "severity": "high", "message": "Test alert"}
             assert msg2 == {"type": "emergency_alert", "severity": "high", "message": "Test alert"}
