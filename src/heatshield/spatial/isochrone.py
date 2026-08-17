import math
import httpx
import json
import asyncio

def haversine(lat1, lon1, lat2, lon2):
    R = 6371000  # Earth radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2.0)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def get_destination_point(lat, lon, distance_m, bearing_deg):
    R = 6371000
    lat_rad = math.radians(lat)
    lon_rad = math.radians(lon)
    bearing_rad = math.radians(bearing_deg)
    
    lat2_rad = math.asin(
        math.sin(lat_rad) * math.cos(distance_m / R) +
        math.cos(lat_rad) * math.sin(distance_m / R) * math.cos(bearing_rad)
    )
    lon2_rad = lon_rad + math.atan2(
        math.sin(bearing_rad) * math.sin(distance_m / R) * math.cos(lat_rad),
        math.cos(distance_m / R) - math.sin(lat_rad) * math.sin(lat2_rad)
    )
    
    return math.degrees(lat2_rad), math.degrees(lon2_rad)

async def build_isochrone_polygon(lat: float, lon: float, max_minutes: int = 15):
    # Walking speed approx 1.4 m/s (5 km/h)
    walking_speed_ms = 1.4
    
    # We will cast 16 rays (every 22.5 degrees)
    angles = [i * 22.5 for i in range(16)]
    
    # Fetch the routes once, targeting 1.5x the max distance
    max_walking_distance = max_minutes * 60 * walking_speed_ms
    target_distance = max_walking_distance * 1.5 
    targets = [get_destination_point(lat, lon, target_distance, angle) for angle in angles]
    
    routes_data = []
    async with httpx.AsyncClient(headers={'User-Agent': 'heatshield-mcp/0.1.0'}) as client:
        tasks = []
        for t_lat, t_lon in targets:
            url = f"http://router.project-osrm.org/route/v1/foot/{lon},{lat};{t_lon},{t_lat}?overview=full&geometries=geojson"
            tasks.append(client.get(url, timeout=10.0))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if isinstance(res, httpx.Response) and res.status_code == 200:
                data = res.json()
                if data.get("code") == "Ok" and len(data.get("routes", [])) > 0:
                    routes_data.append(data["routes"][0]["geometry"]["coordinates"])
                else:
                    routes_data.append(None)
            else:
                routes_data.append(None)

    features = []
    
    # Generate concentric rings: 15 min (Red), 10 min (Yellow), 5 min (Green)
    # Draw largest first so smaller ones render on top!
    time_zones = [
        (15, "#ef4444", "#dc2626"), # Red
        (10, "#eab308", "#ca8a04"), # Yellow
        (5, "#22c55e", "#16a34a")   # Green
    ]
    
    any_mixed = False
    
    for minutes, fill_color, border_color in time_zones:
        if minutes > max_minutes:
            continue
            
        dist_limit = minutes * 60 * walking_speed_ms
        boundary_points = []
        approximated_count = 0
        
        for idx, coords in enumerate(routes_data):
            if coords:
                cumulative_dist = 0
                boundary_point = coords[0]
                for i in range(1, len(coords)):
                    p1_lon, p1_lat = coords[i-1]
                    p2_lon, p2_lat = coords[i]
                    segment_dist = haversine(p1_lat, p1_lon, p2_lat, p2_lon)
                    if cumulative_dist + segment_dist >= dist_limit:
                        boundary_point = coords[i]
                        break
                    cumulative_dist += segment_dist
                    boundary_point = coords[i]
                boundary_points.append(boundary_point)
            else:
                fallback_lat, fallback_lon = get_destination_point(lat, lon, dist_limit, angles[idx])
                boundary_points.append([fallback_lon, fallback_lat])
                approximated_count += 1
                
        if approximated_count > 0:
            any_mixed = True
            
        if len(boundary_points) > 0:
            boundary_points.append(boundary_points[0])
            
        features.append({
            "type": "Feature",
            "geometry": {
                "type": "Polygon",
                "coordinates": [boundary_points]
            },
            "properties": {
                "fillColor": fill_color,
                "color": border_color,
                "fillOpacity": 0.4,
                "approximated_ray_count": approximated_count
            }
        })
        
    geojson = {
        "type": "FeatureCollection",
        "features": features
    }
    
    generated_zones = [z[0] for z in time_zones if z[0] <= max_minutes]
    zones_str = ", ".join([str(z) for z in generated_zones])
    
    return json.dumps({
        "status": "success",
        "message": f"Successfully generated a multi-layered walking isochrone map for {zones_str} minute zones. Tell the user you have highlighted the concentric walk zones on their map.",
        "isochrone_geojson": geojson,
        "isochrone_data_source": "mixed" if any_mixed else "fully_measured"
    }, indent=2)

async def generate_walkability_isochrone(latitude: float, longitude: float, minutes: int = 15) -> str:
    """
    Generates a walking isochrone (reachable area polygon) around the user's coordinates.
    """
    return await build_isochrone_polygon(latitude, longitude, minutes)
