import httpx
import json

OVERPASS_URL = "https://overpass-api.de/api/interpreter"

async def generate_uhi_heatmap(latitude: float, longitude: float, radius: int = 1500) -> str:
    """
    Generates a GeoJSON heatmap of the Urban Heat Island effect by querying OpenStreetMap
    for concrete structures (buildings, parking, roads) vs green structures (parks, forests).
    """
    # Overpass QL to get polygons for concrete and green spaces
    query = f"""
    [out:json][timeout:25];
    (
      // Concrete / Heat Traps (Red)
      way["building"](around:{radius},{latitude},{longitude});
      way["amenity"="parking"](around:{radius},{latitude},{longitude});
      
      // Green Spaces / Cool Zones (Green)
      way["leisure"="park"](around:{radius},{latitude},{longitude});
      way["landuse"="forest"](around:{radius},{latitude},{longitude});
      way["natural"="water"](around:{radius},{latitude},{longitude});
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
        if element.get("type") != "way":
            continue
            
        tags = element.get("tags", {})
        geometry = element.get("geometry", [])
        
        if len(geometry) < 3:
            continue # Need at least a few points for a polygon
            
        # Determine if it's a heat trap (red) or cooling zone (green)
        is_green = "leisure" in tags or "landuse" in tags or "natural" in tags
        color = "#22c55e" if is_green else "#ef4444" # Tailwind Green 500 or Red 500
        fill_opacity = 0.4 if is_green else 0.2
        
        # Build coordinates array
        coordinates = [[point["lon"], point["lat"]] for point in geometry]
        # Close the polygon if not closed
        if coordinates[0] != coordinates[-1]:
            coordinates.append(coordinates[0])
            
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [coordinates]
            },
            "properties": {
                "color": color,
                "fillOpacity": fill_opacity,
                "type": "green_zone" if is_green else "heat_trap",
                "name": tags.get("name", "Unknown Area")
            }
        }
        features.append(feature)
        
        # Limit to 500 features to prevent browser crash
        if len(features) >= 500:
            break
            
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    result = {
        "status": "SUCCESS",
        "message": f"Generated Urban Heat Island heatmap with {len(features)} spatial polygons.",
        "heatmap_geojson": geojson
    }
    
    return json.dumps(result)
