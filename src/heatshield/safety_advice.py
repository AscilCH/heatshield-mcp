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


import json
def get_occupational_heat_guidance(temperature: float, humidity_level: str = 'moderate') -> str:
    # A simplified NIOSH heat-stress framework for demo purposes
    if temperature >= 40:
        risk = 'Extreme'
        light = {'work': '20 min', 'rest': '40 min'}
        moderate = {'work': '10 min', 'rest': '50 min'}
        heavy = {'work': 'Avoid', 'rest': '-'}
    elif temperature >= 35:
        risk = 'High'
        light = {'work': '30 min', 'rest': '30 min'}
        moderate = {'work': '20 min', 'rest': '40 min'}
        heavy = {'work': '10 min', 'rest': '50 min'}
    else:
        risk = 'Moderate'
        light = {'work': 'Normal', 'rest': 'Normal'}
        moderate = {'work': '45 min', 'rest': '15 min'}
        heavy = {'work': '30 min', 'rest': '30 min'}
    
    data = {
        'type': 'work_rest_guidance',
        'feels_like': temperature,
        'actual': temperature - 5 if humidity_level == 'high' else temperature - 2, # Fake calculation to match mockup
        'humidity_level': humidity_level,
        'risk_level': risk,
        'schedule': {
            'light': light,
            'moderate': moderate,
            'heavy': heavy
        }
    }
    return json.dumps(data)
