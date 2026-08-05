import asyncio
import json
from src.heatshield.geocoding import geocode_location
from src.heatshield.weather import get_weather_and_heat_risk
from src.heatshield.cooling_spots import find_cooling_spots

async def test_tools():
    print("="*50)
    print("🧪 HEATSHIELD INDIVIDUAL TOOL TESTER")
    print("="*50)
    
    # 1. Test Geocoding
    print("\n📍 1. Testing Geocoding Tool (Query: 'Sfax, Tunisia')...")
    geo_result = geocode_location("Sfax, Tunisia")
    geo_data = json.loads(geo_result)
    print(json.dumps(geo_data, indent=2))
    
    # Extract coordinates for the next tools
    lat = geo_data['latitude']
    lon = geo_data['longitude']
    
    # 2. Test Weather
    print(f"\n🌤️ 2. Testing Weather Tool for lat={lat}, lon={lon}...")
    weather_result = get_weather_and_heat_risk(lat, lon)
    weather_data = json.loads(weather_result)
    print(json.dumps(weather_data, indent=2))
    
    # 3. Test Cooling Spots
    print(f"\n🌳 3. Testing Cooling Spots Tool for lat={lat}, lon={lon}...")
    cooling_result = find_cooling_spots(lon, lat, radius=3000)
    cooling_data = json.loads(cooling_result)
    
    # Just print the first 2 spots so we don't flood the terminal
    if 'elements' in cooling_data:
        print(f"Found {len(cooling_data['elements'])} total cooling spots. Here are the first 2:")
        print(json.dumps(cooling_data['elements'][:2], indent=2))
    else:
        print(cooling_data)
        
    print("\n✅ All core spatial tools executed successfully!")

if __name__ == "__main__":
    asyncio.run(test_tools())
