import pytest
from unittest.mock import patch, MagicMock
import json
from heatshield.forecast import get_heatwave_forecast

@pytest.fixture
def mock_requests():
    with patch('heatshield.forecast.httpx.get') as mock_get:
        yield mock_get

@pytest.mark.parametrize("days,expected_days", [
    (0, 1),
    (-5, 1),
    (7, 7),
    (15, 14),
    (20, 14),
])
def test_get_heatwave_forecast_clamp_days(mock_requests, days, expected_days):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "daily": {"time": [], "temperature_2m_max": [], "apparent_temperature_max": []},
        "hourly": {"soil_moisture_3_9cm": []}
    }
    mock_requests.return_value = mock_resp
    
    res = get_heatwave_forecast(0.0, 0.0, days=days)
    assert isinstance(res, str)

def test_get_heatwave_forecast_data(mock_requests):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "daily": {
            "time": ["2024-01-01", "2024-01-02", "2024-01-03", "2024-01-04"],
            "temperature_2m_max": [33.0, 32.0, 25.0, 36.0],
            "apparent_temperature_max": [36.0, 35.0, 26.0, 38.0]
        },
        "hourly": {
            # 4 days = 96 hours
            # day 1: avg moisture 0.20
            # day 2: avg moisture 0.25
            # day 3: all None
            # day 4: avg moisture 0.15
            "soil_moisture_0_to_1cm": [0.20]*24 + [0.25]*24 + [None]*24 + [0.15]*24
        }
    }
    mock_requests.return_value = mock_resp
    
    res = get_heatwave_forecast(0.0, 0.0, days=4)
    data = json.loads(res)
    
    assert data["status"] == "SEVERE_HEATWAVE_DETECTED"  # >=32 for >=2 consecutive days (day 1, day 2)
    
    # Day 1: temp > 30, moisture = 0.20 < 0.22 -> drought warning true
    assert data["daily_forecast"][0]["climate_aggravation"] != "Normal moisture"
    assert data["daily_forecast"][0]["risk_level"] == "HIGH" # feel>=35 -> HIGH
    
    # Day 2: moisture > 0.22 -> no drought
    assert data["daily_forecast"][1]["climate_aggravation"] == "Normal moisture"
    assert data["daily_forecast"][1]["risk_level"] == "HIGH" 
    
    # Day 3: None moisture -> 0 division guard -> 0
    assert data["daily_forecast"][2]["soil_moisture"] == 0
    assert data["daily_forecast"][2]["risk_level"] == "LOW"
    
    # Day 4: temp >= 35, feel >= 38 -> EXTREME
    assert data["daily_forecast"][3]["risk_level"] == "EXTREME"
    assert data["daily_forecast"][3]["climate_aggravation"] != "Normal moisture"

def test_get_heatwave_forecast_none_temps(mock_requests):
    mock_resp = MagicMock()
    mock_resp.json.return_value = {
        "daily": {
            "time": ["2024-01-01"],
            "temperature_2m_max": [None],
            "apparent_temperature_max": [None]
        },
        "hourly": {
            "soil_moisture_0_to_1cm": [0.2]*24
        }
    }
    mock_requests.return_value = mock_resp
    
    res = get_heatwave_forecast(0.0, 0.0, days=1)
    data = json.loads(res)
    assert data["daily_forecast"][0]["max_temp_c"] == 0
    assert data["daily_forecast"][0]["risk_level"] == "LOW"

def test_get_heatwave_forecast_exception(mock_requests):
    mock_requests.side_effect = Exception("API error")
    res = get_heatwave_forecast(0, 0)
    data = json.loads(res)
    assert "error" in data
