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
    async with httpx.AsyncClient() as client:
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
