import httpx
import math

OVERPASS_API_URL = "https://overpass-api.de/api/interpreter"

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the Haversine distance between two points in meters."""
    R = 6371000 # Radius of Earth in meters
    phi_1 = math.radians(lat1)
    phi_2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi / 2.0) ** 2 + \
        math.cos(phi_1) * math.cos(phi_2) * \
        math.sin(delta_lambda / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

async def search_cooling_spots(latitude: float, longitude: float, radius: int = 1000) -> str:
    """
    Query the Overpass API to find nearby cooling spots like parks, 
    water fountains, libraries, and pools.
    """
    # Overpass QL query to find specific amenities around a coordinate
    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="drinking_water"](around:{radius},{latitude},{longitude});
      node["leisure"="park"](around:{radius},{latitude},{longitude});
      node["amenity"="library"](around:{radius},{latitude},{longitude});
      node["leisure"="swimming_pool"](around:{radius},{latitude},{longitude});
      node["shop"="mall"](around:{radius},{latitude},{longitude});
      way["leisure"="park"](around:{radius},{latitude},{longitude});
    );
    out center;
    """
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                OVERPASS_API_URL,
                data={"data": query},
                headers={"User-Agent": "heatshield-mcp/0.1.0 (GeoAI Research)"},
                timeout=20.0
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            return f"Error: Failed to connect to Overpass API: {exc}"
        except httpx.HTTPStatusError as exc:
            return f"Error: Overpass API returned status {exc.response.status_code}"

    data = response.json()
    elements = data.get("elements", [])
    
    if not elements:
        return f"No cooling spots found within {radius} meters."
        
    results = [f"Cooling Spots within {radius}m of {latitude}, {longitude}:"]
    
    for el in elements:
        tags = el.get("tags", {})
        
        # Determine the type of spot
        spot_type = "Unknown"
        if "amenity" in tags:
            spot_type = tags["amenity"]
        elif "leisure" in tags:
            spot_type = tags["leisure"]
        elif "shop" in tags:
            spot_type = tags["shop"]
            
        name = tags.get("name", "Unnamed Spot")
        
        # Overpass returns center lat/lon for ways
        spot_lat = el.get("lat") or el.get("center", {}).get("lat", 0.0)
        spot_lon = el.get("lon") or el.get("center", {}).get("lon", 0.0)
        
        dist = calculate_distance(latitude, longitude, spot_lat, spot_lon)
        results.append(f"- {name} ({spot_type}) - {int(dist)}m away")
        
    return "\n".join(results)
