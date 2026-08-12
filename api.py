import asyncio
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import typing
from src.heatshield.security import verify_api_key, RateLimiter

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

app_state = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()
async def get_gemini_response(messages, tools):
    import openai
    for attempt in range(5):
        try:
            return await client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=messages,
                tools=tools
            )
        except openai.RateLimitError as e:
            print(f"⚠️ Rate limit exceeded (429). Retrying in 6 seconds... (Attempt {attempt+1}/5)")
            await asyncio.sleep(6)
        except openai.InternalServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"⚠️ API overloaded (503). Retrying in 2 seconds... (Attempt {attempt+1}/5)")
                await asyncio.sleep(2)
            else:
                raise e
    raise Exception("API is overloaded or rate limited. Please try again.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting HeatShield Backend...")
    server_params = StdioServerParameters(command="python", args=["-m", "src.heatshield.server"])
    
    # We use an ExitStack pattern because stdio_client is an async context manager
    # but we need it to stay open for the whole lifespan of the FastAPI app.
    # A simple trick is to keep it running in a background task, or just block here?
    # No, FastAPI lifespan expects yield. So we can just nest it.
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("Connected to HeatShield MCP Server!")
            
            mcp_tools_response = await session.list_tools()
            llm_tools = []
            for tool in mcp_tools_response.tools:
                llm_tools.append({
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema
                    }
                })
            
            app_state['session'] = session
            app_state['llm_tools'] = llm_tools
            yield
            
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    history: typing.List[dict] = []
    latitude: typing.Optional[float] = None
    longitude: typing.Optional[float] = None

@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect messages from the client, just keeping the connection alive
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

class AlertRequest(BaseModel):
    severity: str
    message: str

@app.post("/api/trigger-alert")
async def trigger_alert(req: AlertRequest):
    # Broadcast the alert to all connected frontend clients
    payload = json.dumps({
        "type": "emergency_alert",
        "severity": req.severity,
        "message": req.message
    })
    await manager.broadcast(payload)
    return {"status": "Alert broadcasted successfully"}

# Check-in Contacts Database (Mock)
contacts_db = {
    "mounira": {
        "id": "mounira",
        "name": "Mounira, grandmother",
        "status": "alert",
        "last_update": "No response to check-in · 3 hrs",
        "initials": "MK"
    },
    "youssef": {
        "id": "youssef",
        "name": "Youssef, neighbor",
        "status": "ok",
        "last_update": "Checked in fine · 40 min ago",
        "initials": "YT"
    }
}

@app.get("/api/contacts")
async def get_contacts():
    return list(contacts_db.values())

@app.post("/webhook/sms-reply")
async def sms_reply(req: dict):
    contact_id = req.get("id")
    message = req.get("message", "").lower()
    
    if contact_id in contacts_db:
        if "ok" in message or "fine" in message or "good" in message or "yes" in message:
            contacts_db[contact_id]["status"] = "ok"
            contacts_db[contact_id]["last_update"] = "Checked in fine · Just now"
            return {"status": "success", "message": "Contact updated to OK"}
        else:
            contacts_db[contact_id]["status"] = "alert"
            contacts_db[contact_id]["last_update"] = "Alert: " + message
            return {"status": "success", "message": "Contact updated to Alert"}
    return {"status": "error", "message": "Contact not found"}

chat_rate_limiter = RateLimiter(requests_per_minute=5)

