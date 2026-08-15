import pytest
import httpx
from unittest.mock import AsyncMock, patch, MagicMock
import json
from heatshield.cooling_spots import get_walking_info, calculate_haversine, search_cooling_spots

@pytest.mark.asyncio
async def test_get_walking_info_success():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "routes": [{"distance": 1400}]
    }
    client = AsyncMock()
    client.get.return_value = mock_response

    dist, dur = await get_walking_info(client, 1.0, 1.0, 2.0, 2.0)
    assert dist == 1400
    assert dur == int(1400 / 1.4)

@pytest.mark.asyncio
async def test_get_walking_info_no_routes():
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"routes": []}
    client = AsyncMock()
    client.get.return_value = mock_response

    dist, dur = await get_walking_info(client, 1.0, 1.0, 2.0, 2.0)
    assert dist == -1
    assert dur == -1

@pytest.mark.asyncio
@pytest.mark.parametrize("status_code", [400, 404, 500])
async def test_get_walking_info_bad_status(status_code):
    mock_response = MagicMock()
    mock_response.status_code = status_code
    client = AsyncMock()
    client.get.return_value = mock_response

    dist, dur = await get_walking_info(client, 1.0, 1.0, 2.0, 2.0)
    assert dist == -1
    assert dur == -1

@pytest.mark.asyncio
async def test_get_walking_info_exception():
    client = AsyncMock()
    client.get.side_effect = httpx.RequestError("Network error")
    
    dist, dur = await get_walking_info(client, 1.0, 1.0, 2.0, 2.0)
    assert dist == -1
    assert dur == -1

@pytest.mark.parametrize("lat1, lon1, lat2, lon2, expected", [
    (48.8566, 2.3522, 51.5074, -0.1278, 343000),
    (0, 0, 0, 0, 0),
    (90, 0, -90, 0, 20015086),
])
def test_calculate_haversine(lat1, lon1, lat2, lon2, expected):
    dist = calculate_haversine(lat1, lon1, lat2, lon2)
    assert abs(dist - expected) < 2000

@pytest.mark.asyncio
@patch('heatshield.cooling_spots.httpx.AsyncClient')
async def test_search_cooling_spots_no_spots(mock_client_class):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"elements": []}
    mock_client.post.return_value = mock_resp
    
    result = await search_cooling_spots(0, 0)
    assert 'no_verified_spots' in result

@pytest.mark.asyncio
@patch('heatshield.cooling_spots.httpx.AsyncClient')
async def test_search_cooling_spots_overpass_exception(mock_client_class):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_client.post.side_effect = Exception("Overpass down")
    
    result = await search_cooling_spots(0, 0)
    assert 'no_verified_spots' in result

@pytest.mark.asyncio
@patch('heatshield.cooling_spots.get_walking_info')
@patch('heatshield.cooling_spots.httpx.AsyncClient')
async def test_search_cooling_spots_success(mock_client_class, mock_get_walking_info):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "elements": [
            {"type": "node", "lat": 0.01, "lon": 0.01, "tags": {"name": "Cool Park", "amenity": "drinking_water"}},
            {"type": "node", "lat": 0.02, "lon": 0.02, "tags": {}},
            {"type": "node", "lat": 0.03, "lon": 0.03, "tags": {"name": ""}},
        ]
    }
    mock_client.post.return_value = mock_resp
    mock_get_walking_info.return_value = (1000, 714)
    
    result = await search_cooling_spots(0.0, 0.0)
    data = json.loads(result)
    
    assert "summary" in data
    assert len(data["elements"]) == 3
    names = [e.get("tags", {}).get("name") for e in data["elements"]]
    assert "Cool Park" in names
    assert "11 minutes" in data["summary"]

@pytest.mark.asyncio
@patch('heatshield.cooling_spots.get_walking_info')
@patch('heatshield.cooling_spots.httpx.AsyncClient')
async def test_search_cooling_spots_osrm_failure(mock_client_class, mock_get_walking_info):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "elements": [
            {"type": "node", "lat": 0.01, "lon": 0.01, "tags": {"name": "Cool Park"}}
        ]
    }
    mock_client.post.return_value = mock_resp
    mock_get_walking_info.return_value = (-1, -1)
    
    result = await search_cooling_spots(0.0, 0.0)
    data = json.loads(result)
    assert "Direct line" in data["summary"]
