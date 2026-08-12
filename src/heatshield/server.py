"""
HeatShield MCP Server - Main Entry Point.

WHAT IS MCP?
The Model Context Protocol (MCP) is an open standard that lets you build tools 
once and expose them to ANY compatible AI client (like Claude Desktop, Cursor, or custom agents).
Unlike a REST API (which is designed for web browsers/apps to consume over HTTP), 
MCP is specifically designed for LLMs to consume locally over standard input/output (stdio) 
using JSON-RPC 2.0 messages.

WHY THIS ARCHITECTURE?
We separate our business logic (like geocoding.py) from the server.py. 
This keeps the server clean and makes the tools testable without the MCP wrapper.
"""
from mcp.server.mcpserver import MCPServer
from heatshield import geocoding, weather, air_quality, cooling_spots, safety_advice, forecast, rag, heat_map, routing, web_search, isochrone

# Initialize the MCP Server (This is the high-level API, formerly known as FastMCP)
mcp = MCPServer(
    name="HeatShield",
    instructions="An urban heat wave safety assistant. Use geocode_location first to get coordinates."
)

# WHAT @mcp.tool() DOES UNDER THE HOOD:
# 1. It inspects the Python type hints (query: str) to build a strict JSON Schema.
#    LLMs need this schema so they know exactly what parameters to send in their JSON payloads.
# 2. It reads this exact docstring to tell the LLM exactly WHEN and WHY to use this tool.
# 3. It registers this function in the server's internal router. When the LLM sends a 'tools/call' 
#    JSON-RPC message, MCPServer automatically routes it here.
@mcp.tool()
async def geocode_location(query: str) -> str:
    """
    Get the latitude and longitude for a city, address, or location.
    Always use this tool first if you only have a city name and need coordinates for the other tools.
    DO NOT use this tool for relative terms like "nearby", "here", "my location", or "my position". 
    If the user asks for a relative location, use the physical coordinates provided in your system prompt instead.
    
    Args:
        query: The name of the city or location (e.g., "Karlsruhe, Germany")
    """
    return await geocoding.search_location(query)

@mcp.tool()
async def get_weather_and_heat_risk(latitude: float, longitude: float) -> str:
    """
    Fetch live weather data (temperature, humidity, UV index) and a calculated WHO/CDC heat risk level.
    Requires latitude and longitude.
    """
    return await weather.get_weather_data(latitude, longitude)

@mcp.tool()
async def get_air_quality(latitude: float, longitude: float) -> str:
    """
    Fetch live air quality data (PM2.5, PM10, AQI) to assess respiratory safety during heat waves.
    Requires latitude and longitude.
    """
    return await air_quality.get_air_quality_data(latitude, longitude)

@mcp.tool()
async def get_air_quality_forecast(latitude: float, longitude: float, days: int = 5) -> str:
    """
    Fetches a multi-day predictive air quality forecast (PM10, PM2.5). 
    Use this to warn users about incoming dust, smoke, or pollution events.
    """
    return await air_quality.get_air_quality_forecast(latitude, longitude, days)

@mcp.tool()
async def find_cooling_spots(latitude: float, longitude: float, radius: int = 800) -> str:
    """
    Use spatial analytics to find nearby cooling shelters (parks, pools, libraries, fountains).
    Requires latitude, longitude, and an optional radius in meters.
    """
    return await cooling_spots.search_cooling_spots(latitude, longitude, radius)

@mcp.tool()
def get_heat_safety_advice(heat_risk_level: str, activity_type: str) -> str:
    """
    Get WHO/CDC safety recommendations based on the current heat risk level and the user's activity.
    
    Args:
        heat_risk_level: Must be LOW, MODERATE, HIGH, or EXTREME (obtained from get_weather_and_heat_risk)
        activity_type: e.g., "jogging", "construction work", "elderly care", "general"
    """
    return safety_advice.get_advice(heat_risk_level, activity_type)

@mcp.tool()
def get_occupational_heat_guidance(temperature: float, humidity_level: str = "moderate") -> str:
    """
    Get structured occupational heat safety guidance (work/rest cycles) based on NIOSH standards.
    Use this specifically when a user asks about safe working conditions, work/rest cycles, or whether it is safe to work outside.
    
    Args:
        temperature: The "feels like" temperature in Celsius.
        humidity_level: "high", "moderate", or "low".
    """
    return safety_advice.get_occupational_heat_guidance(temperature, humidity_level)

