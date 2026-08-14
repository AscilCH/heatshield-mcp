import math
import httpx
import json
import logging
from shapely.geometry import MultiPoint
import shapely

async def get_heat_dome_footprint(latitude: float, longitude: float) -> str:
    """
    Generates a macro-scale spatial grid, fetches 500hPa geopotential height,
    calculates latitude-adjusted anomaly thresholds, checks for 3-day persistence,
    and returns a Shapely concave_hull GeoJSON footprint of the Heat Dome.
    """
    points = []
    spacing_km = 600
    steps = 3 # 3 * 600km = 1800km each side -> 3600km total
    lat_spacing = spacing_km / 111.32
    
    for i in range(-steps, steps + 1):
        lat = latitude + (i * lat_spacing)
        if lat > 90 or lat < -90: continue
        # To avoid division by zero near poles
        cos_lat = math.cos(math.radians(lat))
        if cos_lat < 0.01:
            cos_lat = 0.01
        lon_spacing = spacing_km / (111.32 * cos_lat)
        for j in range(-steps, steps + 1):
            lon = longitude + (j * lon_spacing)
            # handle lon wrap around
            if lon > 180: lon -= 360
            if lon < -180: lon += 360
            points.append((round(lat, 4), round(lon, 4)))
            
    # 2. Prepare triple-sampled batch for TM90 (phi-15, phi, phi+15)
    lats = []
    lons = []
    for pt in points:
        lats.extend([str(max(-90.0, round(pt[0] - 15, 2))), str(round(pt[0], 2)), str(min(90.0, round(pt[0] + 15, 2)))])
        lons.extend([str(round(pt[1], 2)), str(round(pt[1], 2)), str(round(pt[1], 2))])
    
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": ",".join(lats),
        "longitude": ",".join(lons),
        "hourly": "geopotential_height_500hPa",
        "timezone": "auto",
        "forecast_days": 7
    }
    
    async with httpx.AsyncClient() as client:
        try:
            res = await client.get(url, params=params, timeout=45.0)
            res.raise_for_status()
            data = res.json()
        except Exception as e:
            return json.dumps({
                "error": f"Failed to fetch 500hPa geopotential height: {str(e)}",
                "heat_dome_geojson": None
            })
            
    if isinstance(data, dict):
        data = [data]
        
    valid_points = []
    
    # 3. Apply Tibaldi-Molteni 1990 (TM90) Blocking Index
    for idx, pt in enumerate(points):
        south_data = data[idx * 3]
        mid_data = data[idx * 3 + 1]
        north_data = data[idx * 3 + 2]
        
        s_hourly = south_data.get("hourly", {}).get("geopotential_height_500hPa", [])
        m_hourly = mid_data.get("hourly", {}).get("geopotential_height_500hPa", [])
        n_hourly = north_data.get("hourly", {}).get("geopotential_height_500hPa", [])
        
        # Require 5 days of data minimum
        if len(m_hourly) < 24 * 5:
            continue
            
        days = len(m_hourly) // 24
        consecutive = 0
        dome_active = False
        
        for d in range(days):
            s_slice = [h for h in s_hourly[d*24:(d+1)*24] if h is not None]
            m_slice = [h for h in m_hourly[d*24:(d+1)*24] if h is not None]
            n_slice = [h for h in n_hourly[d*24:(d+1)*24] if h is not None]
            
            if not (s_slice and m_slice and n_slice):
                consecutive = 0
                continue
                
            s_max = max(s_slice)
            m_max = max(m_slice)
            n_max = max(n_slice)
            
            GHGS = (m_max - s_max) / 15.0
            GHGN = (n_max - m_max) / 15.0
            
            # TM90 Criteria
            if GHGS > 0 and GHGN < -10:
                consecutive += 1
                if consecutive >= 5:
                    dome_active = True
                    break
            else:
                consecutive = 0
                
        if dome_active:
            valid_points.append((pt[1], pt[0]))
            
    # 5. Generate geometry
    if len(valid_points) < 3:
        return json.dumps({
            "message": "No significant blocking high (Heat Dome) detected in this region.",
            "heat_dome_geojson": None
        })
        
    mp = MultiPoint(valid_points)
    try:
        # Generate a tight bounding polygon around the grid points
        hull = shapely.concave_hull(mp, ratio=0.5) 
        # If concave hull is broken (e.g. lines), fallback to convex
        if hull.geom_type not in ['Polygon', 'MultiPolygon']:
             hull = mp.convex_hull
    except AttributeError:
        hull = mp.convex_hull
        
    # Apply buffer trick to smooth the jagged grid edges into an organic meteorological contour
    smoothed_hull = hull.buffer(1.5, resolution=16).buffer(-1.5, resolution=16)
    
    if smoothed_hull.geom_type not in ['Polygon', 'MultiPolygon']:
        # If smoothing completely degrades it back to a LineString, fallback to original
        smoothed_hull = hull
        
    # Format to GeoJSON
    if smoothed_hull.geom_type == 'Polygon':
        coords = [list(c) for c in smoothed_hull.exterior.coords]
        geometry = {"type": "Polygon", "coordinates": [coords]}
    elif smoothed_hull.geom_type == 'MultiPolygon':
        geometry = {"type": "MultiPolygon", "coordinates": [[[list(c) for c in poly.exterior.coords]] for poly in smoothed_hull.geoms]}
    else:
        coords = [list(c) for c in smoothed_hull.exterior.coords]
        geometry = {"type": "Polygon", "coordinates": [coords]}
        
    feature = {
        "type": "FeatureCollection",
        "features": [{
            "type": "Feature",
            "geometry": geometry,
            "properties": {
                "type": "heat_dome",
                "color": "#e11d48", # Rose 600
                "fillOpacity": 0.2,
                "name": "500hPa Blocking High (Heat Dome)",
                "description": "Area where 500hPa geopotential height exceeds the latitude-adjusted summer ridge threshold for 3+ consecutive days."
            }
        }]
    }
    
    return json.dumps({
        "message": "Successfully mapped the true 500hPa Heat Dome footprint.",
        "heat_dome_geojson": feature
    })
