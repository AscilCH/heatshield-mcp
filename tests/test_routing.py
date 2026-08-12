import pytest
import json
from unittest.mock import patch, MagicMock
from heatshield.routing import get_walking_route

@pytest.fixture
def mock_httpx_get():
    with patch("httpx.AsyncClient.get") as mock_get:
        yield mock_get

@pytest.fixture
def mock_cache():
    with patch("heatshield.routing.get_cached_heatmap") as mock_cache_get:
        yield mock_cache_get

@pytest.fixture
def mock_shapely():
    with patch("heatshield.routing.shape") as mock_shape:
        yield mock_shape

@pytest.mark.asyncio
async def test_get_walking_route_no_cache(mock_httpx_get, mock_cache):
    mock_cache.return_value = None
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": "Ok",
        "routes": [
            {
                "distance": 1400,
                "geometry": {"type": "LineString", "coordinates": [[1, 1], [2, 2]]}
            }
        ]
    }
    mock_httpx_get.return_value = mock_response
    
    result = await get_walking_route(1, 1, 2, 2)
    data = json.loads(result)
    
    assert data["route_geojson"]["features"][0]["properties"]["optimized"] is False
    assert data["route_geojson"]["features"][0]["properties"]["duration_s"] == 1400 / 1.4
    assert data["route_geojson"]["features"][0]["geometry"] == mock_response.json.return_value["routes"][0]["geometry"]

@pytest.mark.asyncio
async def test_get_walking_route_with_cache(mock_httpx_get, mock_cache, mock_shapely):
    mock_cache.return_value = json.dumps({
        "features": [
            {"properties": {"type": "heat_trap"}, "geometry": {"type": "Polygon", "coordinates": []}}
        ]
    })
    
    mock_shape = mock_shapely
    mock_polygon = MagicMock()
    
    mock_line1 = MagicMock()
    mock_line1.intersection.return_value.length = 10
    
    mock_line2 = MagicMock()
    mock_line2.intersection.return_value.length = 5 # Less exposure
    
    mock_shape.side_effect = [mock_polygon, mock_line1, mock_line2]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": "Ok",
        "routes": [
            {"distance": 1400, "geometry": {"type": "LineString", "coordinates": [[1, 1], [2, 2]]}},
            {"distance": 1500, "geometry": {"type": "LineString", "coordinates": [[1, 1], [3, 3]]}}
        ]
    }
    mock_httpx_get.return_value = mock_response
    
    result = await get_walking_route(1, 1, 2, 2)
    data = json.loads(result)
    
    assert data["route_geojson"]["features"][0]["properties"]["optimized"] is True
    assert data["route_geojson"]["features"][0]["geometry"] == mock_response.json.return_value["routes"][1]["geometry"] # selected line2

@pytest.mark.asyncio
async def test_get_walking_route_shapely_fails(mock_httpx_get, mock_cache, mock_shapely):
    mock_cache.return_value = json.dumps({
        "features": [
            {"properties": {"type": "heat_trap"}, "geometry": {"type": "Polygon", "coordinates": []}}
        ]
    })
    
    mock_shape = mock_shapely
    mock_polygon = MagicMock()
    
    mock_line1 = MagicMock()
    mock_line1.intersection.side_effect = Exception("Shapely error")
    mock_shape.side_effect = [mock_polygon, mock_line1]
    
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "code": "Ok",
        "routes": [
            {"distance": 1400, "geometry": {"type": "LineString", "coordinates": [[1, 1], [2, 2]]}}
        ]
    }
    mock_httpx_get.return_value = mock_response
    
    result = await get_walking_route(1, 1, 2, 2)
    data = json.loads(result)
    
    # When shapely fails, exposure falls back to 0 but heat_polygons has 1 entry,
    # so is_optimized = (0 < inf) and len(heat_polygons) > 0 = True
    assert data["route_geojson"]["features"][0]["properties"]["optimized"] is True
    assert data["route_geojson"]["features"][0]["geometry"] == mock_response.json.return_value["routes"][0]["geometry"]
