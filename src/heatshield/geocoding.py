import httpx

NOMINATIM_BASE_URL = "https://nominatim.openstreetmap.org"
USER_AGENT = "heatshield-mcp/0.1.0 (GeoAI Research Project)"

async def search_location(query: str) -> str:
    """
    Core business logic for geocoding a location.
    We keep this separate from the MCP server logic to maintain a clean architecture.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/search",
                params={
                    "q": query,
                    "format": "jsonv2",
                    "limit": 1,
                    "addressdetails": 1,
                },
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            return f"Error: Failed to connect to Nominatim API: {exc}"
        except httpx.HTTPStatusError as exc:
            return f"Error: Nominatim API returned status {exc.response.status_code}"

    results = response.json()
    if not results:
        return f"No locations found matching '{query}'."

    place = results[0]
    lat = place.get("lat", "N/A")
    lon = place.get("lon", "N/A")
    address = place.get("address", {})
    short_name = address.get("city") or address.get("town") or address.get("village") or place.get("name") or place.get("display_name", "Unknown").split(",")[0]
    
    import json
    return json.dumps({
        "name": short_name,
        "latitude": float(lat) if lat != "N/A" else None,
        "longitude": float(lon) if lon != "N/A" else None,
        "message": "Geocoded successfully. Use these coordinates for all other tool calls."
    })

async def resolve_location_coords(query: str) -> tuple[float, float, str]:
    """
    Internal helper to resolve a location string to (lat, lon, display_name).
    Includes intelligent fuzzy fallbacks for colloquial phrases like 'Downtown X'.
    """
    candidate_queries = [query]
    
    clean = query.lower()
    for prefix in ["downtown, ", "downtown ", "centre-ville ", "center of ", "center "]:
        if clean.startswith(prefix):
            candidate_queries.append(query[len(prefix):])
            
    if "djerba" in clean:
        candidate_queries.extend(["Houmt Souk, Djerba", "Djerba, Tunisia"])
        
    async with httpx.AsyncClient() as client:
        for q in candidate_queries:
            try:
                response = await client.get(
                    f"{NOMINATIM_BASE_URL}/search",
                    params={"q": q, "format": "jsonv2", "limit": 1, "addressdetails": 1},
                    headers={"User-Agent": USER_AGENT},
                    timeout=15.0,
                )
                response.raise_for_status()
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
    Reverse geocodes coordinates to find the city/town name.
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOMINATIM_BASE_URL}/reverse",
                params={"lat": lat, "lon": lon, "format": "jsonv2"},
                headers={"User-Agent": USER_AGENT},
                timeout=15.0,
            )
            response.raise_for_status()
            place = response.json()
            address = place.get("address", {})
            return address.get("city") or address.get("town") or address.get("village") or place.get("name") or "Unknown"
        except:
            return "Unknown"
