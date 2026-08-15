import duckdb
import os
import json
from datetime import datetime

# Initialize the persistent DuckDB spatial cache
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), ".spatial_cache.duckdb")

def init_db():
    con = duckdb.connect(CACHE_DB_PATH)
    # DuckDB is amazing because we can store raw JSON or use the spatial extension!
    con.execute("""
        CREATE TABLE IF NOT EXISTS uhi_heatmap_cache (
            location_key VARCHAR PRIMARY KEY,
            geojson_data TEXT,
            cached_at TIMESTAMP
        )
    """)
    con.close()

# Initialize on module load
init_db()

def _get_cache_key(latitude: float, longitude: float, radius: int) -> str:
    # Round to 2 decimal places to create a ~1.1km x 1.1km spatial caching grid
    return f"{round(latitude, 2)}_{round(longitude, 2)}_{radius}"

def get_cached_heatmap(latitude: float, longitude: float, radius: int) -> str:
    """Returns the cached GeoJSON string if it exists and is less than 30 days old."""
    cache_key = _get_cache_key(latitude, longitude, radius)
    con = duckdb.connect(CACHE_DB_PATH)
    
    # DuckDB supports INTERVAL math. We only return rows where cached_at is newer than 30 days ago.
    query = """
        SELECT geojson_data 
        FROM uhi_heatmap_cache 
        WHERE location_key = ? 
        AND cached_at > current_timestamp - INTERVAL 30 DAY
    """
    result = con.execute(query, [cache_key]).fetchone()
    con.close()
    
    if result:
        return result[0]
    return None

def set_cached_heatmap(latitude: float, longitude: float, radius: int, geojson_data: dict):
    """Saves the GeoJSON response to the DuckDB cache."""
    cache_key = _get_cache_key(latitude, longitude, radius)
    geojson_str = json.dumps(geojson_data)
    now = datetime.now()
    
    con = duckdb.connect(CACHE_DB_PATH)
    # Insert or replace (DuckDB syntax)
    con.execute("""
        INSERT INTO uhi_heatmap_cache (location_key, geojson_data, cached_at) 
        VALUES (?, ?, ?) 
        ON CONFLICT (location_key) DO UPDATE SET geojson_data = EXCLUDED.geojson_data, cached_at = EXCLUDED.cached_at
    """, [cache_key, geojson_str, now])
    con.close()
