import httpx

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"

def calculate_heat_risk(apparent_temp: float, uv_index: float) -> str:
    """Calculate heat risk based on WHO/CDC guidelines."""
    # Simplified heat index logic for the prototype
    if apparent_temp >= 39.0 or uv_index >= 8.0:
        return "EXTREME"
    elif apparent_temp >= 33.0 or uv_index >= 6.0:
        return "HIGH"
    elif apparent_temp >= 27.0 or uv_index >= 3.0:
        return "MODERATE"
    return "LOW"

async def get_weather_data(latitude: float, longitude: float) -> str:
    """
    Fetch real-time weather, temperature, humidity, and UV index.
    """
    async with httpx.AsyncClient() as client:
        try:
            # We request current weather conditions, plus hourly UV index
            response = await client.get(
                WEATHER_API_URL,
                params={
                    "latitude": latitude,
                    "longitude": longitude,
                    "current": "temperature_2m,relative_humidity_2m,apparent_temperature,wind_speed_10m",
                    "hourly": "uv_index",
                    "timezone": "auto",
                    "forecast_days": 1
                },
                timeout=15.0,
            )
            response.raise_for_status()
        except httpx.RequestError as exc:
            return f"Error: Failed to connect to Open-Meteo Weather API: {exc}"
        except httpx.HTTPStatusError as exc:
            return f"Error: Open-Meteo Weather API returned status {exc.response.status_code}"

    data = response.json()
    
    current = data.get("current", {})
    temp = current.get("temperature_2m", 0.0)
    feels_like = current.get("apparent_temperature", 0.0)
    humidity = current.get("relative_humidity_2m", 0.0)
    wind_speed = current.get("wind_speed_10m", 0.0)
    
    # Extract the max UV index for the day to represent the worst-case risk
    hourly = data.get("hourly", {})
    uv_array = hourly.get("uv_index", [])
    max_uv = max((uv for uv in uv_array if uv is not None), default=0.0)

    heat_risk = calculate_heat_risk(feels_like, max_uv)

    import json
    return json.dumps({
        "type": "current_weather",
        "latitude": latitude,
        "longitude": longitude,
        "temperature_celsius": temp,
        "feels_like_celsius": feels_like,
        "relative_humidity_percent": humidity,
        "wind_speed_kmh": wind_speed,
        "peak_uv_index_today": max_uv,
        "heat_risk_level": heat_risk
    })
