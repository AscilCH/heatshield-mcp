def get_advice(heat_risk_level: str, activity_type: str) -> str:
    """
    Returns specific safety recommendations based on WHO/CDC guidelines.
    """
    risk = heat_risk_level.upper()
    activity = activity_type.lower()
    
    # Base advice for the risk level
    if risk == "EXTREME":
        advice = "CRITICAL WARNING: Danger of heat stroke is imminent. Stay in air-conditioned environments. "
    elif risk == "HIGH":
        advice = "WARNING: Heat cramps or heat exhaustion likely. "
    elif risk == "MODERATE":
        advice = "CAUTION: Fatigue is possible with prolonged exposure. "
    else:
        advice = "SAFE: No immediate heat risk. "
        
    # Activity-specific modifiers
    if "jogging" in activity or "exercise" in activity or "running" in activity:
        if risk in ["EXTREME", "HIGH"]:
            advice += "Absolutely DO NOT engage in outdoor exercise right now. Move to an indoor, air-conditioned gym."
        elif risk == "MODERATE":
            advice += "If you must exercise, do it in the early morning or late evening. Hydrate extensively."
        else:
            advice += "Safe to exercise. Maintain normal hydration."
            
    elif "work" in activity or "construction" in activity:
        if risk == "EXTREME":
            advice += "Outdoor work should be halted immediately according to OSHA guidelines."
        elif risk == "HIGH":
            advice += "Mandatory rest breaks in the shade every 15-20 minutes. Drink 1 cup of water every 15 minutes."
        else:
            advice += "Normal work conditions. Ensure workers have access to shade and water."
            
    elif "elderly" in activity or "kids" in activity:
        if risk in ["EXTREME", "HIGH"]:
            advice += "Vulnerable individuals must stay indoors. Check on elderly neighbors immediately."
        else:
            advice += "Ensure vulnerable individuals stay hydrated even if they do not feel thirsty."
            
    else:
        # General advice
        if risk in ["EXTREME", "HIGH"]:
            advice += "Limit outdoor activities, stay in the shade, and locate a nearby cooling center."
            
    return advice
