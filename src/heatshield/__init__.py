"""
HeatShield: Autonomous Spatial Intelligence & Urban Heat Safety Platform.
"""
import sys

from .spatial import geocoding, routing, isochrone, heat_dome, heat_map, spatial_cache
from .telemetry import weather, air_quality, cooling_spots, forecast
from .core import occupational, security
from .knowledge import rag, safety_advice, web_search

# Module Aliases for 100% backward compatibility with both `heatshield.*` and `src.heatshield.*`
for name, mod in [
    ("geocoding", geocoding), ("routing", routing), ("isochrone", isochrone),
    ("heat_dome", heat_dome), ("heat_map", heat_map), ("spatial_cache", spatial_cache),
    ("weather", weather), ("air_quality", air_quality), ("cooling_spots", cooling_spots),
    ("forecast", forecast), ("occupational", occupational), ("security", security),
    ("rag", rag), ("safety_advice", safety_advice), ("web_search", web_search)
]:
    sys.modules[f"heatshield.{name}"] = mod
    sys.modules[f"src.heatshield.{name}"] = mod

__all__ = [
    "geocoding", "routing", "isochrone", "heat_dome", "heat_map", "spatial_cache",
    "weather", "air_quality", "cooling_spots", "forecast",
    "occupational", "security",
    "rag", "safety_advice", "web_search"
]
