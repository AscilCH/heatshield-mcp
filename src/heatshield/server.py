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
from heatshield import geocoding, weather, air_quality, cooling_spots, safety_advice, forecast, rag, heat_map, routing, web_search, isochrone, occupational, heat_dome

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
        query: The name of the city or location (e.g., "Paris, France")
    """
    return await geocoding.search_location(query)

@mcp.tool()
async def get_weather_and_heat_risk(latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Fetches real-time weather and calculates the WHO/CDC heat risk level.
    """
    resolved_name = location_name
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
    elif not location_name and latitude is not None and longitude is not None:
        resolved_name = await geocoding.reverse_geocode(latitude, longitude)
    
    result = await weather.get_weather_data(latitude, longitude, resolved_name)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

import json
@mcp.tool()
async def get_occupational_heat_guidance(workload_intensity: str, latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Calculates Wet Bulb Globe Temperature (WBGT) and fetches NIOSH work/rest cycles.
    MUST be used whenever a user asks for a work schedule or occupational safety advice, 
    REGARDLESS of whether they are working outside, working indoors from home, doing 
    construction, or doing light software engineering. ALWAYS calculate it for ANY job.
    
    Args:
        workload_intensity: Must be exactly 'Light', 'Moderate', or 'Heavy'. The AI must evaluate the user's described labor to choose the correct category.
        latitude: The user's latitude
        longitude: The user's longitude
        location_name: Optional city or location name
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    # 1. Fetch current weather for the location
    weather_data_str = await weather.get_weather_data(latitude, longitude)
    if "Error" in weather_data_str:
        return weather_data_str
        
    w = json.loads(weather_data_str)
    temp = w.get("temperature_celsius", 25.0)
    hum = w.get("humidity_percent", 50.0)
    wind = w.get("wind_speed_kmh", 5.0)
    solar = w.get("solar_radiation_wm2", 500.0)
    
    # 2. Calculate WBGT
    wbgt = occupational.calculate_wbgt(temp, hum, wind, solar)
    
    # 3. Get NIOSH guidelines
    guidance = occupational.get_niosh_guidance(wbgt, workload_intensity)
    
    # Add raw inputs for transparency
    guidance["inputs"] = {
        "temperature_celsius": temp,
        "humidity_percent": hum,
        "wind_speed_kmh": wind,
        "solar_radiation_wm2": solar,
        "assumed_workload": guidance["workload"]
    }
    
    if resolved_name:
        guidance["geocoded_location_name"] = resolved_name
        guidance["geocoded_latitude"] = latitude
        guidance["geocoded_longitude"] = longitude
        
    return json.dumps(guidance)

@mcp.tool()
async def get_air_quality(latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Fetch live air quality data (PM2.5, PM10, AQI) to assess respiratory safety during heat waves.
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = await air_quality.get_air_quality_data(latitude, longitude)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

@mcp.tool()
async def get_air_quality_forecast(days: int = 5, latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Fetches a multi-day predictive air quality forecast (PM10, PM2.5). 
    Use this to warn users about incoming dust, smoke, or pollution events.
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = await air_quality.get_air_quality_forecast(latitude, longitude, days)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

@mcp.tool()
async def find_cooling_spots(
    radius: int = 5000,
    latitude: float = None,
    longitude: float = None,
    location_name: str = None,
    destination_type: str = "any"
) -> str:
    """
    Finds nearby cooling shelters (parks, pools, libraries, malls, fountains).
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
    
    if latitude is None or longitude is None:
        return json.dumps({"error": "Cannot determine location."})
    
    spots_result = await cooling_spots.search_cooling_spots(latitude, longitude, radius)
    try:
        spots_data = json.loads(spots_result)
    except:
        return json.dumps({"error": "Failed to search for cooling spots."})
    
    elements = spots_data.get("elements", [])
    if destination_type != "any":
        filtered = []
        for el in elements:
            tags = el.get("tags", {})
            if destination_type == "park" and tags.get("leisure") == "park": filtered.append(el)
            elif destination_type == "mall" and tags.get("shop") == "mall": filtered.append(el)
            elif destination_type == "library" and tags.get("amenity") == "library": filtered.append(el)
            elif destination_type == "pool" and tags.get("leisure") == "swimming_pool": filtered.append(el)
        elements = filtered

    if not elements:
        return json.dumps({"error": "No cooling spots found."})
        
    return json.dumps({
        "elements": elements,
        "geocoded_location_name": resolved_name,
        "geocoded_latitude": latitude,
        "geocoded_longitude": longitude
    })

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
async def get_heatwave_forecast(days: int = 7, latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Fetches a 7-day weather forecast and calculates a Climate Aggravation Risk
    by correlating high temperatures with drought/soil moisture conditions.
    Use this to predict upcoming heatwaves and warn the user.
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = forecast.get_heatwave_forecast(latitude, longitude, days)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

@mcp.tool()
async def query_emergency_protocols(query: str) -> str:
    """
    Search official medical and urban heat emergency protocols using semantic vector search (RAG).
    Use this when the user asks for safety guidelines, medical advice, or urban planning rules.
    """
    return await rag.query_protocols(query)

@mcp.tool()
async def get_urban_heat_island_heatmap(radius: int = 2500, latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Generates a live spatial GeoJSON heatmap of the Urban Heat Island (UHI) effect.
    Use this when the user wants to visualize heat traps (concrete) versus cooling zones (parks).
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = await heat_map.generate_uhi_heatmap(latitude, longitude, radius)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

@mcp.tool()
async def get_heat_dome_footprint(latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Generates a macro-scale (2000km x 2000km) GeoJSON polygon of the Heat Dome (500hPa Blocking High) footprint.
    Use this ONLY when the user asks about massive heat domes, blocking highs, or canicule boundaries.
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = await heat_dome.get_heat_dome_footprint(latitude, longitude)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

@mcp.tool()
async def get_walking_route(start_lat: float = None, start_lon: float = None, end_lat: float = None, end_lon: float = None, start_location_name: str = None, end_location_name: str = None) -> str:
    """
    Calculates a precise walking route between two coordinates.
    Use this ONLY when the user EXPLICITLY asks for directions or a route to a specific cooling spot.
    DO NOT use this to just 'connect' multiple cooling spots together.
    If you don't know the exact coordinates of the destination, use end_location_name.
    """
    if start_location_name and (start_lat is None or start_lon is None):
        start_lat, start_lon, _ = await geocoding.resolve_location_coords(start_location_name)
    if end_location_name and (end_lat is None or end_lon is None):
        end_lat, end_lon, _ = await geocoding.resolve_location_coords(end_location_name)
        
    if None in [start_lat, start_lon, end_lat, end_lon]:
        return json.dumps({"error": "Missing coordinates for walking route. Please provide valid start and end points."})
        
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
async def generate_walkability_isochrone(minutes: int = 15, latitude: float = None, longitude: float = None, location_name: str = None) -> str:
    """
    Generates a walking isochrone (reachable area polygon) around the user's coordinates.
    Use this when the user asks how far they can walk safely, or for a safe zone map.
    """
    resolved_name = None
    if location_name and (latitude is None or longitude is None):
        latitude, longitude, resolved_name = await geocoding.resolve_location_coords(location_name)
        
    result = await isochrone.generate_walkability_isochrone(latitude, longitude, minutes)
    if resolved_name and "Error" not in result:
        try:
            data = json.loads(result)
            data["geocoded_location_name"] = resolved_name
            data["geocoded_latitude"] = latitude
            data["geocoded_longitude"] = longitude
            result = json.dumps(data)
        except: pass
    return result

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
async def display_medical_triage_advice(severity: str, title: str, steps: str, requires_emergency: bool) -> str:
    """
    Outputs structured medical triage advice to the UI as a high-visibility emergency card.
    Use this AFTER you query the emergency protocols via RAG to provide the user with clear first-aid steps.
    Do NOT output raw prose for medical advice. ALWAYS use this tool.
    
    Args:
        severity: "CRITICAL", "WARNING", or "INFO"
        title: Short title (e.g. "Heat Stroke Warning", "Heat Exhaustion Advice")
        steps: The first-aid steps or advice formatted as a newline-separated string.
        requires_emergency: True if the user should call emergency services immediately.
    """
    import json
    return json.dumps({
        "type": "medical_triage_advice",
        "severity": severity,
        "title": title,
        "steps": steps,
        "requires_emergency": requires_emergency
    })

@mcp.tool()
async def broadcast_emergency_alert(severity: str, message: str) -> str:
    """
    Triggers a global emergency siren and flashing red screen across all connected frontend clients.
    Use this ONLY when the user is experiencing a critical medical emergency (e.g. heat stroke, calling 911).
    
    Args:
        severity: "CRITICAL" or "WARNING"
        message: The emergency message to broadcast.
    """
    import json
    return json.dumps({
        "type": "trigger_emergency_broadcast",
        "severity": severity,
        "message": message
    })

# HOW MCP COMMUNICATION WORKS:
# When we call mcp.run(transport="stdio"), the server enters an infinite loop.
# It listens on stdin for requests from the LLM client, routes them to the 
# correct @mcp.tool() function, and prints the response to stdout.
# Because it uses stdio, you cannot use print() statements for debugging, as they will corrupt the JSON!
def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
