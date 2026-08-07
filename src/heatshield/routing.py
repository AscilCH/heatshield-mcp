import httpx
import json
from shapely.geometry import shape
from heatshield.spatial_cache import get_cached_heatmap

# OSRM Public API endpoint for walking (foot)
OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&alternatives=3"

async def get_walking_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> str:
    """
    Queries the OSRM Public API to calculate a walking route between two points.
    Uses Shapely to intersect alternative routes with cached UHI heatmaps,
    selecting the route that avoids the most 'heat trap' polygons.
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
        
    # Retrieve the cached heatmap from DuckDB
    cached_uhi = get_cached_heatmap(start_lat, start_lon)
    heat_polygons = []
    if cached_uhi:
        try:
            uhi_geojson = json.loads(cached_uhi)
            for feature in uhi_geojson.get("features", []):
                # We only want to avoid "heat traps" (red zones)
                if feature.get("properties", {}).get("type") == "heat_trap":
                    geom = shape(feature["geometry"])
                    if geom.is_valid:
                        heat_polygons.append(geom)
        except Exception as e:
            print("Error parsing UHI geom:", e)

    best_route = None
    min_exposure = float('inf')
    best_distance = 0
    best_geometry = None

    for route in data["routes"]:
        distance = route.get("distance", 0)
        geometry = route.get("geometry")
        
        exposure = 0
        try:
            route_line = shape(geometry)
            if route_line.is_valid:
                for poly in heat_polygons:
                    intersection = route_line.intersection(poly)
                    exposure += intersection.length
        except Exception:
            exposure = 0 # Fallback if shapely parsing fails
            
        if exposure < min_exposure:
            min_exposure = exposure
            best_route = route
            best_distance = distance
            best_geometry = geometry
            
    # Fallback to the first route if something goes wrong
    if not best_route:
        best_route = data["routes"][0]
        best_distance = best_route.get("distance", 0)
        best_geometry = best_route.get("geometry")

    # OSRM public API 'foot' profile often hallucinates durations (e.g., 36km/h walking speeds)
    # So we manually calculate the true duration using a realistic human walking speed of 1.4 m/s (5 km/h)
    duration = best_distance / 1.4 # seconds
    
    is_optimized = min_exposure < float('inf') and len(heat_polygons) > 0
    # Tailwind emerald-500 if optimized, blue-500 otherwise
    route_color = "#10b981" if is_optimized else "#3b82f6" 
    
    msg = f"Found a Shade-Optimized walking route: {int(best_distance)} meters ({int(duration // 60)} minutes). Heat exposure minimized." if is_optimized else f"Found a walking route: {int(best_distance)} meters ({int(duration // 60)} minutes)."

    feature = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": best_geometry,
                "properties": {
                    "distance_m": best_distance,
                    "duration_s": duration,
                    "color": route_color,
                    "optimized": is_optimized
                }
            }
        ]
    }
    
    return json.dumps({
        "message": msg,
        "route_geojson": feature
    })
