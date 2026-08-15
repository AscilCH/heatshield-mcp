import duckdb
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Initialize the persistent DuckDB spatial cache
CACHE_DB_PATH = os.path.join(os.path.dirname(__file__), ".spatial_cache.duckdb")
_memory_cache = {}

def init_db():
    try:
        con = duckdb.connect(CACHE_DB_PATH)
        con.execute("""
            CREATE TABLE IF NOT EXISTS uhi_heatmap_cache (
                location_key VARCHAR PRIMARY KEY,
                geojson_data TEXT,
                cached_at TIMESTAMP
            )
        """)
        con.close()
    except Exception as e:
        logger.warning(f"DuckDB init warning (likely external DB viewer lock like DBeaver): {e}")

# Initialize on module load
init_db()

def _get_cache_key(latitude: float, longitude: float, radius: int) -> str:
    return f"{round(latitude, 2)}_{round(longitude, 2)}_{radius}"

def get_cached_heatmap(latitude: float, longitude: float, radius: int) -> str:
    """Returns the cached GeoJSON string if it exists and is less than 30 days old."""
    cache_key = _get_cache_key(latitude, longitude, radius)
    
    # 1. Try DuckDB
    try:
        con = duckdb.connect(CACHE_DB_PATH, read_only=True)
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
    except Exception as e:
        logger.debug(f"DuckDB read skipped ({e}), checking in-memory cache")

    # 2. In-memory fallback
    return _memory_cache.get(cache_key)

def set_cached_heatmap(latitude: float, longitude: float, radius: int, geojson_data: dict):
    """Saves the GeoJSON response to DuckDB and in-memory cache."""
    cache_key = _get_cache_key(latitude, longitude, radius)
    geojson_str = json.dumps(geojson_data)
    now = datetime.now()
    
    # Store in memory cache immediately
    _memory_cache[cache_key] = geojson_str
    
    # Store in DuckDB (gracefully handle external GUI locks)
    try:
        con = duckdb.connect(CACHE_DB_PATH)
        con.execute("""
            INSERT INTO uhi_heatmap_cache (location_key, geojson_data, cached_at) 
            VALUES (?, ?, ?) 
            ON CONFLICT (location_key) DO UPDATE SET geojson_data = EXCLUDED.geojson_data, cached_at = EXCLUDED.cached_at
        """, [cache_key, geojson_str, now])
        con.close()
    except Exception as e:
        logger.warning(f"DuckDB write skipped due to active external lock (e.g. DBeaver): {e}")
