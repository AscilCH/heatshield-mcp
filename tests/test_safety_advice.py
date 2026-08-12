import pytest
import json
from src.heatshield.safety_advice import get_advice, get_occupational_heat_guidance

@pytest.mark.parametrize("risk_level, activity_type", [
    ("EXTREME", "jogging"),
    ("high", "exercise"),
    ("MODERATE", "running"),
    ("low", "work"),
    ("extreme", "construction"),
    ("moderate", "elderly"),
    ("high", "kids"),
    ("extreme", "networking"),
    ("extreme", "homework"),
    ("high", "elderly exercise"),
    ("moderate", "picnic"),
    ("fake_risk", "walking"),
    ("", ""),
])
def test_get_advice(risk_level, activity_type):
    advice = get_advice(risk_level, activity_type)
    assert isinstance(advice, str)
    assert len(advice) > 0

@pytest.mark.parametrize("temperature, humidity, expected_risk", [
    (41.0, "high", "Extreme"),
    (40.0, "moderate", "Extreme"),
    (35.0, "high", "High"),
    (36.0, "low", "High"),
    (34.9, "high", "Moderate"),
    (20.0, "low", "Moderate"),
])
def test_get_occupational_heat_guidance_thresholds(temperature, humidity, expected_risk):
    result_json = get_occupational_heat_guidance(temperature, humidity)
    result = json.loads(result_json)
    assert result.get("risk_level") == expected_risk

def test_get_occupational_heat_guidance_actual_temp():
    result_json = get_occupational_heat_guidance(40.0, "high")
    result = json.loads(result_json)
    assert "actual" in result
    assert isinstance(result["actual"], (float, int))
