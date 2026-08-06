# HeatShield: Geospatial MCP Agent

HeatShield is an AI-powered urban heat wave safety assistant designed to demonstrate the power of the **Model Context Protocol (MCP)** in grounding LLM agents with reliable, deterministic geospatial data.

## The Problem with LLM "Freehanding" Spatial Data

When tasked with geospatial routing, weather analysis, or urban heat island (UHI) mapping, native LLMs suffer from severe hallucinations. They invent streets that don't exist, guess walking distances, and fabricate localized temperatures.

**HeatShield solves this by entirely decoupling the intelligence layer from the data layer via MCP.** 
Instead of the LLM generating markdown tables or estimating distances, it acts purely as a reasoning engine that orchestrates exact tool calls to deterministic APIs.

## Architecture & MCP Implementation

The core of HeatShield is an architecture where the LLM is tightly constrained to use server-side tools. The UI is designed for rapid prototyping, but the true value lies in the backend tool implementation.

### Key MCP Tools Built for this Agent:
- `geocode_location`: Resolves human-readable addresses to exact lat/lon coordinates via Nominatim.
- `find_cooling_spots`: Queries the Overpass API for real-world infrastructure (parks, water fountains, cooling centers) based on the user's localized coordinates.
- `get_walking_route`: Uses OSRM to calculate *true* walking distances and times, preventing the LLM from relying on "crow-flies" haversine estimations.
- `generate_walkability_isochrone`: Generates an exact 15-minute reachable area polygon (GeoJSON).
- `get_urban_heat_island_heatmap`: Pulls UHI surface temperature data to render deterministic heat blobs on the map.
- `get_occupational_heat_guidance`: Calculates CDC/NIOSH work/rest cycles based strictly on current local wet-bulb globe temperature (WBGT) data.

### How it Works
1. **User asks a question** (e.g. "Find a cool place nearby").
2. **LLM reasons and calls tools**. It executes `find_cooling_spots` passing the user's localized coordinates.
3. **MCP Server executes the query**, fetching deterministic JSON data from Overpass.
4. **FastAPI intercepts the JSON payload**. Instead of letting the LLM hallucinate prose about the data, FastAPI intercepts the structured GeoJSON and streams it directly to the React frontend.
5. **React Frontend renders natively**. The UI renders the map pins and walking routes using standard Leaflet/React layers, bypassing LLM generation completely.

This architecture ensures that a user never receives a hallucinated safety route during an extreme weather event.

## Tech Stack
- **Backend**: FastAPI (Python), Model Context Protocol (MCP), Uvicorn, SQLite/DuckDB (Spatial Caching).
- **Frontend**: React, Vite, React-Leaflet.
- **External Integrations**: Overpass API, Open-Meteo, OSRM.

## Setup & Running Locally

1. Clone the repository.
2. Install Python dependencies: `uv sync`
3. Install Frontend dependencies: `cd frontend && npm install`
4. Start the backend: `uv run uvicorn api:app --reload`
5. Start the frontend: `cd frontend && npm run dev`
