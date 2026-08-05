# HeatShield - GeoAI Urban Heat Wave Assistant

![HeatShield](https://img.shields.io/badge/MCP-Server-blue)
![React](https://img.shields.io/badge/React-Frontend-61DAFB)
![FastAPI](https://img.shields.io/badge/FastAPI-Backend-009688)
![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-green)

HeatShield is a production-grade full-stack GeoAgent built for real-time urban heat wave safety. 

Cities are struggling to protect vulnerable citizens during extreme heat events. HeatShield solves this by using the **Model Context Protocol (MCP)** to give Large Language Models real-time spatial reasoning. Instead of hallucinating geographic data, the AI autonomously queries real-time Open-Meteo and OpenStreetMap data to assess environmental risks and map out cooling shelters.

## Architecture

This project is built from scratch as a complete end-to-end GeoAgent system:

1. **MCP Spatial Tools (`src/heatshield/server.py`)**: A standard MCP JSON-RPC server over `stdio` that exposes real-world spatial intelligence tools.
2. **FastAPI Agent Backend (`api.py`)**: A custom Python backend that implements a true autonomous Agent loop. It connects to the Gemini API and the local MCP server, allowing the LLM to autonomously trigger spatial tools in a `while` loop until it solves the user's problem.
3. **React Visual Dashboard (`frontend/`)**: A sleek, modern Vite + React web application featuring a glassmorphism chat interface and an interactive Leaflet map that dynamically plots the AI's spatial reasoning in real-time.

## The Spatial Tools
The MCP server exposes 7 autonomous tools using Open Source Intelligence (OSINT):
1. `geocode_location`: Converts city/place names to GPS coordinates (via OpenStreetMap Nominatim).
2. `get_weather_and_heat_risk`: Fetches live temperature, humidity, UV index, and calculates WHO/CDC Heat Risk (via Open-Meteo).
3. `get_air_quality`: Fetches real-time AQI and particulate matter levels (via Open-Meteo).
4. `find_cooling_spots`: A spatial query to locate nearby parks, pools, fountains, and libraries (via Overpass QL).
5. `get_heat_safety_advice`: A localized WHO/CDC knowledge base for activity-specific safety recommendations.
6. `query_emergency_protocols`: A **Spatial RAG** engine that searches a local ChromaDB Vector Database using `sentence-transformers` to inject official medical documents into the LLM context, preventing hallucination.
7. `generate_uhi_heatmap`: Extracts raw GeoJSON geometries of buildings, roads, and parks via OpenStreetMap Overpass QL to generate visual Urban Heat Island (UHI) Polygon Heatmaps on the React frontend.

## Installation & Setup

Ensure you have [uv](https://github.com/astral-sh/uv) (for Python) and Node.js (for React) installed.

```bash
# Clone the repository
git clone https://github.com/yourusername/heatshield-mcp.git
cd heatshield-mcp
```

## Running the Web Dashboard

You need to run the Backend and the Frontend simultaneously in two separate terminals.

**Terminal 1 (Backend - FastAPI + Agent Loop):**
```bash
uv run uvicorn api:app --reload
```

**Terminal 2 (Frontend - React + Interactive Map):**
```bash
cd frontend
npm install
npm run dev
```
Open your browser to `http://localhost:5173` to interact with the map and the AI.

## Testing the Tools Independently

To prove the validity of the spatial data pipeline (without LLM hallucination), you can test the raw tools directly.

**Option 1: Official MCP Inspector (Web UI)**
The industry standard way to debug an MCP server.
```bash
npx -y @modelcontextprotocol/inspector uv run python src/heatshield/server.py
```

**Option 2: Raw Python Test Script**
A terminal script that manually calls the Open-Meteo and Overpass APIs for Sfax, Tunisia.
```bash
uv run test_tools.py
```

## How the AI Thinks (Agent Loop)

When a user asks: *"I am in Karlsruhe looking to swim in a lake"*

1. **Gemini** realizes it needs coordinates, so it calls `geocode_location({'query': 'Karlsruhe'})`.
2. **The Backend** parses the MCP tool output and plots a marker on the React map.
3. **Gemini** sees the coordinates and calls `get_weather_and_heat_risk(lat, lon)`.
4. **Gemini** sees the temperature is 30°C and calls `find_cooling_spots(lat, lon)`.
5. **The Backend** receives the exact GPS coordinates of lakes (like Epplesee and Baggerseen) from OpenStreetMap and streams them to the Frontend map.
6. **Gemini** formats a final, human-readable safety summary. 

All of this happens autonomously in a single user request.
