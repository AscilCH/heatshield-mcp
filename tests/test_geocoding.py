import pytest
import json
from unittest.mock import patch, MagicMock
import httpx
from heatshield.geocoding import search_location

@pytest.fixture
def mock_httpx_get():
    with patch("httpx.AsyncClient.get") as mock_get:
        yield mock_get

@pytest.mark.asyncio
async def test_search_location_known_city():
    # Tests the fast local cache path (0ms instant resolution)
    result_json = await search_location("Phoenix")
    data = json.loads(result_json)
    assert data["name"] == "Phoenix"
    assert round(data["latitude"], 2) == 33.45
    assert round(data["longitude"], 2) == -112.07

@pytest.mark.asyncio
async def test_search_location_open_meteo(mock_httpx_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "results": [{
            "name": "CustomCity",
            "latitude": 12.345,
            "longitude": 67.890
        }]
    }
    mock_httpx_get.return_value = mock_response

    result_json = await search_location("CustomCityQuery")
    data = json.loads(result_json)
    assert data["name"] == "CustomCity"
    assert data["latitude"] == 12.345
    assert data["longitude"] == 67.890

@pytest.mark.asyncio
async def test_search_location_no_results(mock_httpx_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"results": []}
    mock_httpx_get.return_value = mock_response

    result = await search_location("nonexistent_unknown_city_xyz")
    assert "No locations found matching" in result
