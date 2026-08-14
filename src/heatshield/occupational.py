import math

def calculate_vapor_pressure(temp_c: float, humidity_percent: float) -> float:
    """
    Calculates water vapor pressure (hPa) using the Tetens formula.
    """
    return (humidity_percent / 100.0) * 6.105 * math.exp((17.27 * temp_c) / (237.7 + temp_c))

def calculate_wbgt(temp_c: float, humidity_percent: float, wind_speed_kmh: float, solar_rad_wm2: float) -> float:
    """
    Calculates an estimated outdoor Wet Bulb Globe Temperature (WBGT) in Celsius.
    
    Model Architecture:
      1. Vapor Pressure: e = (humidity / 100) * 6.105 * exp((17.27 * T) / (237.7 + T)) [Tetens Equation]
      2. Baseline Shade WBGT: WBGT_shade = 0.567 * T + 0.393 * e + 3.94 [Australian Bureau of Meteorology (BOM)]
      3. Outdoor Solar Adjustment: +0.003 * solar_rad_wm2 [Heuristic outdoor solar loading]
      4. Conservative Wind Adjustment: -0.5 * sqrt(v_ms), where v_ms = wind_speed_kmh / 3.6
         [Heuristic conservative cooling adjustment; square-root scaling bounds wind credit to prevent unsafe underestimation of heat stress at high wind speeds].
    
    Note: The Australian Bureau of Meteorology's published formula models shade conditions only. 
    The solar and wind terms are our conservative outdoor operational heuristic extensions.
    
    Args:
        temp_c: Air temperature in Celsius
        humidity_percent: Relative humidity (0-100)
        wind_speed_kmh: Wind speed in km/h
        solar_rad_wm2: Solar shortwave radiation in W/m^2
        
    Returns:
        float: Estimated WBGT in Celsius.
    """
    # 1. Calculate water vapor pressure
    e = calculate_vapor_pressure(temp_c, humidity_percent)
    
    # 2. Calculate shade WBGT (ABM formula)
    wbgt_shade = 0.567 * temp_c + 0.393 * e + 3.94
    
    # 3. Apply solar radiation penalty (Globe Temp impact)
    solar_penalty = solar_rad_wm2 * 0.003 
    
    # 4. Apply convective wind cooling benefit (Nu ~ Re^0.5)
    wind_ms = wind_speed_kmh / 3.6
    wind_benefit = math.sqrt(wind_ms) * 0.5 if wind_ms > 0 else 0
    
    # Final outdoor WBGT
    wbgt_outdoor = wbgt_shade + solar_penalty - wind_benefit
    
    return round(wbgt_outdoor, 1)

def map_workload(description: str) -> str:
    """
    Optional helper to map a natural language description to NIOSH categories if the LLM doesn't.
    We rely on the LLM to do the semantic mapping before calling the tool, 
    but this serves as a fallback validator.
    """
    desc = description.lower()
    if any(word in desc for word in ["digging", "shoveling", "roofing", "heavy", "asphalt", "sledgehammer"]):
        return "Heavy"
    elif any(word in desc for word in ["walking", "carrying", "painting", "moderate", "construction"]):
        return "Moderate"
    elif any(word in desc for word in ["sitting", "driving", "standing", "light"]):
        return "Light"
    return "Moderate" # Default safe assumption

def get_niosh_guidance(wbgt: float, workload: str) -> dict:
    """
    Returns the strict NIOSH work/rest cycle and safety instructions based on WBGT and Workload.
    Uses a standard threshold matrix.
    """
    wl = workload.capitalize()
    if wl not in ["Light", "Moderate", "Heavy"]:
        wl = "Moderate"
        
    # Default
    work_min = 60
    rest_min = 0
    halt = False
    
    if wl == "Light":
        if wbgt > 32:
            work_min, rest_min = 30, 30
        elif wbgt > 31:
            work_min, rest_min = 45, 15
    elif wl == "Moderate":
        if wbgt > 31.5:
            halt = True
        elif wbgt > 30:
            work_min, rest_min = 15, 45
        elif wbgt > 29:
            work_min, rest_min = 30, 30
        elif wbgt > 28:
            work_min, rest_min = 45, 15
    elif wl == "Heavy":
        if wbgt > 31.5:
            halt = True
        elif wbgt > 30:
            work_min, rest_min = 15, 45
        elif wbgt > 28:
            work_min, rest_min = 30, 30
        elif wbgt > 26:
            work_min, rest_min = 45, 15
            
    return {
        "workload": wl,
        "wbgt_celsius": wbgt,
        "work_minutes": 0 if halt else work_min,
        "rest_minutes": 60 if halt else rest_min,
        "halt_operations": halt,
        "hydration_rule": "Drink 1 cup (8 oz) of water every 15-20 minutes." if wbgt > 26 else "Drink water when thirsty."
    }
