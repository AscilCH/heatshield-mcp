import httpx
import json

# OSRM Public API endpoint for walking (foot)
OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson"

async def get_walking_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> str:
    """
    Queries the OSRM Public API to calculate a walking route between two points.
    Returns a GeoJSON payload of the route LineString that can be rendered on a map.
    """
    url = OSRM_ROUTE_URL.format(
        lon1=start_lon, lat1=start_lat,
        lon2=end_lon, lat2=end_lat
    )
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, timeout=10.0)
            response.raise_for_status()
        except Exception as exc:
            return json.dumps({"error": f"Failed to connect to OSRM API: {str(exc)}"})
            
    data = response.json()
    
    if data.get("code") != "Ok" or not data.get("routes"):
        return json.dumps({"error": "No walking route found between these points."})
        
    route = data["routes"][0]
    distance = route.get("distance", 0) # meters
    
    # OSRM public API 'foot' profile often hallucinates durations (e.g., 36km/h walking speeds)
    # So we manually calculate the true duration using a realistic human walking speed of 1.4 m/s (5 km/h)
    duration = distance / 1.4 # seconds
    
    geometry = route.get("geometry") # GeoJSON LineString
    
    feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry,
                "properties": {
                    "distance_m": distance,
                    "duration_s": duration,
                    "color": "#3b82f6" # Tailwind blue-500
                }
            }
        ]
    }
    
    return json.dumps({
        "message": f"Found a walking route: {int(distance)} meters ({int(duration // 60)} minutes).",
        "route_geojson": feature
    })
