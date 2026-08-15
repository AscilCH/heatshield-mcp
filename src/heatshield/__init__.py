"""
HeatShield: Autonomous Spatial Intelligence & Urban Heat Safety Platform.
"""
from .spatial import geocoding, routing, isochrone, heat_dome, heat_map, spatial_cache
from .telemetry import weather, air_quality, cooling_spots, forecast
from .core import occupational, security
from .knowledge import rag, safety_advice, web_search

__all__ = [
    "geocoding", "routing", "isochrone", "heat_dome", "heat_map", "spatial_cache",
    "weather", "air_quality", "cooling_spots", "forecast",
    "occupational", "security",
    "rag", "safety_advice", "web_search"
]
