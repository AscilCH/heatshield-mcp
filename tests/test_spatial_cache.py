import pytest
from unittest.mock import patch, MagicMock
from heatshield.spatial_cache import init_db, _get_cache_key, get_cached_heatmap, set_cached_heatmap

@pytest.fixture
def mock_duckdb():
    with patch("heatshield.spatial_cache.duckdb") as mock_db:
        yield mock_db

def test_init_db(mock_duckdb):
    mock_conn = MagicMock()
    mock_duckdb.connect.return_value = mock_conn
    init_db()
    mock_duckdb.connect.assert_called()
    mock_conn.execute.assert_called()

def test_get_cache_key():
    assert _get_cache_key(34.7936, 10.8082) == "34.79_10.81"
    assert _get_cache_key(0, 0) == "0_0"

def test_get_cached_heatmap_miss(mock_duckdb):
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_conn
    mock_conn.fetchone.return_value = None
    mock_duckdb.connect.return_value = mock_conn
    
    assert get_cached_heatmap(34.7936, 10.8082) is None

def test_get_cached_heatmap_hit(mock_duckdb):
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_conn
    mock_conn.fetchone.return_value = ['{"test": "data"}']
    mock_duckdb.connect.return_value = mock_conn
    
    assert get_cached_heatmap(34.7936, 10.8082) == '{"test": "data"}'
    
def test_set_cached_heatmap(mock_duckdb):
    mock_conn = MagicMock()
    mock_duckdb.connect.return_value = mock_conn
    
    set_cached_heatmap(34.7936, 10.8082, '{"test": "data"}')
    mock_conn.execute.assert_called()