@app.post("/api/chat", dependencies=[Depends(verify_api_key), Depends(chat_rate_limiter)])
async def chat_endpoint(req: ChatRequest):
    session = app_state.get('session')
    llm_tools = app_state.get('llm_tools')
    
    if not session:
        raise HTTPException(status_code=500, detail="MCP Server not connected")
        
    system_prompt = (
        "You are HeatShield, an urban heat wave safety assistant. Use geospatial tools to accurately assess risk and answer the user's queries. "
        "IMPORTANT: NEVER use LaTeX formatting or math equations for numbers, temperatures, or ranges (e.g. use '4°C' instead of '$4^\\circ\\text{C}$', and '0.10' instead of '$0.10$'). Use standard plain text formatting only. "
        "STRICT PERSONA ENFORCEMENT: You MUST absolutely refuse to answer any questions that are off-topic. "
        "OCCUPATIONAL SAFETY: When asked about safe work conditions, CDC/NIOSH work/rest cycles, or working outside, you MUST call the `get_occupational_heat_guidance` tool. "
        "CRITICAL RULE: If the user asks for a safety schedule but does not specify their physical activity or workload (e.g. they just say 'I need a schedule'), YOU MUST ask them what kind of physical labor they are doing before calling the tool! DO NOT guess their workload. "
        "Do not generate a free-text markdown table yourself; the UI will render it natively based on your tool call. NEVER write any prose summarizing the results of this tool, the UI will display everything. "
        "MAP UPDATES: When the user asks about a new city, place, or location, you MUST call both `get_urban_heat_island_heatmap` and `find_cooling_spots` for that new location to ensure the map UI updates properly! "
        "MEDICAL TRIAGE & RAG: If the user lists symptoms or asks for medical advice, you MUST call `query_emergency_protocols` to retrieve official WHO/CDC first-aid protocols. NEVER hallucinate medical advice. "
        "EMERGENCIES: If the user explicitly states they are calling emergency services or experiencing a critical emergency, you MUST call the `broadcast_emergency_alert` tool to trigger the global siren on all connected devices."
    )
    
    if req.latitude is not None and req.longitude is not None:
        system_prompt += (
            f" The user's physical device is located at Latitude {req.latitude}, Longitude {req.longitude}. "
            f"If they ask for information 'nearby' or 'here', DO NOT call the geocode_location tool with the word 'nearby'. "
            f"Instead, use the coordinates of the last city discussed in the conversation history. "
            f"If no other location has been discussed yet, you MUST directly use their physical device coordinates ({req.latitude}, {req.longitude}) for all tool calls."
        )
    else:
        system_prompt += (
            " WARNING: The user's browser blocked geolocation and IP location failed. YOU DO NOT KNOW WHERE THEY ARE. "
            "If they ask for something 'nearby' and you have no previous city in the chat history, YOU MUST ASK THEM to type their city name. "
            "DO NOT hallucinate a default city. DO NOT assume they are in Paris or anywhere else. Ask them where they are."
        )

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})
    
    async def event_generator():
        # Track map coordinates for the frontend
        map_markers = []
        forecast_data = None
        aq_forecast_data = None
        uhi_geojson = None
        route_geojson = None
        isochrone_geojson = None
        safety_advice_data = None
        work_rest_guidance = None
        current_weather_data = None
        symptom_triage_ui = False
        
        try:
            response = await get_gemini_response(messages, llm_tools)
        except Exception as e:
            yield json.dumps({"type": "final", "text": "⚠️ **Google Gemini API Rate Limit Exceeded.** You are making too many requests too quickly on the Free Tier (15 requests per minute). Please wait 60 seconds and try again. If you are doing a live interview, consider adding a billing account in Google AI Studio to increase your limit to 1000 RPM."}) + "\n"
            return
            
        msg = response.choices[0].message
        messages.append(msg)
        
        loop_count = 0
        # 2. Agentic Boundary: Limit tool calls to prevent infinite loops
        while msg.tool_calls and loop_count < 10:
            loop_count += 1
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                # YIELD TOOL CALL EVENT TO FRONTEND
                yield json.dumps({"type": "tool_call", "name": tool_name}) + "\n"
                
                # Extract coordinates to send to the frontend map!
                if 'latitude' in tool_args and 'longitude' in tool_args:
                    map_markers.append({
                        "type": tool_name,
                        "lat": tool_args['latitude'],
                        "lng": tool_args['longitude'],
                        "label": "AI Inspection Point"
                    })
                    
                try:
                    mcp_result = await session.call_tool(tool_name, tool_args)
                    tool_output = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
                except Exception as e:
                    tool_output = f"Error executing tool {tool_name}: {str(e)}"
                
                # If we found cooling spots, extract their coordinates too!
                if tool_name == "find_cooling_spots" and not "Error" in tool_output:
                    try:
                        spots = json.loads(tool_output)
                        if 'elements' in spots:
                            for el in spots['elements'][:20]: # Show up to 20 spots on the map
                                if 'lat' in el and 'lon' in el:
                                    tags = el.get('tags', {})
                                    name = tags.get('name', tags.get('amenity', tags.get('leisure', 'Cooling Spot')))
                                    map_markers.append({
                                        "type": "cooling_spot",
                                        "lat": el['lat'],
                                        "lng": el['lon'],
                                        "label": name,
                                        "tags": tags,
                                        "dist": el.get("distance_m")
                                    })
                    except:
                        pass
                
                # If we got a forecast, extract the daily forecast data to render a chart!
                if tool_name == "get_heatwave_forecast" and not "error" in tool_output:
                    try:
                        forecast_res = json.loads(tool_output)
                        if 'daily_forecast' in forecast_res:
                            forecast_data = forecast_res['daily_forecast']
                    except:
                        pass
                        
                if tool_name == "get_air_quality_forecast" and not "error" in tool_output:
                    try:
                        aq_res = json.loads(tool_output)
                        if 'aq_forecast' in aq_res:
                            aq_forecast_data = aq_res['aq_forecast']
                    except:
                        pass
                        
                if tool_name == "get_urban_heat_island_heatmap" and not "error" in tool_output:
                    try:
                        heatmap_res = json.loads(tool_output)
                        if 'heatmap_geojson' in heatmap_res:
                            uhi_geojson = heatmap_res['heatmap_geojson']
                    except:
                        pass
                        
                if tool_name == "get_walking_route" and not "error" in tool_output:
                    try:
                        route_res = json.loads(tool_output)
                        if 'route_geojson' in route_res:
                            route_geojson = route_res['route_geojson']
                    except:
                        pass
                
                if tool_name == "generate_walkability_isochrone" and not "error" in tool_output:
                    try:
                        iso_res = json.loads(tool_output)
                        if 'isochrone_geojson' in iso_res:
                            isochrone_geojson = iso_res['isochrone_geojson']
                    except:
                        pass
                        
                if tool_name == "get_heat_safety_advice" and not "error" in tool_output.lower():
                    safety_advice_data = tool_output
                    
                if tool_name == "get_occupational_heat_guidance" and not "error" in tool_output.lower():
                    try:
                        work_rest_guidance = json.loads(tool_output)
                    except:
                        pass
                        
                if tool_name == "get_weather_and_heat_risk" and not "error" in tool_output.lower():
                    try:
                        current_weather_data = json.loads(tool_output)
                    except:
                        pass
                        
                if tool_name == "trigger_symptom_triage_ui":
                    symptom_triage_ui = True
                
                # IMPORTANT: Truncate massive GeoJSON payloads before sending back to LLM to prevent TPM Rate Limits!
                llm_tool_output = tool_output
                try:
                    parsed_output = json.loads(tool_output)
                    if 'heatmap_geojson' in parsed_output:
                        parsed_output['heatmap_geojson'] = "GeoJSON data successfully extracted and sent to frontend."
                    if 'isochrone_geojson' in parsed_output:
                        parsed_output['isochrone_geojson'] = "GeoJSON data successfully extracted and sent to frontend."
                    if 'route_geojson' in parsed_output:
                        parsed_output['route_geojson'] = "GeoJSON data successfully extracted and sent to frontend."
                    llm_tool_output = json.dumps(parsed_output)
                except:
                    pass

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": llm_tool_output
                })
                
            try:
                response = await get_gemini_response(messages, llm_tools)
            except Exception as e:
                yield json.dumps({"type": "final", "text": "⚠️ **Google Gemini API Rate Limit Exceeded.** You are making too many requests too quickly on the Free Tier (15 requests per minute). Please wait 60 seconds and try again."}) + "\n"
                return
                
            msg = response.choices[0].message
            messages.append(msg)
            
        if loop_count >= 10:
            msg.content = "⚠️ **Security Alert:** The AI agent exceeded the maximum allowed tool iterations (10) and was forcefully terminated to prevent resource exhaustion. Here is the data collected so far."
            
        final_data = {
            "type": "final",
            "text": msg.content,
            "markers": map_markers,
            "forecast": forecast_data,
            "aq_forecast": aq_forecast_data,
            "uhi_geojson": uhi_geojson,
            "route_geojson": route_geojson,
            "isochrone_geojson": isochrone_geojson,
            "safety_advice": safety_advice_data,
            "work_rest_guidance": work_rest_guidance,
            "current_weather": current_weather_data,
            "symptom_triage": symptom_triage_ui
        }
        yield json.dumps(final_data) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post('/api/default-map')
