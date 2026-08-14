import httpx
import json
from . import occupational

def get_heatwave_forecast(latitude: float, longitude: float, days: int = 7) -> str:
    """
    Fetches a 7-day weather forecast and calculates a Climate Aggravation Risk
    by correlating high temperatures with drought/soil moisture conditions.
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": latitude,
        "longitude": longitude,
        "daily": "temperature_2m_max,apparent_temperature_max",
        "hourly": "soil_moisture_0_to_1cm,temperature_2m,relative_humidity_2m,wind_speed_10m,shortwave_radiation",
        "timezone": "auto",
        "forecast_days": min(max(days, 1), 14) # Between 1 and 14 days
    }
    
    try:
        response = httpx.get(url, params=params, timeout=10.0)
        response.raise_for_status()
        data = response.json()
        
        daily = data.get("daily", {})
        hourly = data.get("hourly", {})
        
        dates = daily.get("time", [])
        temps = daily.get("temperature_2m_max", [])
        feels_like = daily.get("apparent_temperature_max", [])
        
        soil_moisture = hourly.get("soil_moisture_0_to_1cm", [])
        h_temps = hourly.get("temperature_2m", [])
        h_hums = hourly.get("relative_humidity_2m", [])
        h_winds = hourly.get("wind_speed_10m", [])
        h_solars = hourly.get("shortwave_radiation", [])
        
        forecast_analysis = []
        heatwave_detected = False
        consecutive_hot_days = 0
        
        for i in range(len(dates)):
            date = dates[i]
            temp = temps[i] if temps[i] is not None else 0
            feel = feels_like[i] if feels_like[i] is not None else 0
            
            # Calculate average soil moisture for this day (24 hour chunks)
            day_slice = slice(i*24, (i+1)*24)
            day_moisture_data = soil_moisture[day_slice]
            # Filter out None values
            valid_moisture = [m for m in day_moisture_data if m is not None]
            avg_moisture = sum(valid_moisture) / len(valid_moisture) if valid_moisture else 0
            
            # Calculate Peak WBGT for this day
            day_temps = h_temps[day_slice]
            day_hums = h_hums[day_slice]
            day_winds = h_winds[day_slice]
            day_solars = h_solars[day_slice]
            
            peak_wbgt = 0
            for h in range(24):
                if h < len(day_temps) and day_temps[h] is not None:
                    t = day_temps[h]
                    hu = day_hums[h] if day_hums[h] is not None else 50.0
                    wi = day_winds[h] if day_winds[h] is not None else 0.0
                    so = day_solars[h] if day_solars[h] is not None else 0.0
                    wbgt_hr = occupational.calculate_wbgt(t, hu, wi, so)
                    if wbgt_hr > peak_wbgt:
                        peak_wbgt = wbgt_hr
            
            # Heatwave Logic: > 32C
            if temp >= 32.0:
                consecutive_hot_days += 1
            else:
                consecutive_hot_days = 0
                
            if consecutive_hot_days >= 2:
                heatwave_detected = True
                
            # Drought Amplifier Logic
            # Soil moisture below 0.2 m3/m3 is generally considered dry/drought stress for vegetation
            drought_amplifier = False
            if avg_moisture < 0.22 and temp > 30:
                drought_amplifier = True
            
            risk_level = "LOW"
            if temp >= 35 or feel >= 38:
                risk_level = "EXTREME"
            elif temp >= 32 or feel >= 35:
                risk_level = "HIGH"
            elif temp >= 28:
                risk_level = "MODERATE"
                
            forecast_analysis.append({
                "date": date,
                "max_temp_c": temp,
                "feels_like_c": feel,
                "wbgt_celsius": peak_wbgt,
                "soil_moisture": round(avg_moisture, 3),
                "risk_level": risk_level,
                "climate_aggravation": "Drought conditions amplifying heat" if drought_amplifier else "Normal moisture"
            })
            
        result = {
            "status": "SEVERE_HEATWAVE_DETECTED" if heatwave_detected else "NORMAL",
            "message": "A prolonged heatwave is approaching. Proactively alert the user and locate cooling spots." if heatwave_detected else "No severe heatwave detected in the forecast period.",
            "daily_forecast": forecast_analysis
        }
        
        return json.dumps(result, indent=2)
        
    except Exception as e:
        return json.dumps({"error": f"Failed to fetch forecast: {str(e)}"})
