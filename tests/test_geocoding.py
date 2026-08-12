import pytest
from unittest.mock import patch, MagicMock
import httpx
from heatshield.geocoding import search_location

@pytest.fixture
def mock_httpx_get():
    with patch("httpx.AsyncClient.get") as mock_get:
        yield mock_get

@pytest.mark.asyncio
async def test_search_location_success(mock_httpx_get):
    mock_response = MagicMock()
    mock_response.json.return_value = [{
        "display_name": "Test Location, City, Country",
        "lat": "12.345",
        "lon": "67.890"
    }]
    mock_response.raise_for_status = MagicMock()
    mock_httpx_get.return_value = mock_response

    result = await search_location("test query")
    expected = "Location: Test Location, City, Country\nLatitude: 12.345\nLongitude: 67.890"
    assert result == expected

@pytest.mark.asyncio
async def test_search_location_no_results(mock_httpx_get):
    mock_response = MagicMock()
    mock_response.json.return_value = []
    mock_response.raise_for_status = MagicMock()
    mock_httpx_get.return_value = mock_response

    result = await search_location("unknown")
    assert result == "No locations found matching 'unknown'."

@pytest.mark.asyncio
async def test_search_location_request_error(mock_httpx_get):
    mock_httpx_get.side_effect = httpx.RequestError("Network error", request=MagicMock())
    
    result = await search_location("error")
    assert "Error: Failed to connect to Nominatim API" in result

@pytest.mark.asyncio
async def test_search_location_http_status_error(mock_httpx_get):
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_httpx_get.side_effect = httpx.HTTPStatusError("HTTP error", request=MagicMock(), response=mock_response)
    
    result = await search_location("error")
    assert "Error: Nominatim API returned status 500" in result
