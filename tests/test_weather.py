import pytest
import json
import httpx
from unittest.mock import AsyncMock, patch, MagicMock

from heatshield.weather import calculate_heat_risk, get_weather_data, _WEATHER_CACHE

@pytest.fixture(autouse=True)
def clear_weather_cache():
    _WEATHER_CACHE.clear()

@pytest.mark.parametrize("apparent_temp, uv_index, expected", [
    (39.0, 5.0, "EXTREME"),
    (20.0, 8.0, "EXTREME"),
    (39.0, 8.0, "EXTREME"),
    (33.0, 5.0, "HIGH"),
    (20.0, 6.0, "HIGH"),
    (32.9, 7.9, "HIGH"),
    (27.0, 2.0, "MODERATE"),
    (20.0, 3.0, "MODERATE"),
    (26.9, 5.9, "MODERATE"),
    (20.0, 2.0, "LOW"),
    (26.9, 2.9, "LOW"),
    (-10.0, 0.0, "LOW"),
    (0.0, -1.0, "LOW"),
])
def test_calculate_heat_risk(apparent_temp, uv_index, expected):
    assert calculate_heat_risk(apparent_temp, uv_index) == expected

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_get_weather_data_success(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 35.0,
            "apparent_temperature": 38.0,
            "relative_humidity_2m": 40,
            "wind_speed_10m": 12.0,
            "shortwave_radiation": 800.0
        },
        "hourly": {
            "apparent_temperature": [30.0, 32.0, 35.0, 38.0, 36.0, 30.0],
            "uv_index": [2.0, 5.0, None, 8.0, 1.0]
        }
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result_json = await get_weather_data(34.0, -118.0)
    result = json.loads(result_json)
    
    assert result["temperature_celsius"] == 35.0
    assert result["feels_like_celsius"] == 38.0
    assert result["humidity_percent"] == 40
    assert result["uv_index"] == 8.0
    assert result["heat_risk_level"] == "EXTREME" 

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_get_weather_data_defaults(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {},
        "hourly": {
            "uv_index": [None, None]
        }
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result_json = await get_weather_data(34.0, -118.0)
    result = json.loads(result_json)
    
    assert result["temperature_celsius"] == 0.0
    assert result["feels_like_celsius"] == 0.0
    assert result["humidity_percent"] == 0.0
    assert result["uv_index"] == 0.0
    assert result["heat_risk_level"] == "LOW"

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_get_weather_data_empty_uv(mock_get):
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "current": {
            "temperature_2m": 25.0,
            "apparent_temperature": 26.0,
            "relative_humidity_2m": 50
        },
        "hourly": {}
    }
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    result_json = await get_weather_data(34.0, -118.0)
    result = json.loads(result_json)
    
    assert result["uv_index"] == 0.0

@pytest.mark.asyncio
@patch('httpx.AsyncClient.get')
async def test_get_weather_data_failure(mock_get):
    mock_get.side_effect = httpx.RequestError("API Error", request=MagicMock())

    result = await get_weather_data(34.0, -118.0)
    assert "Error: Failed to connect" in result