async def default_map_endpoint(req: dict):
    # Used to populate the SSOT and default map state on load
    session = app_state.get('session')
    if not session:
        raise HTTPException(status_code=500, detail='MCP Server not connected')
    
    lat = req.get('lat')
    lng = req.get('lng')
    
    if lat is None or lng is None:
        # If there's absolutely no location (GPS failed, IP failed), return empty map state
        return {
            "current_weather": None,
            "uhi_geojson": None,
            "isochrone_geojson": None,
            "markers": []
        }
    
    # 1. Fetch current weather for SSOT
    weather_res = await session.call_tool('get_weather_and_heat_risk', {'latitude': lat, 'longitude': lng})
    import json
    current_weather = None
    try:
        current_weather = json.loads(''.join([c.text for c in weather_res.content if c.type == 'text']))
    except:
        pass
        
    # 2. Fetch UHI Map (Reduced to 400m to prevent Overpass timeouts in ultra-dense cities like Paris)
    uhi_res = await session.call_tool('get_urban_heat_island_heatmap', {'latitude': lat, 'longitude': lng, 'radius': 400})
    uhi_geojson = None
    try:
        uhi_data = json.loads(''.join([c.text for c in uhi_res.content if c.type == 'text']))
        uhi_geojson = uhi_data.get('heatmap_geojson')
    except:
        pass
        
    # 3. Fetch Cooling Spots (Increased to 5000m to ensure spots are found in less dense areas)
    spots_res = await session.call_tool('find_cooling_spots', {'latitude': lat, 'longitude': lng, 'radius': 5000})
    markers = []
    try:
        spots_data = json.loads(''.join([c.text for c in spots_res.content if c.type == 'text']))
        for el in spots_data.get('elements', [])[:20]:
            if 'lat' in el and 'lon' in el:
                tags = el.get('tags', {})
                name = tags.get('name', tags.get('amenity', tags.get('leisure', 'Cooling Spot')))
                # Filter out Unnamed Spot
                if 'Unnamed Spot' in name or name == 'Cooling Spot':
                    name = 'Nearby park' if tags.get('leisure') == 'park' else 'Cooling center'
                markers.append({
                    'type': 'cooling_spot',
                    'lat': el['lat'],
                    'lng': el['lon'],
                    'label': name,
                    'tags': tags,
                    'dist': el.get('distance_m')
                })
    except:
        pass
        
    return {
        'current_weather': current_weather,
        'uhi_geojson': uhi_geojson,
        'markers': markers
    }
