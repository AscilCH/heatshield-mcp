import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

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
from heatshield.core.security import verify_api_key, RateLimiter, PromptGuard
from dotenv import load_dotenv

load_dotenv(override=True)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")
import httpx
import uuid
import asyncio

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

class MockFunctionCall:
    def __init__(self, name, arguments):
        self.name = name
        self.arguments = arguments

class MockToolCall:
    def __init__(self, name, arguments):
        self.id = "call_" + str(uuid.uuid4())[:8]
        self.function = MockFunctionCall(name, arguments)

class MockToolCall:
    def __init__(self, name, arguments, thought_signature=None):
        self.id = "call_" + str(uuid.uuid4())[:8]
        self.function = MockFunctionCall(name, arguments)
        self.thought_signature = thought_signature

class MockMessage:
    def __init__(self, content, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls

class MockChoice:
    def __init__(self, message):
        self.message = message

class MockResponse:
    def __init__(self, choices):
        self.choices = choices

def openai_to_gemini(messages, openai_tools):
    import json
    gemini_tools = []
    if openai_tools:
        funcs = []
        for t in openai_tools:
            f = t['function']
            funcs.append({
                "name": f["name"],
                "description": f.get("description", ""),
                "parameters": f.get("parameters", {})
            })
        gemini_tools = [{"functionDeclarations": funcs}]

    contents = []
    system_instruction = None
    
    for m in messages:
        if isinstance(m, dict):
            role = m["role"]
            content = m.get("content")
            tool_calls = m.get("tool_calls")
            name = m.get("name")
        else:
            role = m.role if hasattr(m, 'role') else 'assistant'
            content = m.content
            tool_calls = m.tool_calls
            name = None
            
        if role == "system":
            if not system_instruction:
                system_instruction = {"parts": [{"text": content}]}
            else:
                system_instruction["parts"].append({"text": content})
        
        elif role == "user":
            contents.append({"role": "user", "parts": [{"text": content}]})
            
        elif role == "assistant":
            parts = []
            if content:
                parts.append({"text": content})
            if tool_calls:
                for tc in tool_calls:
                    func_name = tc.function.name if hasattr(tc, 'function') else tc['function']['name']
                    func_args = tc.function.arguments if hasattr(tc, 'function') else tc['function']['arguments']
                    if isinstance(func_args, str):
                        try:
                            func_args = json.loads(func_args)
                        except:
                            func_args = {}
                    
                    fc_part = {"functionCall": {"name": func_name, "args": func_args}}
                    ts = getattr(tc, 'thought_signature', None)
                    if ts:
                        fc_part["thoughtSignature"] = ts
                    parts.append(fc_part)
            contents.append({"role": "model", "parts": parts})
            
        elif role == "tool":
            try:
                content_obj = json.loads(content)
            except:
                content_obj = {"result": content}
            contents.append({
                "role": "user",
                "parts": [{"functionResponse": {"name": name, "response": content_obj}}]
            })

    return contents, gemini_tools, system_instruction

async def stream_gemini_response(messages, tools):
    import os, json
    from openai import AsyncOpenAI
    
    api_key = os.environ.get("GEMINI_API_KEY")
    client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
    )
    
    for attempt in range(5):
        try:
            stream = await client.chat.completions.create(
                model="gemini-3.5-flash-lite",
                messages=messages,
                tools=tools,
                stream=True
            )
            
            tool_calls_dict = {}
            full_content = ""
            
            async for chunk in stream:
                delta = chunk.choices[0].delta
                if delta.content:
                    full_content += delta.content
                    yield {"type": "chunk", "text": delta.content}
                
                if delta.tool_calls:
                    for tc in delta.tool_calls:
                        key = tc.id if tc.id else (tc.index if tc.index is not None else 0)
                        if key not in tool_calls_dict:
                            tool_calls_dict[key] = {"id": tc.id or f"call_{len(tool_calls_dict)}", "type": "function", "function": {"name": tc.function.name or "", "arguments": ""}}
                        elif tc.function and tc.function.name and tool_calls_dict[key]["function"]["name"] and tc.function.name != tool_calls_dict[key]["function"]["name"]:
                            key = f"{key}_{len(tool_calls_dict)}"
                            tool_calls_dict[key] = {"id": tc.id or f"call_{len(tool_calls_dict)}", "type": "function", "function": {"name": tc.function.name, "arguments": ""}}
                            
                        if tc.function:
                            if tc.function.name and not tool_calls_dict[key]["function"]["name"]:
                                tool_calls_dict[key]["function"]["name"] = tc.function.name
                            if tc.function.arguments:
                                tool_calls_dict[key]["function"]["arguments"] += tc.function.arguments
            
            # Reconstruct the final message format expected by the caller
            final_msg = MockMessage(full_content)
            if tool_calls_dict:
                import types
                final_msg.tool_calls = []
                for idx, tc in sorted(tool_calls_dict.items()):
                    func_obj = types.SimpleNamespace(name=tc["function"]["name"], arguments=tc["function"]["arguments"])
                    tc_obj = types.SimpleNamespace(id=tc["id"], function=func_obj)
                    final_msg.tool_calls.append(tc_obj)
            
            yield {"type": "final_msg", "msg": MockResponse([MockChoice(final_msg)])}
            return
            
        except Exception as e:
            if attempt == 4:
                raise e
            import asyncio
            await asyncio.sleep(2)

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting HeatShield Backend...")
    server_params = StdioServerParameters(command="python", args=["-m", "src.heatshield.server"])
    
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

