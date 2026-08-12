import pytest
import math
from src.heatshield.occupational import (
    calculate_vapor_pressure,
    calculate_wbgt,
    map_workload,
    get_niosh_guidance
)

def test_calculate_vapor_pressure_happy_path():
    e = calculate_vapor_pressure(20.0, 50.0)
    assert isinstance(e, float)
    # (50/100) * 6.105 * exp(17.27 * 20 / (237.7 + 20)) -> ~11.66
    assert math.isclose(e, 11.66, rel_tol=0.01)

def test_calculate_vapor_pressure_zero_humidity():
    assert calculate_vapor_pressure(25.0, 0.0) == 0.0

def test_calculate_vapor_pressure_div_zero():
    with pytest.raises(ZeroDivisionError):
        calculate_vapor_pressure(-237.7, 50.0)

@pytest.mark.parametrize("temp,humidity", [
    (100.0, 150.0), # Extreme high temp and humidity > 100
    (-50.0, -10.0), # Extreme low temp and negative humidity
])
def test_calculate_vapor_pressure_extremes(temp, humidity):
    # Just asserting it doesn't crash and returns a float
    result = calculate_vapor_pressure(temp, humidity)
    assert isinstance(result, float)

def test_calculate_wbgt_happy_path():
    res = calculate_wbgt(30.0, 50.0, 10.0, 800.0)
    assert isinstance(res, float)

def test_calculate_wbgt_zero_wind():
    res = calculate_wbgt(25.0, 60.0, 0.0, 0.0)
    assert isinstance(res, float)

def test_calculate_wbgt_negative_wind():
    res = calculate_wbgt(30.0, 50.0, -5.0, 800.0)
    assert isinstance(res, float)

@pytest.mark.parametrize("temp,humidity,wind,solar", [
    (-10.0, 0.0, 100.0, -500.0), # Negative solar not validated, extreme cold
    (50.0, 100.0, 0.0, 1200.0), # Extreme heat
])
def test_calculate_wbgt_extremes(temp, humidity, wind, solar):
    res = calculate_wbgt(temp, humidity, wind, solar)
    assert isinstance(res, float)

@pytest.mark.parametrize("desc, expected", [
    ("digging a hole", "Heavy"),
    ("shoveling dirt", "Heavy"),
    ("roofing today", "Heavy"),
    ("heavy lifting", "Heavy"),
    ("laying asphalt", "Heavy"),
    ("using a sledgehammer", "Heavy"),
    ("walking around", "Moderate"),
    ("carrying boxes", "Moderate"),
    ("painting walls", "Moderate"),
    ("moderate effort", "Moderate"),
    ("construction site", "Moderate"),
    ("sitting at desk", "Light"),
    ("driving truck", "Light"),
    ("standing still", "Light"),
    ("light work", "Light"),
    ("headlight", "Light"), # Substring match edge case
    ("heavy construction", "Heavy"), # Matches Heavy first
    ("homework", "Moderate"), # No match, defaults to Moderate
    ("", "Moderate"),
])
def test_map_workload(desc, expected):
    assert map_workload(desc) == expected

@pytest.mark.parametrize("wbgt, workload, expected_work, expected_rest, expected_halt", [
    # Light workload
    (32.1, "Light", 30, 30, False),  # > 32
    (32.0, "Light", 45, 15, False),  # > 31, exact boundary for 32
    (31.1, "Light", 45, 15, False),  # > 31
    (31.0, "Light", 60, 0, False),   # else
    (20.0, "Light", 60, 0, False),
    # Moderate workload
    (31.6, "Moderate", 0, 60, True), # > 31.5
    (31.5, "Moderate", 15, 45, False), # > 30, exact boundary
    (30.1, "Moderate", 15, 45, False), # > 30
    (30.0, "Moderate", 30, 30, False), # > 29, exact boundary
    (29.1, "Moderate", 30, 30, False), # > 29
    (29.0, "Moderate", 45, 15, False), # > 28, exact boundary
    (28.1, "Moderate", 45, 15, False), # > 28
    (28.0, "Moderate", 60, 0, False),  # else
    # Heavy workload
    (31.6, "Heavy", 0, 60, True),    # > 31.5
    (31.5, "Heavy", 15, 45, False),  # > 30, exact boundary
    (30.1, "Heavy", 15, 45, False),  # > 30
    (30.0, "Heavy", 30, 30, False),  # > 28, exact boundary
    (28.1, "Heavy", 30, 30, False),  # > 28
    (28.0, "Heavy", 45, 15, False),  # > 26, exact boundary
    (26.1, "Heavy", 45, 15, False),  # > 26
    (26.0, "Heavy", 60, 0, False),   # else
])
def test_get_niosh_guidance_thresholds(wbgt, workload, expected_work, expected_rest, expected_halt):
    res = get_niosh_guidance(wbgt, workload)
    assert res['work_minutes'] == expected_work
    assert res['rest_minutes'] == expected_rest
    assert res['halt_operations'] == expected_halt
    assert res['workload'] == workload.capitalize()
    assert res['wbgt_celsius'] == wbgt
    assert 'hydration_rule' in res

@pytest.mark.parametrize("wbgt, expected_hydration", [
    (26.1, "Drink 1 cup (8 oz) of water every 15-20 minutes."),
    (26.0, "Drink water when thirsty."),
    (25.9, "Drink water when thirsty."),
])
def test_get_niosh_guidance_hydration(wbgt, expected_hydration):
    res = get_niosh_guidance(wbgt, "Moderate")
    assert res['hydration_rule'] == expected_hydration

def test_get_niosh_guidance_invalid_workload_fallback():
    res = get_niosh_guidance(29.5, "unknown_workload")
    # Should fallback to Moderate
    assert res['workload'] == "Moderate"
    # Should fallback to Moderate limits: >29 -> 30/30
    assert res['work_minutes'] == 30
    assert res['rest_minutes'] == 30
    assert res['halt_operations'] is False