@mcp.tool()
def get_heatwave_forecast(latitude: float, longitude: float, days: int = 7) -> str:
    """
    Fetches a 7-day weather forecast and calculates a Climate Aggravation Risk
    by correlating high temperatures with drought/soil moisture conditions.
    Use this to predict upcoming heatwaves and warn the user.
    """
    return forecast.get_heatwave_forecast(latitude, longitude, days)

@mcp.tool()
async def query_emergency_protocols(query: str) -> str:
    """
    Search official medical and urban heat emergency protocols using semantic vector search (RAG).
    Use this when the user asks for safety guidelines, medical advice, or urban planning rules.
    """
    return await rag.query_protocols(query)

@mcp.tool()
async def get_urban_heat_island_heatmap(latitude: float, longitude: float, radius: int = 800) -> str:
    """
    Generates a live spatial GeoJSON heatmap of the Urban Heat Island (UHI) effect.
    Use this when the user wants to visualize heat traps (concrete) versus cooling zones (parks).
    """
    return await heat_map.generate_uhi_heatmap(latitude, longitude, radius)

@mcp.tool()
async def get_walking_route(start_lat: float, start_lon: float, end_lat: float, end_lon: float) -> str:
    """
    Calculates a precise walking route between two coordinates.
    Use this when the user asks for directions or a route to a specific cooling spot.
    """
    return await routing.get_walking_route(start_lat, start_lon, end_lat, end_lon)

@mcp.tool()
async def ingest_emergency_document_url(url: str) -> str:
    """
    Downloads a document (PDF or Text) from a URL and ingests it into the ChromaDB vector database.
    Use this when the user asks to learn from a specific WHO/CDC document or urban plan URL.
    """
    return await rag.ingest_document(url)

@mcp.tool()
async def search_web_for_pdfs(query: str) -> str:
    """
    Search the web for official PDF documents. 
    Always include 'filetype:pdf' and specific domains like 'site:who.int' or 'site:cdc.gov' in your query.
    If you find a good URL, you can then use ingest_emergency_document_url to learn it.
    """
    return await web_search.search_web_for_pdfs(query)

@mcp.tool()
async def generate_walkability_isochrone(latitude: float, longitude: float, minutes: int = 15) -> str:
    """
    Generates a walking isochrone (reachable area polygon) around the user's coordinates.
    Use this when the user asks how far they can walk safely, or for a safe zone map.
    """
    return await isochrone.generate_walkability_isochrone(latitude, longitude, minutes)

@mcp.tool()
def trigger_symptom_triage_ui() -> str:
    """
    Triggers the interactive symptom triage UI for the user.
    Use this immediately when the user says they don't feel well, asks about heat exhaustion vs heat stroke, or lists symptoms.
    Do NOT ask them questions or list symptoms yourself; just call this tool so the UI handles the triage.
    """
    import json
    return json.dumps({"type": "symptom_triage_ui"})

@mcp.tool()
async def broadcast_emergency_alert(severity: str, message: str) -> str:
    """
    Triggers a global emergency siren and flashing red screen across all connected frontend clients.
    Use this ONLY when the user is experiencing a critical medical emergency (e.g. heat stroke, calling 911).
    
    Args:
        severity: "CRITICAL" or "WARNING"
        message: The emergency message to broadcast.
    """
    import httpx
    import json
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/api/trigger-alert",
                json={"severity": severity, "message": message},
                timeout=5.0
            )
            response.raise_for_status()
            return json.dumps({"status": "Emergency alert broadcasted successfully!"})
    except Exception as e:
        return json.dumps({"error": f"Failed to broadcast alert: {str(e)}"})

# HOW MCP COMMUNICATION WORKS:
# When we call mcp.run(transport="stdio"), the server enters an infinite loop.
# It listens on stdin for requests from the LLM client, routes them to the 
# correct @mcp.tool() function, and prints the response to stdout.
# Because it uses stdio, you cannot use print() statements for debugging, as they will corrupt the JSON!
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
