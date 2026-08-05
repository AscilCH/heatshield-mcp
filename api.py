import asyncio
import os
import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession
import typing

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

app_state = {}

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
    raise HTTPException(status_code=503, detail="API is overloaded or rate limited. Please try again.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🚀 Starting HeatShield Backend...")
    server_params = StdioServerParameters(command="python", args=["src/heatshield/server.py"])
    
    # We use an ExitStack pattern because stdio_client is an async context manager
    # but we need it to stay open for the whole lifespan of the FastAPI app.
    # A simple trick is to keep it running in a background task, or just block here?
    # No, FastAPI lifespan expects yield. So we can just nest it.
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to HeatShield MCP Server!")
            
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
    userLocation: typing.Optional[dict] = None

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    session = app_state.get('session')
    llm_tools = app_state.get('llm_tools')
    
    if not session:
        raise HTTPException(status_code=500, detail="MCP Server not connected")
        
    system_prompt = "You are HeatShield, an urban heat wave safety assistant. Use geospatial tools to accurately assess risk and answer the user's queries."
    
    if req.userLocation:
        lat = req.userLocation.get('lat')
        lng = req.userLocation.get('lng')
        system_prompt += f" The user's device is currently located at Latitude {lat}, Longitude {lng}. If they ask for information 'near me', 'here', or for their current location, you MUST use these exact coordinates directly in your tool calls without geocoding."

    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(req.history)
    messages.append({"role": "user", "content": req.message})
    
    # Track map coordinates for the frontend
    map_markers = []
    forecast_data = None
    aq_forecast_data = None
    heatmap_geojson = None
    
    response = await get_gemini_response(messages, llm_tools)
    msg = response.choices[0].message
    messages.append(msg)
    
    while msg.tool_calls:
        for tool_call in msg.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)
            
            # Extract coordinates to send to the frontend map!
            if 'latitude' in tool_args and 'longitude' in tool_args:
                map_markers.append({
                    "type": tool_name,
                    "lat": tool_args['latitude'],
                    "lng": tool_args['longitude'],
                    "label": "AI Inspection Point"
                })
                
            mcp_result = await session.call_tool(tool_name, tool_args)
            tool_output = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
            
            # If we found cooling spots, extract their coordinates too!
            if tool_name == "find_cooling_spots" and not "Error" in tool_output:
                try:
                    spots = json.loads(tool_output)
                    if 'elements' in spots:
                        for el in spots['elements'][:15]: # Show top 15 spots
                            if 'lat' in el and 'lon' in el:
                                tags = el.get('tags', {})
                                name = tags.get('name', tags.get('amenity', tags.get('leisure', 'Cooling Spot')))
                                map_markers.append({
                                    "type": "cooling_spot",
                                    "lat": el['lat'],
                                    "lng": el['lon'],
                                    "label": name
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
                        heatmap_geojson = heatmap_res['heatmap_geojson']
                except:
                    pass
            
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "name": tool_name,
                "content": tool_output
            })
            
        response = await get_gemini_response(messages, llm_tools)
        msg = response.choices[0].message
        messages.append(msg)
        
    return {
        "text": msg.content,
        "markers": map_markers,
        "forecast": forecast_data,
        "aq_forecast": aq_forecast_data,
        "heatmap_geojson": heatmap_geojson,
        "history": req.history + [
            {"role": "user", "content": req.message},
            {"role": "assistant", "content": msg.content}
        ]
    }
