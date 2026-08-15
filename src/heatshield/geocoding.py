import httpx
import json

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
OPEN_METEO_GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
USER_AGENT = "heatshield-mcp/0.1.0 (GeoAI Research Project)"

# Fast local cache for major global cities to guarantee 0ms instant resolution
KNOWN_CITIES = {
    "phoenix": (33.4484, -112.0740, "Phoenix"),
    "austin": (30.2672, -97.7431, "Austin"),
    "death valley": (36.4229, -116.9137, "Death Valley"),
    "atlanta": (33.7490, -84.3880, "Atlanta"),
    "paris": (48.8566, 2.3522, "Paris"),
    "tokyo": (35.6762, 139.6503, "Tokyo"),
    "cairo": (30.0444, 31.2357, "Cairo"),
    "london": (51.5074, -0.1278, "London"),
    "berlin": (52.5200, 13.4050, "Berlin"),
    "madrid": (40.4168, -3.7038, "Madrid"),
    "rome": (41.9028, 12.4964, "Rome"),
    "tunis": (36.8065, 10.1815, "Tunis"),
    "sfax": (34.7406, 10.7603, "Sfax"),
    "midoun": (33.8081, 10.9922, "Midoun"),
    "houmt souk": (33.8750, 10.8583, "Houmt Souk"),
    "djerba": (33.8075, 10.8451, "Djerba"),
    "dubai": (25.2048, 55.2708, "Dubai"),
    "los angeles": (34.0522, -118.2437, "Los Angeles"),
    "new york": (40.7128, -74.0060, "New York"),
    "miami": (25.7617, -80.1918, "Miami"),
    "las vegas": (36.1699, -115.1398, "Las Vegas"),
    "dallas": (32.7767, -96.7970, "Dallas"),
    "houston": (29.7604, -95.3698, "Houston"),
    "chicago": (41.8781, -87.6298, "Chicago"),
    "san francisco": (37.7749, -122.4194, "San Francisco"),
    "seattle": (47.6062, -122.3321, "Seattle"),
}

async def search_location(query: str) -> str:
    """
    Geocodes a location with multi-provider fallback (Local Cache -> Open-Meteo Geocoding -> Nominatim).
    """
    clean_q = query.strip().lower().replace(", united states", "").replace(", usa", "").replace(", us", "").strip()
    
    # 1. Fast local cache check
    if clean_q in KNOWN_CITIES:
        lat, lon, name = KNOWN_CITIES[clean_q]
        return json.dumps({
            "name": name,
            "latitude": lat,
            "longitude": lon,
            "message": "Geocoded successfully. Use these coordinates for all other tool calls."
        })
    
    for city_key, (lat, lon, name) in KNOWN_CITIES.items():
        if clean_q.startswith(city_key) or clean_q == city_key:
            return json.dumps({
                "name": name,
                "latitude": lat,
                "longitude": lon,
                "message": "Geocoded successfully. Use these coordinates for all other tool calls."
            })

    # 2. Open-Meteo High-Availability Geocoding API (Fast, No 429 Rate Limits)
    async with httpx.AsyncClient() as client:
        try:
            om_res = await client.get(
                OPEN_METEO_GEOCODE_URL,
                params={"name": query, "count": 1, "language": "en", "format": "json"},
                timeout=5.0
            )
            if om_res.status_code == 200:
                om_data = om_res.json()
                results = om_data.get("results", [])
                if results:
                    r = results[0]
                    short_name = r.get("name", query)
                    return json.dumps({
                        "name": short_name,
                        "latitude": float(r["latitude"]),
                        "longitude": float(r["longitude"]),
                        "message": "Geocoded successfully. Use these coordinates for all other tool calls."
                    })
        except Exception:
            pass

        # 3. OSM Nominatim Fallback
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={"q": query, "format": "jsonv2", "limit": 1, "addressdetails": 1},
                headers={"User-Agent": USER_AGENT},
                timeout=6.0,
            )
            if response.status_code == 200:
                results = response.json()
                if results:
                    place = results[0]
                    display_name = place.get("display_name", "")
                    lat = place.get("lat", "N/A")
                    lon = place.get("lon", "N/A")
                    address = place.get("address", {})
                    short_name = address.get("city") or address.get("town") or address.get("village") or place.get("name") or display_name.split(",")[0]
                    
                    q_words = [w.strip() for w in query.lower().replace(",", " ").split() if len(w.strip()) > 2]
                    d_lower = (display_name + " " + short_name).lower()
                    if q_words and not any(w in d_lower for w in q_words):
                        return f"No confident real-world location found matching '{query}'. Please verify spelling or specify a recognized city or region."
                        
                    return json.dumps({
                        "name": short_name,
                        "latitude": float(lat) if lat != "N/A" else None,
                        "longitude": float(lon) if lon != "N/A" else None,
                        "message": "Geocoded successfully. Use these coordinates for all other tool calls."
                    })
        except Exception:
            pass

    return f"No locations found matching '{query}'. Please specify a recognized city or region."

async def resolve_location_coords(query: str) -> tuple[float, float, str]:
    """
    Internal helper to resolve a location string to (lat, lon, display_name) with multi-provider fallback.
    """
    clean = query.strip().lower()
    
    # 1. Check local cache
    for prefix in ["downtown, ", "downtown ", "centre-ville ", "center of ", "center "]:
        if clean.startswith(prefix):
            clean = clean[len(prefix):]
            
    if clean in KNOWN_CITIES:
        return KNOWN_CITIES[clean]
        
    for k, v in KNOWN_CITIES.items():
        if clean.startswith(k) or k in clean:
            return v

    # 2. Try Open-Meteo Geocoding
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(
                OPEN_METEO_GEOCODE_URL,
                params={"name": query, "count": 1, "language": "en", "format": "json"},
                timeout=5.0
            )
            if res.status_code == 200:
                data = res.json()
                results = data.get("results", [])
                if results:
                    r = results[0]
                    return float(r["latitude"]), float(r["longitude"]), r.get("name", query)
        except Exception:
            pass

        # 3. Try Nominatim
        candidate_queries = [query]
        if "djerba" in clean:
            candidate_queries.extend(["Houmt Souk, Djerba", "Djerba, Tunisia"])
            
        for q in candidate_queries:
            try:
                response = await client.get(
                    f"{NOMINATIM_BASE_URL}/search",
                    params={"q": q, "format": "jsonv2", "limit": 1, "addressdetails": 1},
                    headers={"User-Agent": USER_AGENT},
                    timeout=5.0,
                )
                if response.status_code == 200:
                    results = response.json()
                    if results:
                        place = results[0]
                        address = place.get("address", {})
                        short_name = address.get("city") or address.get("town") or address.get("village") or place.get("name") or place.get("display_name", query).split(",")[0]
                        return float(place["lat"]), float(place["lon"]), short_name
            except Exception:
                continue

    raise ValueError(f"Could not resolve location '{query}'.")

async def reverse_geocode(lat: float, lon: float) -> str:
    """
    Reverse geocodes coordinates to find the city/town name with fallback.
    """
    # Check if close to any known city
    for _, (c_lat, c_lon, name) in KNOWN_CITIES.items():
        if abs(lat - c_lat) < 0.15 and abs(lon - c_lon) < 0.15:
            return name

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={"lat": lat, "lon": lon, "format": "jsonv2"},
                headers={"User-Agent": USER_AGENT},
                timeout=5.0,
            )
            if response.status_code == 200:
                place = response.json()
                address = place.get("address", {})
                return address.get("city") or address.get("town") or address.get("village") or place.get("name") or "Unknown"
        except Exception:
            pass
            
    return "Current Location"
