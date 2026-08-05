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
from heatshield import geocoding, weather, air_quality, cooling_spots, safety_advice

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
async def find_cooling_spots(latitude: float, longitude: float, radius: int = 1000) -> str:
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


# HOW MCP COMMUNICATION WORKS:
# When we call mcp.run(transport="stdio"), the server enters an infinite loop.
# It listens on stdin for requests from the LLM client, routes them to the 
# correct @mcp.tool() function, and prints the response to stdout.
# Because it uses stdio, you cannot use print() statements for debugging, as they will corrupt the JSON!
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
