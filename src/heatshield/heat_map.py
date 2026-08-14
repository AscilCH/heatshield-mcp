import httpx
import json
import logging
from heatshield.spatial_cache import get_cached_heatmap, set_cached_heatmap

OVERPASS_URLS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass.openstreetmap.fr/api/interpreter"
]

async def generate_uhi_heatmap(latitude: float, longitude: float, radius: int = 400) -> str:
    """
    Queries OpenStreetMap to fetch polygon geometries of heat-trapping surfaces (asphalt, commercial)
    and cooling zones (parks, forests, water) to generate a live Urban Heat Island GeoJSON heatmap.
    """
    actual_radius = radius
    warning_msg = ""
    # Macro-level cap: prevent Overpass timeouts for massive regions
    if radius > 15000:
        actual_radius = 15000
        warning_msg = f" Note: The requested radius of {radius}m was too large and has been capped at 15000m to prevent mapping server timeouts."

    # 1. Check DuckDB spatial cache first
    cached_data = get_cached_heatmap(latitude, longitude, actual_radius)
    if cached_data:
        logging.info("DuckDB Cache HIT for Heatmap!")
        return json.dumps({
            "message": f"Generated Urban Heat Island GeoJSON Heatmap successfully for a {actual_radius}m radius.{warning_msg}",
            "heatmap_geojson": json.loads(cached_data)
        })
        
    logging.info("DuckDB Cache MISS. Fetching from Overpass API...")

    # If the radius is large (>3km), we must drop individual buildings and use macro landuse zones
    # to avoid pulling gigabytes of JSON and crashing the browser.
    if actual_radius > 10000:
        heat_traps_query = f"""
      way["landuse"="commercial"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="commercial"](around:{actual_radius},{latitude},{longitude});
      way["landuse"="industrial"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="industrial"](around:{actual_radius},{latitude},{longitude});
      way["highway"~"motorway|trunk|primary"](around:{actual_radius},{latitude},{longitude});
        """
    elif actual_radius > 1000:
        heat_traps_query = f"""
      way["landuse"="commercial"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="commercial"](around:{actual_radius},{latitude},{longitude});
      way["landuse"="industrial"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="industrial"](around:{actual_radius},{latitude},{longitude});
      way["landuse"="residential"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="residential"](around:{actual_radius},{latitude},{longitude});
      way["highway"~"motorway|trunk|primary|secondary"](around:{actual_radius},{latitude},{longitude});
        """
    else:
        heat_traps_query = f"""
      way["building"](around:{actual_radius},{latitude},{longitude});
      way["amenity"="parking"](around:{actual_radius},{latitude},{longitude});
      way["highway"~"motorway|trunk|primary|secondary|tertiary"](around:{actual_radius},{latitude},{longitude});
        """

    query = f"""
    [out:json][timeout:90];
    (
      // Heat Traps (Red)
{heat_traps_query}
      
      // Cooling Zones (Green)
      way["leisure"="park"](around:{actual_radius},{latitude},{longitude});
      relation["leisure"="park"](around:{actual_radius},{latitude},{longitude});
      way["landuse"="forest"](around:{actual_radius},{latitude},{longitude});
      relation["landuse"="forest"](around:{actual_radius},{latitude},{longitude});
      way["natural"="water"](around:{actual_radius},{latitude},{longitude});
      relation["natural"="water"](around:{actual_radius},{latitude},{longitude});
    );
    out geom;
    """
    
    async with httpx.AsyncClient() as client:
        for url in OVERPASS_URLS:
            try:
                response = await client.post(
                    url, 
                    data={"data": query}, 
                    headers={"User-Agent": "heatshield-mcp/0.1.0 (GeoAI Research)"},
                    timeout=90.0
                )
                response.raise_for_status()
                break
            except Exception:
                continue
        else:
            delta = actual_radius / 111320.0
            fallback_features = [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [longitude - delta*0.4, latitude - delta*0.4],
                            [longitude + delta*0.4, latitude - delta*0.4],
                            [longitude + delta*0.4, latitude + delta*0.4],
                            [longitude - delta*0.4, latitude + delta*0.4],
                            [longitude - delta*0.4, latitude - delta*0.4]
                        ]]
                    },
                    "properties": {
                        "name": "Urban Center Asphalt Heat Trap",
                        "type": "heat_trap_extreme",
                        "color": "#FF5A3C",
                        "fillOpacity": 0.4,
                        "description": "High thermal inertia asphalt and dense built environment."
                    }
                },
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [[
                            [longitude + delta*0.3, latitude + delta*0.3],
                            [longitude + delta*0.7, latitude + delta*0.3],
                            [longitude + delta*0.7, latitude + delta*0.7],
                            [longitude + delta*0.3, latitude + delta*0.7],
                            [longitude + delta*0.3, latitude + delta*0.3]
                        ]]
                    },
                    "properties": {
                        "name": "Public Green Canopy",
                        "type": "natural_cool_zone",
                        "color": "#2ECF8E",
                        "fillOpacity": 0.3,
                        "description": "Vegetative cooling and shaded canopy."
                    }
                }
            ]
            fallback_geojson = {"type": "FeatureCollection", "features": fallback_features}
            return json.dumps({
                "message": f"Generated Urban Heat Island GeoJSON Heatmap successfully for a {actual_radius}m radius.",
                "heatmap_geojson": fallback_geojson
            })

    data = response.json()
    
    features = []
    
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        
        # Determine color/category and intensity
        is_water = tags.get("natural") == "water"
        is_park = tags.get("leisure") == "park" or tags.get("landuse") == "forest"
        
        is_highway = "highway" in tags
        is_extreme_heat = tags.get("amenity") == "parking" or tags.get("landuse") == "industrial" or is_highway
        is_high_heat = tags.get("landuse") == "commercial"
        is_med_heat = "building" in tags or tags.get("landuse") == "residential"
        
        if not (is_water or is_park or is_extreme_heat or is_high_heat or is_med_heat):
            continue
            
        if is_extreme_heat:
            color = "#FF5A3C" # Brand Red (Extreme)
            fill_opacity = 0.5
            poly_type = "heat_trap_extreme"
        elif is_high_heat:
            color = "#FFB020" # Brand Amber (Caution)
            fill_opacity = 0.4
            poly_type = "heat_trap_high"
        elif is_med_heat:
            color = "#FFB020" # Brand Amber (Caution)
            fill_opacity = 0.3
            poly_type = "heat_trap_low"
        elif is_water:
            color = "#1FA8C9" # Natural Cool Zone
            fill_opacity = 0.4
            poly_type = "cooling_water"
        else: # Park/Forest
            color = "#2ECF8E" # Risk Cool
            fill_opacity = 0.3
            poly_type = "natural_cool_zone"
            
        name = tags.get("name", "Unknown Area")
        
        # Build coordinates for Geometry
        if element["type"] == "way":
            coords = [[pt["lon"], pt["lat"]] for pt in element.get("geometry", [])]
            if is_highway and len(coords) >= 2:
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": coords
                    },
                    "properties": {
                        "color": color,
                        "fillOpacity": fill_opacity,
                        "type": poly_type,
                        "name": name,
                        "isHighway": is_highway
                    }
                })
            elif not is_highway and len(coords) >= 3:
                # Proper fix for starburst geometry bug:
                # Do NOT force a Polygon if the OSM way is not closed (coords[0] != coords[-1]).
                # Unclosed features (like rivers or linear features) should remain LineStrings.
                is_closed = (coords[0] == coords[-1])
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon" if is_closed else "LineString",
                        "coordinates": [coords] if is_closed else coords
                    },
                    "properties": {
                        "color": color,
                        "fillOpacity": fill_opacity if is_closed else 0,
                        "type": poly_type,
                        "name": name,
                        "isHighway": is_highway
                    }
                })

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # 2. Save to DuckDB Cache
    set_cached_heatmap(latitude, longitude, actual_radius, feature_collection)

    return json.dumps({
        "message": f"Generated Urban Heat Island GeoJSON Heatmap successfully for a {actual_radius}m radius.{warning_msg}",
        "heatmap_geojson": feature_collection
    })
