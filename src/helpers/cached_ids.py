import pickle
from pathlib import Path
from typing import Dict

from bson import ObjectId
from config_rdr import config


class CachedIds:
    """
    A class to store cached MongoDB ids.
    """

    def __init__(self, entity: str) -> None:
        self.entity = entity
        self.name_to_id: Dict[str, str] = {}
        self.id_to_name: Dict[str, str] = {}

        # Load cached data if it exists
        self._load_cache()

    def _get_cache_path(self) -> Path:
        """Get the path to the cache file for this entity."""
        cache_dir = Path(config.WORKING_DIR) / "ids"
        cache_dir.mkdir(exist_ok=True, parents=True)
        return cache_dir / f"{self.entity}_cache.pkl"

    def _load_cache(self) -> None:
        """Load cached data from the pickle file if it exists."""
        cache_path = self._get_cache_path()
        if cache_path.exists():
            try:
                with open(cache_path, "rb") as f:
                    data = pickle.load(f)
                    self.name_to_id = data.get("name_to_id", {})
                    self.id_to_name = data.get("id_to_name", {})
            except (pickle.PickleError, IOError) as e:
                print(f"Error loading cache for {self.entity}: {e}")

    def _save_cache(self) -> None:
        """Save cached data to the pickle file."""
        cache_path = self._get_cache_path()
        try:
            with open(cache_path, "wb") as f:
                data = {"name_to_id": self.name_to_id, "id_to_name": self.id_to_name}
                pickle.dump(data, f)
        except (pickle.PickleError, IOError) as e:
            print(f"Error saving cache for {self.entity}: {e}")

    def id_from_name(self, name: str) -> str:
        if name not in self.name_to_id:
            self._add_entry(name)
        return self.name_to_id[name]

    def name_from_id(self, id_: str) -> str:
        if id_ not in self.id_to_name:
            raise KeyError(f"ID {id_} not found in cache for {self.entity}")
        return self.id_to_name[id_]

    def _add_entry(self, name: str):
        id_ = str(ObjectId())
        self.name_to_id[name] = id_
        self.id_to_name[id_] = name

        # Save cache after modification
        self._save_cache()
