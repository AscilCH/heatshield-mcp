import httpx

AQI_API_URL = "https://air-quality-api.open-meteo.com/v1/air-quality"

def assess_aqi(european_aqi: int) -> str:
    """Provide a human-readable assessment of the European AQI."""
    if european_aqi <= 20:
        return "Good (Safe for all outdoor activities)"
    elif european_aqi <= 40:
        return "Fair (Acceptable air quality)"
    elif european_aqi <= 60:
        return "Moderate (Sensitive individuals should limit prolonged outdoor exertion)"
    elif european_aqi <= 80:
        return "Poor (Unhealthy for sensitive groups)"
    elif european_aqi <= 100:
        return "Very Poor (Unhealthy for the general public)"
    return "Extremely Poor (Hazardous - avoid outdoor activities)"

async def get_air_quality_data(latitude: float, longitude: float) -> str:
    """
    Fetch live air quality data including PM2.5, PM10, and AQI indices.
    """
    async with httpx.AsyncClient(headers={'User-Agent': 'heatshield-mcp/0.1.0'}) as client:
        try:
            response = await client.get(
                AQI_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "european_aqi,us_aqi,pm10,pm2_5",
                    "timezone": "auto"
                },
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            return f"Error: Failed to connect to Open-Meteo Air Quality API: {exc}"
        except httpx.HTTPStatusError as exc:
            return f"Error: Air Quality API returned status {exc.response.status_code}"

    data = response.json()
    current = data.get("current", {})
    
    eu_aqi = current.get("european_aqi", 0)
    us_aqi = current.get("us_aqi", 0)
    pm10 = current.get("pm10", 0.0)
    pm25 = current.get("pm2_5", 0.0)
    
    assessment = assess_aqi(eu_aqi)

    return (
        f"Live Air Quality at Lat {latitude}, Lon {longitude}:\n"
        f"- European AQI: {eu_aqi} ({assessment})\n"
        f"- US AQI: {us_aqi}\n"
        f"- PM10: {pm10} μg/m³\n"
        f"- PM2.5: {pm25} μg/m³\n"
        f"==> OVERALL ASSESSMENT: {assessment}"
    )

async def get_air_quality_forecast(latitude: float, longitude: float, days: int = 5) -> str:
    """
    Fetches a multi-day air quality forecast (PM10 and PM2.5) to predict smoke or dust events.
    Returns JSON string for the frontend to graph.
    """
    import json
    async with httpx.AsyncClient(headers={'User-Agent': 'heatshield-mcp/0.1.0'}) as client:
        try:
            response = await client.get(
                AQI_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "hourly": "pm10,pm2_5",
                    "timezone": "auto",
                    "forecast_days": min(max(days, 1), 7)
                },
                timeout=15.0,
            )
            response.raise_for_status()
        except Exception as exc:
            return json.dumps({"error": f"Failed to connect to AQI API: {str(exc)}"})

    data = response.json()
    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    pm10 = hourly.get("pm10", [])
    pm25 = hourly.get("pm2_5", [])
    
    # We will chunk by day (24 hours) to get daily max
    forecast_analysis = []
    
    for i in range(0, len(times), 24):
        if i + 24 > len(times):
            break
        
        day_date = times[i].split("T")[0]
        day_pm10 = pm10[i:i+24]
        day_pm25 = pm25[i:i+24]
        
        valid_pm10 = [v for v in day_pm10 if v is not None]
        valid_pm25 = [v for v in day_pm25 if v is not None]
        
        max_pm10 = max(valid_pm10) if valid_pm10 else 0
        max_pm25 = max(valid_pm25) if valid_pm25 else 0
        
        risk = "POOR" if max_pm25 > 25 or max_pm10 > 50 else "GOOD"
        
        forecast_analysis.append({
            "date": day_date,
            "max_pm10": round(max_pm10, 1),
            "max_pm25": round(max_pm25, 1),
            "risk": risk
        })
        
    result = {
        "status": "SUCCESS",
        "message": "Air quality forecast retrieved.",
        "aq_forecast": forecast_analysis
    }
    
    return json.dumps(result, indent=2)
