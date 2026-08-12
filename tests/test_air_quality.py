import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from heatshield.air_quality import assess_aqi, get_air_quality_data, get_air_quality_forecast

@pytest.mark.parametrize("aqi,expected", [
    (10, "Good"),
    (20, "Good"),
    (21, "Fair"),
    (40, "Fair"),
    (41, "Moderate"),
    (60, "Moderate"),
    (61, "Poor"),
    (80, "Poor"),
    (81, "Very Poor"),
    (100, "Very Poor"),
    (101, "Extremely Poor"),
    (500, "Extremely Poor"),
])
def test_assess_aqi(aqi, expected):
    assert assess_aqi(aqi).startswith(expected)

@pytest.mark.asyncio
@patch('heatshield.air_quality.httpx.AsyncClient')
async def test_get_air_quality_data_success(mock_client_class):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "current": {
            "european_aqi": 45,
            "pm10": 12.5,
            "pm2_5": 5.5,
            "nitrogen_dioxide": 20.0,
            "ozone": 50.0
        }
    }
    mock_client.get.return_value = mock_resp
    
    res = await get_air_quality_data(0.0, 0.0)
    assert "Moderate" in res
    assert "PM10:" in res
    assert "45" in res

@pytest.mark.asyncio
@patch('heatshield.air_quality.httpx.AsyncClient')
async def test_get_air_quality_data_exception(mock_client_class):
    import httpx
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    mock_client.get.side_effect = httpx.RequestError("Net Error", request=MagicMock())
    
    res = await get_air_quality_data(0.0, 0.0)
    assert "Failed to connect" in res

@pytest.mark.asyncio
@patch('heatshield.air_quality.httpx.AsyncClient')
@pytest.mark.parametrize("days,expected_days", [
    (0, 1),
    (5, 5),
    (10, 7),
])
async def test_get_air_quality_forecast(mock_client_class, days, expected_days):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # 24 items per day
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "hourly": {
            "time": ["2024-01-01T00:00"] * (24 * expected_days),
            "european_aqi": [40] * (24 * expected_days),
            "pm10": [10] * (24 * expected_days),
            "pm2_5": [5] * (24 * expected_days)
        }
    }
    mock_client.get.return_value = mock_resp
    
    res = await get_air_quality_forecast(0.0, 0.0, days=days)
    assert "SUCCESS" in res
    assert isinstance(res, str)
    
    mock_client.get.assert_called_once()
    assert mock_client.get.call_args.kwargs["params"]["forecast_days"] == expected_days

@pytest.mark.asyncio
@patch('heatshield.air_quality.httpx.AsyncClient')
async def test_get_air_quality_forecast_incomplete_day(mock_client_class):
    mock_client = AsyncMock()
    mock_client_class.return_value.__aenter__.return_value = mock_client
    
    # Provide only 12 items for the day -> skips incomplete days
    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = {
        "hourly": {
            "time": ["2024-01-01T00:00"] * 12,
            "european_aqi": [40] * 12,
            "pm10": [10] * 12,
            "pm2_5": [5] * 12
        }
    }
    mock_client.get.return_value = mock_resp
    
    res = await get_air_quality_forecast(0.0, 0.0, days=1)
    assert isinstance(res, str)
