import httpx
import json
import logging
from heatshield.spatial_cache import get_cached_heatmap, set_cached_heatmap

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

async def generate_uhi_heatmap(latitude: float, longitude: float, radius: int = 800) -> str:
    """
    Queries OpenStreetMap to fetch polygon geometries of heat-trapping surfaces (asphalt, commercial)
    and cooling zones (parks, forests, water) to generate a live Urban Heat Island GeoJSON heatmap.
    """
    
    # 1. Check DuckDB spatial cache first
    cached_data = get_cached_heatmap(latitude, longitude)
    if cached_data:
        logging.info("DuckDB Cache HIT for Heatmap!")
        return json.dumps({
            "message": "Generated Urban Heat Island GeoJSON Heatmap successfully.",
            "heatmap_geojson": json.loads(cached_data)
        })
        
    logging.info("DuckDB Cache MISS. Fetching from Overpass API...")

    # Overpass QL Query to fetch Polygons (ways and relations)
    query = f"""
    [out:json][timeout:30];
    (
      // Heat Traps (Red)
      way["building"](around:{radius},{latitude},{longitude});
      relation["building"](around:{radius},{latitude},{longitude});
      way["amenity"="parking"](around:{radius},{latitude},{longitude});
      relation["amenity"="parking"](around:{radius},{latitude},{longitude});
      
      // Cooling Zones (Green)
      way["leisure"="park"](around:{radius},{latitude},{longitude});
      relation["leisure"="park"](around:{radius},{latitude},{longitude});
      way["landuse"="forest"](around:{radius},{latitude},{longitude});
      relation["landuse"="forest"](around:{radius},{latitude},{longitude});
      way["natural"="water"](around:{radius},{latitude},{longitude});
      relation["natural"="water"](around:{radius},{latitude},{longitude});
    );
    out geom;
    """
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OVERPASS_URL, 
                data={"data": query}, 
                headers={"User-Agent": "heatshield-mcp/0.1.0 (GeoAI Research)"},
                timeout=30.0
            )
            response.raise_for_status()
        except Exception as exc:
            return json.dumps({"error": f"Failed to connect to OSM Overpass API: {str(exc)}"})

    data = response.json()
    
    features = []
    
    for element in data.get("elements", []):
        tags = element.get("tags", {})
        
        # Determine color/category
        is_heat_trap = "building" in tags or tags.get("amenity") == "parking"
        is_cooling = tags.get("leisure") == "park" or tags.get("landuse") == "forest" or tags.get("natural") == "water"
        
        if not (is_heat_trap or is_cooling):
            continue
            
        color = "#ef4444" if is_heat_trap else "#22c55e" # Red or Green
        fill_opacity = 0.2
        poly_type = "heat_trap" if is_heat_trap else "cooling_zone"
        name = tags.get("name", "Unknown Area")
        
        # Build coordinates for Polygon
        if element["type"] == "way":
            coords = [[pt["lon"], pt["lat"]] for pt in element.get("geometry", [])]
            if len(coords) >= 3:
                # Ensure closed polygon
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                
                features.append({
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [coords]
                    },
                    "properties": {
                        "color": color,
                        "fillOpacity": fill_opacity,
                        "type": poly_type,
                        "name": name
                    }
                })

    feature_collection = {
        "type": "FeatureCollection",
        "features": features
    }
    
    # 2. Save to DuckDB Cache
    set_cached_heatmap(latitude, longitude, feature_collection)

    return json.dumps({
        "message": "Generated Urban Heat Island GeoJSON Heatmap successfully.",
        "heatmap_geojson": feature_collection
    })
