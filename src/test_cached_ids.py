import os
from pathlib import Path
from helpers.cached_ids import CachedIds


def test_cached_ids():
    # Clean up any existing test cache file
    test_entity = "test_entity"
    cache_path = Path("logs") / f"{test_entity}_cache.pkl"
    if cache_path.exists():
        os.remove(cache_path)

    # Create a new CachedIds instance and add some entries
    cache = CachedIds(test_entity)
    id1 = cache.id_from_name("test1")
    id2 = cache.id_from_name("test2")

    print(f"Created IDs: test1 -> {id1}, test2 -> {id2}")
    print(f"Cache file created: {cache_path.exists()}")

    # Create a new instance and verify that the data is loaded from the cache
    cache2 = CachedIds(test_entity)
    id1_loaded = cache2.id_from_name("test1")
    id2_loaded = cache2.id_from_name("test2")

    print(f"Loaded IDs: test1 -> {id1_loaded}, test2 -> {id2_loaded}")
    print(f"IDs match: {id1 == id1_loaded and id2 == id2_loaded}")

    # Clean up
    if cache_path.exists():
        os.remove(cache_path)
        print("Test cache file removed")


if __name__ == "__main__":
    test_cached_ids()
