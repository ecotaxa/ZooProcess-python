import os
import sys
import tempfile
from pathlib import Path

import pytest
from bson import ObjectId

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from helpers.cached_ids import CachedIds


@pytest.fixture
def temp_cache_dir():
    """Create a temporary directory for cache files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def mock_config(temp_cache_dir, monkeypatch):
    """Mock the config to use the temporary directory."""

    class MockConfig:
        WORKING_DIR = str(temp_cache_dir)

    monkeypatch.setattr("helpers.cached_ids.config", MockConfig())
    return MockConfig()


def test_init(mock_config):
    """Test initialization of CachedIds."""
    entity = "test_entity"
    cache = CachedIds(entity)

    assert cache.entity == entity
    assert isinstance(cache.name_to_id, dict)
    assert isinstance(cache.id_to_name, dict)
    assert len(cache.name_to_id) == 0
    assert len(cache.id_to_name) == 0


def test_id_from_name_existing(mock_config):
    """Test retrieving an ID for an existing name."""
    entity = "test_entity"
    cache = CachedIds(entity)

    # Add a name-ID mapping
    name = "test_name"
    id_ = "test_id"
    cache.name_to_id[name] = id_

    # Retrieve the ID
    result = cache.id_from_name(name)

    # Verify that the correct ID was returned
    assert result == id_


def test_id_from_name_new(mock_config, monkeypatch):
    """Test retrieving an ID for a new name."""
    entity = "test_entity"
    cache = CachedIds(entity)

    # Mock ObjectId to return a predictable value
    mock_id = "mock_object_id"
    monkeypatch.setattr(ObjectId, "__str__", lambda self: mock_id)

    # Retrieve an ID for a new name
    name = "test_name"
    result = cache.id_from_name(name)

    # Verify that a new ID was generated and stored
    assert result == mock_id
    assert cache.name_to_id[name] == mock_id
    assert cache.id_to_name[mock_id] == name

    # Verify that the cache was saved
    cache_path = Path(mock_config.WORKING_DIR) / "logs" / f"{entity}_cache.pkl"
    assert cache_path.exists()


def test_name_from_id(mock_config):
    """Test retrieving a name for an ID."""
    entity = "test_entity"
    cache = CachedIds(entity)

    # Add an ID-name mapping
    id_ = "test_id"
    name = "test_name"
    cache.name_to_id[name] = id_
    cache.id_to_name[id_] = name

    # Retrieve the name
    result = cache.name_from_id(id_)

    # Verify that the correct name was returned
    assert result == name
