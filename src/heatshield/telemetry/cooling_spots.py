import httpx
import math
import asyncio

OVERPASS_URLS = [
    "https://lz4.overpass-api.de/api/interpreter",
    "https://z.overpass-api.de/api/interpreter",
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter"
]
OSRM_ROUTE_URL = "http://router.project-osrm.org/route/v1/foot/{lon1},{lat1};{lon2},{lat2}?overview=false"

async def get_walking_info(client: httpx.AsyncClient, lat1: float, lon1: float, lat2: float, lon2: float) -> tuple[int, int]:
    """Fetches true walking distance (m) and time (s) from OSRM. Returns (-1, -1) on failure."""
    url = OSRM_ROUTE_URL.format(lon1=lon1, lat1=lat1, lon2=lon2, lat2=lat2)
    try:
        resp = await client.get(url, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            if "routes" in data and len(data["routes"]) > 0:
                dist = int(data["routes"][0].get("distance", 0))
                # OSRM public API foot profile often calculates insanely fast walking speeds.
                # Use a realistic 1.4 m/s (5 km/h) walking speed for accuracy.
                duration = int(dist / 1.4) 
                return dist, duration
    except Exception:
        pass
    return -1, -1

def calculate_haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Fallback crow-flies distance."""
    R = 6371000
    phi_1, phi_2 = math.radians(lat1), math.radians(lat2)
    delta_phi, delta_lambda = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0) ** 2 + math.cos(phi_1) * math.cos(phi_2) * math.sin(delta_lambda / 2.0) ** 2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

async def search_cooling_spots(latitude: float, longitude: float, radius: int = 5000) -> str:
    """
    Query the Overpass API to find nearby cooling spots. 
    Then calculates True Walking Time using OSRM to represent accessibility.
    """
    actual_radius = radius
    if radius > 25000:
        actual_radius = 25000

    query = f"""
    [out:json][timeout:15];
    (
      node["amenity"="drinking_water"](around:{actual_radius},{latitude},{longitude});
      node["leisure"="park"](around:{actual_radius},{latitude},{longitude});
      node["amenity"="library"](around:{actual_radius},{latitude},{longitude});
      node["leisure"="swimming_pool"](around:{actual_radius},{latitude},{longitude});
      node["shop"="mall"](around:{actual_radius},{latitude},{longitude});
      way["leisure"="park"](around:{actual_radius},{latitude},{longitude});
    );
    out center;
    """
    
    async with httpx.AsyncClient(headers={'User-Agent': 'heatshield-mcp/0.1.0'}) as client:
        elements = []
        for url in OVERPASS_URLS:
            try:
                response = await client.post(
                    url,
                    data={"data": query},
                    headers={"User-Agent": "heatshield-mcp/0.1.0 (GeoAI Research)"},
                    timeout=30.0
                )
                response.raise_for_status()
                data = response.json()
                elements = data.get("elements", [])
                break
            except Exception:
                continue
        
        if not elements:
            import json
            return json.dumps({
                "status": "no_verified_spots",
                "count": 0,
                "elements": [],
                "summary": f"No verified air-conditioned cooling centers, libraries, or shaded public parks found within {actual_radius}m. Prioritize indoor commercial spaces with AC, public facilities, or immediate deep tree canopy shade."
            }, indent=2)
            
        results = [f"Cooling Spots within {actual_radius}m (Evaluating True Walking Time from {latitude}, {longitude}):"]
        
        # Limit to top 3 closest by haversine first to avoid OSRM rate limits (1 req/sec max)
        spots = []
        for el in elements:
            tags = el.get("tags", {})
            spot_lat = el.get("lat") or el.get("center", {}).get("lat", 0.0)
            spot_lon = el.get("lon") or el.get("center", {}).get("lon", 0.0)
            dist_hav = calculate_haversine(latitude, longitude, spot_lat, spot_lon)
            spots.append((el, tags, spot_lat, spot_lon, dist_hav))
            
        spots.sort(key=lambda x: x[4])
        all_spots = spots[:20] # Return up to 20 spots for the frontend map
        top_spots = all_spots[:3] # Only calculate OSRM for top 3 to prevent rate limits
        
        # Concurrent OSRM requests to speed up response
        tasks = []
        for _, _, s_lat, s_lon, _ in top_spots:
            tasks.append(get_walking_info(client, latitude, longitude, s_lat, s_lon))
            
        walking_infos = await asyncio.gather(*tasks)
        
        # Format output
        for i, (el, tags, s_lat, s_lon, dist_hav) in enumerate(top_spots):
            spot_type = tags.get("amenity") or tags.get("leisure") or tags.get("shop", "Unknown")
            name = tags.get("name", "")
            if not name or "Unnamed Spot" in name:
                name = "Nearby park" if spot_type == "park" else "Cooling center"
            
            w_dist, w_time = walking_infos[i]
            if w_dist != -1 and w_time != -1:
                mins = max(1, w_time // 60) # Ensure it doesn't say 0 minutes or negative
                results.append(f"- {name} ({spot_type}) - True Walk: {mins} minutes ({w_dist}m)")
            else:
                results.append(f"- {name} ({spot_type}) - {int(dist_hav)}m away (Direct line)")
            
        import json
        return json.dumps({
            "status": "success",
            "count": len(all_spots),
            "summary": "\n".join(results),
            "elements": [
                {
                    "lat": s_lat,
                    "lon": s_lon,
                    "tags": tags,
                    "distance_m": int(dist_hav)
                } for _, tags, s_lat, s_lon, dist_hav in all_spots
            ]
        }, indent=2)