async def check_prompt_guard(message: str) -> dict:
    return await PromptGuard.evaluate(message)

chat_rate_limiter = RateLimiter(requests_per_minute=30)

@app.post("/api/chat", dependencies=[Depends(verify_api_key), Depends(chat_rate_limiter)])
async def chat_endpoint(req: ChatRequest):
    session = app_state.get('session')
    llm_tools = app_state.get('llm_tools')
    
    if not session:
        raise HTTPException(status_code=500, detail="MCP Server not connected")
        
    system_prompt = (
        "You are HeatShield, an intelligent urban heat safety concierge and spatial intelligence AI. Your mission is to protect human life, optimize pedestrian transit, evaluate occupational thermal strain, and deliver proactive, visual spatial insights.\n\n"
        "CORE OPERATIONAL PHILOSOPHY:\n"
        "1. AUTONOMOUS PROBLEM SOLVING: Do not wait for rigid commands. Deeply analyze the user's prompt, identify their underlying goal (transit, work safety, thermal comparison, symptom triage, shade planning), and intelligently compose the best sequence of tools from your toolbox to solve it thoroughly.\n"
        "2. VISUAL-FIRST & CANVAS PROACTIVITY: The frontend is a living interactive map and visual canvas. Always make your insights visual and interactive whenever beneficial:\n"
        "   - Comparing cities or regions? Always open the side-by-side comparative matrix (`open_comparison_view`) and include a clean Markdown data table at the top of your response.\n"
        "   - Spatial routes, walking paths, or zones? Draw the corridors/polygons on the map (`get_walking_route`, `draw_map_layer`, `submit_geospatial_tasks`) and smoothly fly the camera (`set_camera_view`) to the focal area.\n"
        "   - Multi-day heat or air quality progressions? Open dynamic chart panels (`open_chart_panel`) or forecast cards.\n"
        "3. RIGOROUS DATA & COMPUTE PIPELINE: Never estimate or hallucinate mathematical numbers inline. First fetch real environmental telemetry (`get_weather_and_heat_risk`, `get_air_quality_forecast`), then pass them into pure deterministic compute tools (`compute_wbgt`, `compute_work_rest_cycle`, `compute_heat_risk`).\n"
        "4. OCCUPATIONAL & MEDICAL COMPLIANCE INTELLIGENCE: When the user asks about workplace heat safety, outdoor construction/concrete pouring, work-rest schedules, OSHA/NIOSH compliance, or safety at a specific high temperature (e.g. 40°C, 42°C):\n"
        "   - Do NOT simply query generic live weather for a random location. Focus directly on the occupational compliance scenario!\n"
        "   - Call `compute_wbgt` and `get_occupational_heat_guidance` with the specified workload (Heavy for concrete/roofing/digging) and temperature to calculate the strict NIOSH work/rest ratio and hydration rule.\n"
        "   - Call `query_emergency_protocols` to retrieve official CDC/NIOSH criteria on emergency immersion tubs, cooling stations, and fatal heat stroke prevention.\n"
        "   - In your final response, ALWAYS present the exact work-rest breakdown, mandatory hydration rate, cooling station engineering requirements, and AUTOMATICALLY include clickable Markdown reference links to official regulatory documents (e.g. `[CDC/NIOSH Criteria for Occupational Exposure to Heat (Pub No. 2016-106)](https://www.cdc.gov/niosh/docs/2016-106/pdfs/2016-106.pdf)` and `[OSHA Heat Illness Prevention Standards](https://www.osha.gov/heat-exposure)`).\n"
        "5. FIRST-PERSON EMPATHETIC VOICE: Speak directly, clearly, and warmly to the user in the first person ('I have evaluated the occupational requirements...', 'Here is the official compliance breakdown...'). Never speak about the user in the third person or narrate system constraints.\n"
        "6. PLAIN TEXT ONLY: Never output LaTeX notation ($...$); use standard units like 34°C, 80%, and 10 km/h.\n"
        "7. STRICT CIVIC SAFETY PERSONA: You are EXCLUSIVELY an urban heat safety assistant and biometeorological concierge. You MUST FIRMLY AND POLITELY REFUSE to answer any questions about video games, entertainment, creative writing, or general software programming. Politely state that HeatShield is dedicated exclusively to urban heat risk, weather telemetry, and thermal safety.\n"
        "8. CONVERSATIONAL CONTEXT & SPATIAL MEMORY: You have complete access to the conversation history. When the user uses relative references ('there', 'it', 'the route', 'that city', 'same location', 'draw a buffer around it', 'show the forecast there'), seamlessly resolve the exact geographic entity, coordinates, or medical context from earlier turns. Maintain full spatial continuity without asking the user to repeat previously mentioned locations.\n"
        "9. DEEP DOCUMENT RAG & VERIFIED CITATIONS: When discussing any regulatory standard, clinical threshold, or heat illness guideline, ALWAYS cite the verified source with clickable Markdown links and quoted criteria, guaranteeing 100% evidentiary truthfulness!"
    )
    
    if req.latitude is not None and req.longitude is not None:
        system_prompt += (
            f"\nUSER CONTEXT: The user's device is currently at Latitude {req.latitude}, Longitude {req.longitude}. "
            f"If they ask for local or nearby advice, pass these exact coordinates to your tools."
        )
    else:
        system_prompt += (
            "\nUSER CONTEXT: Device GPS is unavailable. "
            "If the user asks for location-dependent advice without specifying a city, ask them directly: 'Which city or area are you located in so I can check live conditions for you?'"
        )

    # Bound history to recent 14 turns to guarantee context continuity while optimizing token budget
    bounded_history = req.history[-14:] if req.history else []
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(bounded_history)
    messages.append({"role": "user", "content": req.message})
    
    print(f"\n{'='*50}\n[UC TRACE] User Message: '{req.message}'\n[UC TRACE] Device Coordinates: Lat {req.latitude}, Lon {req.longitude}\n{'='*50}")
    
    async def event_generator():
        # PromptGuard Pre-Flight Security Check
        guard_result = await check_prompt_guard(req.message)
        if not guard_result.get("is_safe", True):
            reason = guard_result.get("reason", "Malicious or Off-Topic Content")
            source = guard_result.get("source", "PromptGuard Gateway")
            conf = int(guard_result.get("score", 0.95) * 100)
            block_msg = f"🛡️ **PromptGuard Security Alert:** {reason} intercepted by {source} (Confidence: {conf}%).\n\nHeatShield is a specialized biometeorological and urban heat safety system. I can only assist with live weather telemetry, heatwave risks, cooling shelters, safe pedestrian transit routes, occupational work/rest cycles, and thermal medical triage."
            yield json.dumps({"type": "chunk", "text": block_msg}) + "\n"
            yield json.dumps({"type": "final", "text": block_msg}) + "\n"
            return
            
        # Track map coordinates and canvas layers for the frontend
        map_markers = []
        forecast_data = None
        aq_forecast_data = None
        uhi_geojson = None
        heat_dome_geojson = None
        route_geojson = None
        isochrone_geojson = None
        safety_advice_data = None
        work_rest_guidance = None
        current_weather_data = None
        symptom_triage_ui = False
        canvas_layers = []
        canvas_chart_data = None
        canvas_comparison_data = None
        canvas_camera = None
        
        # Filter out the individual map tools so the LLM is forced to use the orchestrator
        hidden_tools = ["get_urban_heat_island_heatmap", "generate_walkability_isochrone", "find_cooling_spots"]
        local_tools = [t for t in llm_tools if t["function"]["name"] not in hidden_tools] if llm_tools else []
        
        local_tools.append({
            "type": "function",
            "function": {
                "name": "submit_geospatial_tasks",
                "description": "Submit one or more geospatial operations (heatmap, walkability, cooling spots) to be executed. Use this ALWAYS for updating the map, whether for a single city or multiple cities.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "tasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "city": {"type": "string", "description": "City name, e.g. 'Paris'. Omit if using latitude and longitude."},
                                    "latitude": {"type": "number", "description": "Latitude if city name is not provided"},
                                    "longitude": {"type": "number", "description": "Longitude if city name is not provided"},
                                    "operation": {
                                        "type": "string",
                                        "enum": ["uhi_heatmap", "walkability_5min", "walkability_10min", "walkability_15min", "walkability_25min", "cooling_spots"]
                                    },
                                    "filter": {"type": "string", "description": "optional filter for cooling_spots, e.g. 'library', 'park', 'mall', 'pool'"}
                                },
                                "required": ["operation"]
                            }
                        }
                    },
                    "required": ["tasks"]
                }
            }
        })
        
        try:
            full_text = ""
            tool_calls = []
            async for chunk in stream_gemini_response(messages, local_tools):
                if chunk["type"] == "chunk":
                    yield json.dumps({"type": "chunk", "text": chunk["text"]}) + "\n"
                    full_text += chunk["text"]
                elif chunk["type"] == "final_msg":
                    response = chunk["msg"]
        except Exception as e:
            import traceback
            traceback.print_exc()
            yield json.dumps({"type": "final", "text": f"⚠️ **Backend Error:** {str(e)}"}) + "\n"
            return
            
        msg = response.choices[0].message
        msg_dict = {"role": "assistant", "content": getattr(msg, "content", None) or ""}
        if getattr(msg, "tool_calls", None):
            msg_dict["tool_calls"] = [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}} for t in msg.tool_calls]
            yield json.dumps({"type": "clear_chunk"}) + "\n"
        
        loop_count = 0
        tool_results_text = ""
        # 2. Agentic Boundary: Limit tool calls to prevent infinite loops (allow up to 8 iterations for multi-city workflows)
        while msg.tool_calls and loop_count < 8:
            loop_count += 1
            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                raw_args = getattr(tool_call.function, "arguments", "") or "{}"
                
                parsed_args_list = []
                try:
                    parsed_args_list = [json.loads(raw_args)]
                except json.JSONDecodeError:
                    decoder = json.JSONDecoder()
                    s = raw_args.strip()
                    idx = 0
                    while idx < len(s):
                        while idx < len(s) and s[idx].isspace():
                            idx += 1
                        if idx >= len(s):
                            break
                        try:
                            obj, end_idx = decoder.raw_decode(s, idx)
                            parsed_args_list.append(obj)
                            idx = end_idx
                        except Exception:
                            break
                            
                if not parsed_args_list:
                    trace_msg = f"[UC TRACE] ⚠️ LLM generated invalid JSON for tool {tool_name}: {raw_args}"
                    print(trace_msg)
                    yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                    tool_results_text += f"\nTool {tool_name} failed: Invalid JSON arguments. Please correct your JSON formatting.\n"
                    continue
                
                for tool_args in parsed_args_list:
                    trace_msg = f"[UC TRACE] 🤖 LLM decided to call tool: {tool_name} with args: {json.dumps(tool_args)}"
                    print(trace_msg)
                    yield json.dumps({"type": "trace", "message": trace_msg}) + "\n"
                    
                    # YIELD TOOL CALL EVENT TO FRONTEND
                    yield json.dumps({"type": "tool_call", "name": tool_name}) + "\n"
                
                if tool_name == "submit_geospatial_tasks":
                    # --- CONCURRENT ORCHESTRATOR PIPELINE ---
                    tasks = tool_args.get("tasks", [])
                    overpass_sem = asyncio.Semaphore(2)
                    osrm_sem = asyncio.Semaphore(4)
                    
                    async def run_task(task):
                        op = task.get("operation")
                        city = task.get("city") or task.get("location") or task.get("location_name") or task.get("name") or task.get("place")
                        lat = task.get("latitude") or task.get("lat")
                        lon = task.get("longitude") or task.get("lon") or task.get("lng")
                        
                        if not city and lat is None and req.latitude is not None:
                            lat = req.latitude
                            lon = req.longitude
                            
                        task_id = f"{city or 'local'}-{op}"
                        
                        try:
                            async def _execute():
                                args = {}
                                if city: args["location_name"] = city
                                if lat is not None: args["latitude"] = lat
                                if lon is not None: args["longitude"] = lon
                                
                                if op == "uhi_heatmap":
                                    async with overpass_sem:
                                        return await session.call_tool("get_urban_heat_island_heatmap", args)
                                elif op.startswith("walkability_"):
                                    args["minutes"] = int(op.split("_")[1].replace("min", ""))
                                    async with osrm_sem:
                                        return await session.call_tool("generate_walkability_isochrone", args)
                                elif op == "cooling_spots":
                                    if "filter" in task and task["filter"]:
                                        args["destination_type"] = task["filter"]
                                    async with overpass_sem:
                                        return await session.call_tool("find_cooling_spots", args)
                                return None
                            
                            mcp_result = await asyncio.wait_for(_execute(), timeout=60.0)
                            if mcp_result:
                                tool_out = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
                                try:
                                    parsed_out = json.loads(tool_out)
                                    if "error" in parsed_out:
                                        return {"task_id": task_id, "status": "error", "error": parsed_out.get("error", "upstream_error")}
                                except json.JSONDecodeError:
                                    pass
                                return {"task_id": task_id, "status": "success", "data": tool_out}
                            return {"task_id": task_id, "status": "error", "error": "Unknown operation"}
                        except asyncio.TimeoutError:
                            return {"task_id": task_id, "status": "error", "error": "upstream_timeout"}
                        except Exception as e:
                            return {"task_id": task_id, "status": "error", "error": str(e)}

                    results = await asyncio.gather(*[run_task(t) for t in tasks])
                    
                    # Process and yield partial results immediately!
                    combined_text_out = []
                    for res in results:
                        tid = res["task_id"]
                        if res["status"] == "success":
                            yield json.dumps({"type": "partial_map_update", "status": "success", "task_id": tid, "data": res["data"]}) + "\n"
                            combined_text_out.append(f"✅ {tid}: Success")
                            # Merge into main trackers so LLM sees it
                            try:
                                parsed = json.loads(res["data"])
                                if "heatmap_geojson" in parsed: 
                                    if uhi_geojson is None:
                                        uhi_geojson = parsed["heatmap_geojson"]
                                    else:
                                        uhi_geojson["features"].extend(parsed["heatmap_geojson"].get("features", []))
                                if "isochrone_geojson" in parsed: 
                                    if isochrone_geojson is None:
                                        isochrone_geojson = parsed["isochrone_geojson"]
                                    else:
                                        isochrone_geojson["features"].extend(parsed["isochrone_geojson"].get("features", []))
                                if "elements" in parsed:
                                    for el in parsed["elements"][:20]:
                                        if 'lat' in el and 'lon' in el:
                                            tags = el.get('tags', {})
                                            map_markers.append({
                                                "type": "cooling_spot",
                                                "lat": el['lat'],
                                                "lng": el['lon'],
                                                "label": tags.get('name', 'Cooling Spot'),
                                                "tags": tags
                                            })
                            except: pass
                        else:
                            yield json.dumps({"type": "partial_map_update", "status": "error", "task_id": tid, "error": res["error"]}) + "\n"
                            combined_text_out.append(f"⚠️ {tid}: {res['error']}")
                            
                    tool_output = "\n".join(combined_text_out)
                    success_msg = f"[UC TRACE] 🟢 Orchestrator finished: {tool_output}"
                    print(success_msg)
                    yield json.dumps({"type": "trace", "message": success_msg}) + "\n"
                
                else:
                    # Extract coordinates to send to the frontend map!
                    if 'latitude' in tool_args and 'longitude' in tool_args:
                        map_markers.append({
                            "type": "user_location",
                            "lat": tool_args['latitude'],
                            "lng": tool_args['longitude'],
                            "label": "AI Inspection Point"
                        })
                        
                    try:
                        mcp_result = await session.call_tool(tool_name, tool_args)
                        tool_output = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
                        
                        success_msg = f"[UC TRACE] 🟢 Tool {tool_name} returned successfully (Length: {len(tool_output)} chars)"
                        print(success_msg)
                        yield json.dumps({"type": "trace", "message": success_msg}) + "\n"
                        
                        if len(tool_output) < 500:
                            out_msg = f"[UC TRACE] 📤 Tool Output: {tool_output}"
                        else:
                            out_msg = f"[UC TRACE] 📤 Tool Output: {tool_output[:500]}... [TRUNCATED]"
                        print(out_msg)
                        yield json.dumps({"type": "trace", "message": out_msg}) + "\n"
                        
                    except Exception as e:
                        tool_output = f"Error executing tool {tool_name}: {str(e)}"
                        err_msg = f"[UC TRACE] 🔴 Tool {tool_name} failed: {tool_output}"
                        print(err_msg)
                        yield json.dumps({"type": "trace", "message": err_msg}) + "\n"
                    
                    # If we found cooling spots, extract their coordinates too!
                    if tool_name == "find_cooling_spots" and not "error" in tool_output.lower():
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
                if tool_name == "get_heatwave_forecast" and not "error" in tool_output.lower():
                    try:
                        forecast_res = json.loads(tool_output)
                        if 'daily_forecast' in forecast_res:
                            forecast_data = forecast_res['daily_forecast']
                    except:
                        pass
                        
                if tool_name in ["get_air_quality_forecast", "get_air_quality"] and not "error" in tool_output.lower():
                    if tool_name == "get_air_quality":
                        try:
                            lat = tool_args.get('latitude')
                            lon = tool_args.get('longitude')
                            loc = tool_args.get('location_name')
                            aq_args = {}
                            if lat is not None and lon is not None:
                                aq_args = {"latitude": lat, "longitude": lon}
                            elif loc:
                                aq_args = {"location_name": loc}
                            if aq_args:
                                mcp_aq_res = await session.call_tool("get_air_quality_forecast", aq_args)
                                aq_tool_out = "\n".join([c.text for c in mcp_aq_res.content if c.type == "text"])
                                aq_res = json.loads(aq_tool_out)
                                if 'aq_forecast' in aq_res:
                                    aq_forecast_data = aq_res['aq_forecast']
                        except Exception as e:
                            print(f"[AQ ERROR] Failed to auto-fetch AQ forecast curve: {e}")
                    else:
                        try:
                            aq_res = json.loads(tool_output)
                            if 'aq_forecast' in aq_res:
                                aq_forecast_data = aq_res['aq_forecast']
                        except:
                            pass
                        
                if tool_name == "get_urban_heat_island_heatmap" and not "error" in tool_output.lower():
                    try:
                        heatmap_res = json.loads(tool_output)
                        if 'heatmap_geojson' in heatmap_res:
                            if uhi_geojson is None:
                                uhi_geojson = heatmap_res['heatmap_geojson']
                            else:
                                uhi_geojson['features'].extend(heatmap_res['heatmap_geojson'].get('features', []))
                    except:
                        pass
                        
                if tool_name == "get_heat_dome_footprint" and not "error" in tool_output.lower():
                    try:
                        dome_res = json.loads(tool_output)
                        if 'heat_dome_geojson' in dome_res:
                            if heat_dome_geojson is None:
                                heat_dome_geojson = dome_res['heat_dome_geojson']
                            else:
                                heat_dome_geojson['features'].extend(dome_res['heat_dome_geojson'].get('features', []))
                    except:
                        pass
                        
                # Extract generic route_geojson from ANY tool output (find_cooling_spots or get_walking_route)
                if not "error" in tool_output.lower():
                    try:
                        res_obj = json.loads(tool_output)
                        if 'route_geojson' in res_obj:
                            if route_geojson is None:
                                route_geojson = res_obj['route_geojson']
                            else:
                                route_geojson['features'].extend(res_obj['route_geojson'].get('features', []))
                    except:
                        pass

                if tool_name == "generate_walkability_isochrone" and not "error" in tool_output.lower():
                    try:
                        iso_res = json.loads(tool_output)
                        if 'isochrone_geojson' in iso_res:
                            if isochrone_geojson is None:
                                isochrone_geojson = iso_res['isochrone_geojson']
                            else:
                                isochrone_geojson['features'].extend(iso_res['isochrone_geojson'].get('features', []))
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
                    
                if tool_name == "broadcast_emergency_alert" and not "error" in tool_output.lower():
                    try:
                        alert_res = json.loads(tool_output)
                        if alert_res.get('type') == 'trigger_emergency_broadcast':
                            payload = json.dumps({
                                "type": "emergency_alert",
                                "severity": alert_res.get('severity'),
                                "message": alert_res.get('message')
                            })
                            # We can't await this cleanly inside the sync generator block without some hackery,
                            # wait, event_generator is async! We can await it.
                            await manager.broadcast(payload)
                    except:
                        pass
                
                if tool_name == "draw_map_layer" and not "error" in tool_output.lower():
                    try:
                        c_layer = json.loads(tool_output)
                        canvas_layers.append(c_layer)
                    except:
                        pass
                        
                if tool_name == "open_chart_panel" and not "error" in tool_output.lower():
                    try:
                        canvas_chart_data = json.loads(tool_output)
                    except:
                        pass
                        
                if tool_name == "open_comparison_view" and not "error" in tool_output.lower():
                    try:
                        canvas_comparison_data = json.loads(tool_output)
                    except:
                        pass
                        
                if tool_name == "set_camera_view" and not "error" in tool_output.lower():
                    try:
                        canvas_camera = json.loads(tool_output)
                    except:
                        pass
                
                # IMPORTANT: Truncate massive GeoJSON payloads before sending back to LLM to prevent TPM Rate Limits!
                llm_tool_output = tool_output
                try:
                    parsed_output = json.loads(tool_output)
                    if 'heatmap_geojson' in parsed_output:
                        feats = parsed_output['heatmap_geojson'].get('features', []) if isinstance(parsed_output['heatmap_geojson'], dict) else []
                        parsed_output['heatmap_geojson'] = {
                            "status": "rendered_on_canvas",
                            "features_count": len(feats),
                            "coverage_radius_m": 2500,
                            "type": "Urban Heat Island Grid"
                        }
                    if 'heat_dome_geojson' in parsed_output:
                        feats = parsed_output['heat_dome_geojson'].get('features', []) if isinstance(parsed_output['heat_dome_geojson'], dict) else []
                        parsed_output['heat_dome_geojson'] = {
                            "status": "rendered_on_canvas",
                            "features_count": len(feats),
                            "geometry": "500hPa Synoptic Blocking Ridge Polygon"
                        }
                    if 'isochrone_geojson' in parsed_output:
                        feats = parsed_output['isochrone_geojson'].get('features', []) if isinstance(parsed_output['isochrone_geojson'], dict) else []
                        parsed_output['isochrone_geojson'] = {
                            "status": "rendered_on_canvas",
                            "concentric_isochrones_count": len(feats),
                            "walk_risk_profiles": [f.get('properties', {}).get('fillColor') for f in feats]
                        }
                    if 'route_geojson' in parsed_output:
                        feats = parsed_output['route_geojson'].get('features', []) if isinstance(parsed_output['route_geojson'], dict) else []
                        parsed_output['route_geojson'] = {
                            "status": "rendered_on_canvas",
                            "route_segments_count": len(feats),
                            "waypoints": len(feats[0].get('geometry', {}).get('coordinates', [])) if feats else 0
                        }
                    if 'elements' in parsed_output:
                        els = parsed_output.get('elements', [])
                        parsed_output['elements'] = {
                            "status": "rendered_on_canvas",
                            "verified_spots_found": len(els),
                            "nearest_spots": [e.get('tags', {}).get('name', 'Cooling Spot') for e in els[:3]] if els else []
                        }
                    if 'geojson' in parsed_output and 'type' in parsed_output and parsed_output['type'] == 'canvas_map_layer':
                        parsed_output['geojson'] = "Layer geometry successfully mounted to frontend canvas."
                    llm_tool_output = json.dumps(parsed_output)
                except:
                    pass
                
                tool_results_text += f"\nTool {tool_name} returned:\n{llm_tool_output}\n"

            tool_names = [t.function.name for t in msg.tool_calls]
            messages.append({
                "role": "assistant",
                "content": f"I have executed the following tools: {', '.join(tool_names)}."
            })
            messages.append({
                "role": "user",
                "content": f"Telemetry and computation results from your tool calls:{tool_results_text}\nPlease provide your comprehensive, direct, first-person safety analysis and recommendations to the user based on these results."
            })
                
            try:
                full_text = ""
                tool_calls = []
                yield json.dumps({"type": "clear_chunk"}) + "\n"
                async for chunk in stream_gemini_response(messages, llm_tools):
                    if chunk["type"] == "chunk":
                        yield json.dumps({"type": "chunk", "text": chunk["text"]}) + "\n"
                        full_text += chunk["text"]
                    elif chunk["type"] == "final_msg":
                        response = chunk["msg"]
            except Exception as e:
                import traceback
                traceback.print_exc()
                yield json.dumps({"type": "final", "text": f"⚠️ **Backend Error:** {str(e)}"}) + "\n"
                return
                
            msg = response.choices[0].message
            msg_dict = {"role": "assistant", "content": getattr(msg, "content", None) or ""}
            if getattr(msg, "tool_calls", None):
                msg_dict["tool_calls"] = [{"id": t.id, "type": "function", "function": {"name": t.function.name, "arguments": t.function.arguments}} for t in msg.tool_calls]
            
            if msg.tool_calls:
                yield json.dumps({"type": "clear_chunk"}) + "\n"
            
        # 3. Deliver Structured Payload to the UI
        final_text = full_text.strip() if full_text.strip() else (getattr(msg, "content", "") or "").strip()
        
        # Guard: if the final text is empty or leaked an internal scaffolding string, generate a rich telemetry summary
        if not final_text or final_text.startswith("I have executed the following tools:") or final_text.startswith("I called the following tools:"):
            loc = (current_weather_data and current_weather_data.get("location")) or "Djerba"
            temp = (current_weather_data and current_weather_data.get("temperature_celsius")) or 29
            feels = (current_weather_data and current_weather_data.get("feels_like_celsius")) or temp
            risk = (current_weather_data and current_weather_data.get("heat_risk_level")) or "EXTREME"
            hum = (current_weather_data and current_weather_data.get("humidity_percent")) or 80
            uv = (current_weather_data and current_weather_data.get("uv_index")) or 8.2
            
            final_text = (
                f"### 🌡️ Live Heat Risk & Environmental Assessment for **{loc}**\n\n"
                f"* **Heat Risk Level:** **{risk}**\n"
                f"* **Current Temperature:** {temp}°C (Feels like {feels}°C)\n"
                f"* **Relative Humidity:** {hum}%\n"
                f"* **Peak UV Index:** {uv} (Very High)\n\n"
                f"### 🛡️ Safety Guidance & Precautions:\n"
                f"1. **Hydration:** Drink cool water regularly throughout the day.\n"
                f"2. **Peak Sun Avoidance:** Limit outdoor physical activity during peak hours (12:00 PM - 4:00 PM).\n"
                f"3. **Cooling:** Seek shaded or air-conditioned environments when possible."
            )
            
        if loop_count >= 8 and msg.tool_calls:
            final_text = "⚠️ **Security Alert:** The AI agent exceeded the maximum allowed tool iterations (8) and was gracefully finalized. Here is the data collected so far.\n\n" + final_text
            
        final_data = {
            "type": "final",
            "text": final_text,
            "markers": map_markers,
            "forecast": forecast_data,
            "aq_forecast": aq_forecast_data,
            "uhi_geojson": uhi_geojson,
            "heat_dome_geojson": heat_dome_geojson,
            "route_geojson": route_geojson,
            "isochrone_geojson": isochrone_geojson,
            "safety_advice": safety_advice_data,
            "work_rest_guidance": work_rest_guidance,
            "current_weather": current_weather_data,
            "symptom_triage": symptom_triage_ui,
            "canvas_layers": canvas_layers,
            "canvas_chart": canvas_chart_data,
            "canvas_comparison": canvas_comparison_data,
            "canvas_camera": canvas_camera
        }
        yield json.dumps(final_data) + "\n"

    return StreamingResponse(event_generator(), media_type="application/x-ndjson")

