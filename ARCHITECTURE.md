# HeatShield GeoAgent Architecture

This document visually breaks down exactly how the HeatShield project operates. You can use these diagrams to study for your interview and explain the data flow to Shoaib.

> [!TIP]
> The core value proposition of this architecture is that **the AI does not guess geographic data**. It acts strictly as an orchestrator, while the MCP Server acts as the factual data retrieval engine.

## High-Level System Flow

```mermaid
graph TD
    User([User]) -->|1. Asks a question| FE[React Web Dashboard]
    FE -->|2. Sends Chat History| BE[FastAPI Backend]
    
    subgraph Agent Loop
        BE <-->|3. Analyzes Prompt| LLM((Gemini 3.5 Flash))
        LLM -.->|4. Decides to use a tool| BE
        BE <-->|5. Executes Tool Call via MCP| MCP[HeatShield MCP Server]
        MCP -.->|6. Returns Raw JSON| BE
        BE -.->|7. Extracts Map Coordinates| FE
    end
    
    MCP -->|Queries| OM(Open-Meteo API)
    MCP -->|Queries| OSM(OpenStreetMap Overpass API)
    
    LLM -->|8. Formats final text| BE
    BE -->|9. Returns Response| FE
```

---

## The Model Context Protocol (MCP) Boundary

The MCP Server is completely isolated from the AI. This means you can swap out Gemini for Claude or ChatGPT, and the tools will still work identically.

```mermaid
sequenceDiagram
    participant LLM as Gemini Agent
    participant MCP as HeatShield MCP Server
    participant APIs as External APIs
    
    LLM->>MCP: Call geocode_location("Karlsruhe")
    MCP->>APIs: Nominatim API Request
    APIs-->>MCP: lat: 49.0068, lon: 8.4034
    MCP-->>LLM: JSON Coordinates
    
    LLM->>MCP: Call get_weather_and_heat_risk(49.00, 8.40)
    MCP->>APIs: Open-Meteo Request
    APIs-->>MCP: Temp: 30°C, Risk: HIGH
    MCP-->>LLM: JSON Risk Assessment
    
    LLM->>MCP: Call find_cooling_spots(49.00, 8.40)
    MCP->>APIs: Overpass QL Request
    APIs-->>MCP: List of 15 nearby lakes/parks
    MCP-->>LLM: JSON Array of Locations
```

---

## Directory Structure

Here is how your codebase is physically organized to support this architecture:

```mermaid
graph LR
    Root[heatshield-mcp/] --> BE(api.py - FastAPI Server)
    Root --> FE[frontend/ - React Web App]
    Root --> MCP[src/heatshield/ - MCP Server]
    
    MCP --> S(server.py - RPC Registration)
    MCP --> G(geocoding.py)
    MCP --> W(weather.py)
    MCP --> AQ(air_quality.py)
    MCP --> CS(cooling_spots.py)
    MCP --> SA(safety_advice.py)
    
    style Root fill:#1e293b,stroke:#334155,color:#fff
    style BE fill:#0f766e,stroke:#115e59,color:#fff
    style FE fill:#0369a1,stroke:#0284c7,color:#fff
    style MCP fill:#b45309,stroke:#92400e,color:#fff
```

> [!IMPORTANT]
> **Decoupled Logic:** Notice how the `src/heatshield/` folder separates `server.py` from the individual tool files (`geocoding.py`, `weather.py`, etc.). This is a best practice that makes the tools testable without needing to boot up the entire MCP server!
