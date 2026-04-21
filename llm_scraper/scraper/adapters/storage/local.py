import json
import os
from typing import Any

from scraper.core.ports.storage_port import StoragePort


class LocalStorage(StoragePort):
    def save(self, data: Any, path: str) -> None:
        os.makedirs(path, exist_ok=True)
        abs_path = os.path.join(path, "output.json")
        with open(abs_path, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
