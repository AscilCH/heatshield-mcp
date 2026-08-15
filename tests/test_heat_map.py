import pytest
import json
from unittest.mock import patch, MagicMock
from heatshield.heat_map import generate_uhi_heatmap

@pytest.fixture
def mock_cache():
    with patch("heatshield.spatial.heat_map.get_cached_heatmap") as mock_get, \
         patch("heatshield.spatial.heat_map.set_cached_heatmap") as mock_set:
        yield mock_get, mock_set

@pytest.fixture
def mock_httpx_post():
    with patch("httpx.AsyncClient.post") as mock_post:
        yield mock_post

@pytest.mark.asyncio
async def test_generate_uhi_heatmap_cache_hit(mock_cache):
    mock_get, mock_set = mock_cache
    cached_data = '{"type": "FeatureCollection", "features": []}'
    mock_get.return_value = cached_data

    result = await generate_uhi_heatmap(12.34, 56.78, radius=400)
    data = json.loads(result)
    assert data["heatmap_geojson"] == json.loads(cached_data)
    mock_get.assert_called_once_with(12.34, 56.78, 400)
    mock_set.assert_not_called()

@pytest.mark.asyncio
async def test_generate_uhi_heatmap_polygons(mock_cache, mock_httpx_post):
    mock_get, mock_set = mock_cache
    mock_get.return_value = None
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "elements": [
            {
                "type": "way",
                "tags": {"building": "yes"},
                "geometry": [{"lat": 1, "lon": 1}, {"lat": 2, "lon": 2}, {"lat": 3, "lon": 3}]
            },
            {
                "type": "way",
                "tags": {"leisure": "park"},
                "geometry": [{"lat": 4, "lon": 4}, {"lat": 5, "lon": 5}, {"lat": 6, "lon": 6}, {"lat": 4, "lon": 4}]
            },
            {
                "type": "relation",
                "tags": {"water": "yes"}
            }
        ]
    }
    mock_httpx_post.return_value = mock_response
    
    result = await generate_uhi_heatmap(12.34, 56.78, radius=400)
    data = json.loads(result)
    assert data["heatmap_geojson"]["type"] == "FeatureCollection"
    features = data["heatmap_geojson"]["features"]
    assert len(features) == 2
    
    building_feat = features[0]
    assert building_feat["properties"]["color"] == "#FFB020"
    assert building_feat["geometry"]["coordinates"][0][0] == building_feat["geometry"]["coordinates"][0][-1] # Closed
    
    park_feat = features[1]
    assert park_feat["properties"]["color"] == "#2ECF8E"
    assert park_feat["geometry"]["coordinates"][0][0] == [4, 4] # Closed