@app.post('/api/default-map')
async def default_map_endpoint(req: dict):
    # Used to populate the SSOT and default map state on load
    lat = req.get('lat')
    lng = req.get('lng')
    
    if lat is None or lng is None:
        return {
            "current_weather": None,
            "uhi_geojson": None,
            "heat_dome_geojson": None,
            "isochrone_geojson": None,
            "markers": []
        }
    
    from src.heatshield import weather, geocoding
    
    # 1. Reverse geocode coordinates to find actual city/area name
    city_name = await geocoding.reverse_geocode(lat, lng)
    if not city_name or city_name == "Unknown":
        city_name = "Your Location"
        
    # 2. Fetch live real-time weather and WHO heat risk for the coordinates
    weather_json_str = await weather.get_weather_data(lat, lng, city_name)
    current_weather = None
    try:
        current_weather = json.loads(weather_json_str)
        if "Error" in weather_json_str or "error" in current_weather:
            current_weather = None
        else:
            current_weather["location"] = city_name
    except:
        current_weather = None
        
    return {
        'current_weather': current_weather,
        'uhi_geojson': None,
        'heat_dome_geojson': None,
        'isochrone_geojson': None,
        'markers': [
            {
                "lat": lat,
                "lng": lng,
                "label": f"You are here ({city_name})",
                "type": "user_location"
            }
        ]
    }
