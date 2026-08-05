import asyncio
import os
import json
from openai import AsyncOpenAI
from mcp.client.stdio import stdio_client, StdioServerParameters
from mcp.client.session import ClientSession

# Use Gemini's OpenAI-compatible endpoint!
# This allows us to use the standard OpenAI tool-calling format which maps perfectly to MCP.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "your-api-key-here")
client = AsyncOpenAI(
    api_key=GEMINI_API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

async def get_gemini_response(client, messages, tools):
    import openai
    for attempt in range(5):
        try:
            return await client.chat.completions.create(
                model="gemini-3.5-flash",
                messages=messages,
                tools=tools
            )
        except openai.InternalServerError as e:
            if "503" in str(e) or "UNAVAILABLE" in str(e):
                print(f"⚠️ Google API is currently experiencing high demand. Auto-retrying in 2 seconds... (Attempt {attempt+1}/5)")
                await asyncio.sleep(2)
            else:
                raise e
    raise Exception("Google API is consistently overloaded right now. Please wait a minute and try again.")

async def main():
    print("🚀 Starting HeatShield AI Client (Powered by Gemini 3.5)...")
    
    server_params = StdioServerParameters(
        command="python",
        args=["src/heatshield/server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            print("✅ Connected to HeatShield MCP Server!")
            
            mcp_tools_response = await session.list_tools()
            print(f"🔧 Discovered {len(mcp_tools_response.tools)} tools from the server.")
            
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
            
            print("\n" + "="*50)
            print("Chat session started! Type 'quit' to exit.")
            print("Example: 'I am elderly and live in Karlsruhe, is it safe to go outside?'")
            print("="*50 + "\n")
            
            messages = [{"role": "system", "content": "You are HeatShield, an urban heat wave safety assistant. You have access to geospatial tools. Use them to answer the user's questions accurately."}]
            
            while True:
                user_input = input("\nYou: ")
                if user_input.lower() in ['quit', 'exit']:
                    break
                    
                messages.append({"role": "user", "content": user_input})
                
                print("\n🤔 Gemini is thinking...")
                response = await get_gemini_response(client, messages, llm_tools)
                
                msg = response.choices[0].message
                messages.append(msg)
                
                while msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        print(f"🛠️  Agent autonomously calling tool: {tool_name}({tool_args})")
                        
                        mcp_result = await session.call_tool(tool_name, tool_args)
                        tool_output = "\n".join([c.text for c in mcp_result.content if c.type == "text"])
                        
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "name": tool_name,
                            "content": tool_output
                        })
                        
                    print("🧠 Analyzing tool results...")
                    response = await get_gemini_response(client, messages, llm_tools)
                    
                    msg = response.choices[0].message
                    messages.append(msg)
                    
                print(f"\nHeatShield: {msg.content}")

if __name__ == "__main__":
    asyncio.run(main())
