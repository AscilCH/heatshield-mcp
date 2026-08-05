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
    display_name = place.get("display_name", "Unknown")
    
    # We return a formatted string because LLMs parse structured natural language very well.
    return (
        f"Location: {display_name}\n"
        f"Latitude: {lat}\n"
        f"Longitude: {lon}"
    )
