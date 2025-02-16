from scraper_manager.application.interfaces.storage_interface import BaseStorage
import os
import json

class LocalStorage(BaseStorage):
    """
    LocalStorage is an implementation of the `BaseStorage` interface that saves data to the local filesystem.

    Methods:
        save(data: str, path: str) -> None:
            Saves the given data to the specified path on the local filesystem.
    """
    def save(self, data, path_to_save: str) -> None:
        """
        Save the given data to the specified path on the local filesystem.

        Args:
            data (str): The data to save.
            path (str): The path to save the data to.
        """
        abs_path = os.path.join(path_to_save, 'output.json')
        os.makedirs(path_to_save, exist_ok=True)
        with open(abs_path, 'w') as file:
            json.dump(data, file, indent=4)