import pytest
import json
from src.heatshield.safety_advice import get_advice

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

