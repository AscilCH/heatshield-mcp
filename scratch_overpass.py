import httpx
import sys

query = """
[out:json][timeout:15];
(
  node["amenity"="drinking_water"](around:1000,49.0068,8.4034);
);
out center;
"""

try:
    response = httpx.post(
        "https://overpass-api.de/api/interpreter", 
        data={"data": query},
        headers={"User-Agent": "heatshield-mcp/0.1.0"},
        timeout=30.0
    )
    print(response.status_code)
    print(response.text)
except Exception as e:
    print(e)
sys.exit(0)

